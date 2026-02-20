from pathlib import Path

import autogen  # type: ignore[import-not-found]
import chainlit as cl
from chainlit.input_widget import Select, Slider, Switch
from rich import print
from typing_extensions import Annotated

from onboard_ai.agent_factory import (
	create_retriever,
	create_specialists,
	create_user_proxy,
	select_specialist,
)
from onboard_ai.graphrag_service import (
	has_data_citation,
	index_not_ready_message,
	index_ready,
	query_graphrag,
)
from onboard_ai.settings import AUDIENCE_INSTRUCTION, LLM_CONFIG_AUTOGEN
from onboard_ai.services.web_search import augment_answer_with_web, web_search_enabled


@cl.on_chat_start
async def on_chat_start():
	try:
		settings = await cl.ChatSettings(
			[
				Switch(id="Search_type", label="(GraphRAG) Local Search", initial=True),
				Switch(
					id="Enable_web_search",
					label="(Web) Enable SearXNG fallback",
					initial=True,
				),
				Select(
					id="Gen_type",
					label="(GraphRAG) Content Type",
					values=[
						"prioritized list",
						"single paragraph",
						"multiple paragraphs",
						"multiple-page report",
					],
					initial_index=1,
				),
				Select(
					id="Audience",
					label="(Onboarding) Audience",
					values=["General", "Developer", "QA", "Manager"],
					initial_index=0,
				),
				Switch(
					id="Enable_multi_agent",
					label="(AutoGen) Enable Specialist Router",
					initial=False,
				),
				Slider(
					id="Community",
					label="(GraphRAG) Community Level",
					initial=0,
					min=0,
					max=2,
					step=1,
				),
			]
		).send()

		cl.user_session.set("Gen_type", settings["Gen_type"])
		cl.user_session.set("Audience", settings["Audience"])
		cl.user_session.set("Enable_web_search", settings["Enable_web_search"])
		cl.user_session.set("Enable_multi_agent", settings["Enable_multi_agent"])
		cl.user_session.set("Community", settings["Community"])
		cl.user_session.set("Search_type", settings["Search_type"])

		retriever = create_retriever()
		user_proxy = create_user_proxy()
		specialists = create_specialists()

		cl.user_session.set("Query Agent", user_proxy)
		cl.user_session.set("Retriever", retriever)
		cl.user_session.set("Specialists", specialists)

		if not index_ready(Path(".")):
			await cl.Message(content=index_not_ready_message(), author="System").send()

		await cl.Message(
			content="Hello! What task would you like to get done today?",
			author="User_Proxy",
		).send()
		print("Session initialized")
	except Exception as e:
		print("Error:", e)


@cl.on_settings_update
async def setup_agent(settings):
	cl.user_session.set("Gen_type", settings["Gen_type"])
	cl.user_session.set("Audience", settings["Audience"])
	cl.user_session.set("Enable_web_search", settings["Enable_web_search"])
	cl.user_session.set("Enable_multi_agent", settings["Enable_multi_agent"])
	cl.user_session.set("Community", settings["Community"])
	cl.user_session.set("Search_type", settings["Search_type"])
	print("on_settings_update", settings)


@cl.on_message
async def run_conversation(message: cl.Message):
	root_dir = Path(".")
	context = message.content
	max_iter = 10

	response_type = cl.user_session.get("Gen_type")
	audience = cl.user_session.get("Audience")
	enable_multi_agent = cl.user_session.get("Enable_multi_agent")
	enable_web_search = web_search_enabled(cl.user_session.get("Enable_web_search"))
	community = cl.user_session.get("Community")
	local_search = cl.user_session.get("Search_type")

	retriever = cl.user_session.get("Retriever")
	user_proxy = cl.user_session.get("Query Agent")
	specialists = cl.user_session.get("Specialists") or {}
	specialist = select_specialist(audience, specialists)

	def state_transition(last_speaker, groupchat):
		messages = groupchat.messages
		if last_speaker is user_proxy:
			if enable_multi_agent and specialist is not None:
				return specialist
			return retriever
		if enable_multi_agent and specialist is not None and last_speaker is specialist:
			return retriever
		if last_speaker is retriever:
			if messages[-1]["content"].lower() not in ["math_expert", "physics_expert"]:
				return user_proxy
			return user_proxy
		return None

	async def query_graph_rag(
		question: Annotated[
			str, "Query string containing information that you want from RAG search"
		],
	) -> str:
		role_hint = AUDIENCE_INSTRUCTION.get(audience, AUDIENCE_INSTRUCTION["General"])
		query = f"{question}\n\nAudience guidance: {role_hint}"

		if not index_ready(root_dir):
			result = index_not_ready_message()
			if enable_web_search:
				result = augment_answer_with_web(answer=result, query=query)
			await cl.Message(content=result).send()
			return result

		result = query_graphrag(
			root_dir=root_dir,
			local_search=local_search,
			community_level=community,
			response_type=response_type,
			query=query,
		)
		if not has_data_citation(result):
			result = (
				f"{result}\n\n"
				"_Citation check: no explicit [Data: ...] references were found in the response. "
				"Please verify against source context._"
			)
			if enable_web_search:
				result = augment_answer_with_web(answer=result, query=query)

		await cl.Message(content=result).send()
		return result

	d_retrieve_content = retriever.register_for_llm(
		description="retrieve content for code generation and question answering.",
		api_style="function",
	)(query_graph_rag)

	specialist_agents = [specialist] if enable_multi_agent and specialist is not None else []

	for agent in [user_proxy, retriever, *specialist_agents]:
		agent.register_for_execution()(d_retrieve_content)

	groupchat = autogen.GroupChat(
		agents=[user_proxy, retriever, *specialist_agents],
		messages=[],
		max_round=max_iter,
		speaker_selection_method=state_transition,
		allow_repeat_speaker=True,
	)
	manager = autogen.GroupChatManager(
		groupchat=groupchat,
		llm_config=LLM_CONFIG_AUTOGEN,
		is_termination_msg=lambda x: x.get("content", "")
		and x.get("content", "").rstrip().endswith("TERMINATE"),
		code_execution_config=False,
	)

	if len(groupchat.messages) == 0:
		await cl.make_async(user_proxy.initiate_chat)(manager, message=context)
	elif len(groupchat.messages) < max_iter:
		await cl.make_async(user_proxy.send)(manager, message=context)
	else:
		await cl.make_async(user_proxy.send)(manager, message="exit")
