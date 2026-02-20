"""Chainlit-aware wrappers around AutoGen agents.

Provides ``ChainlitAssistantAgent`` and ``ChainlitUserProxyAgent`` that
bridge AutoGen's message protocol with Chainlit's real-time UI updates.
"""

import chainlit as cl
from autogen.agentchat import Agent, AssistantAgent, UserProxyAgent


async def ask_helper(func: type, **kwargs: object) -> dict:
    """Repeatedly send a Chainlit ask widget until the user provides a response.

    Args:
        func: Chainlit ask-widget class (e.g. ``AskActionMessage``).
        **kwargs: Keyword arguments forwarded to the widget constructor.

    Returns:
        The user's response dict.
    """
    res = await func(**kwargs).send()
    while not res:
        res = await func(**kwargs).send()
    return res


class ChainlitAssistantAgent(AssistantAgent):
    """Wrapper around AutoGen's AssistantAgent that streams messages to Chainlit."""

    def send(
        self,
        message: dict | str,
        recipient: Agent,
        request_reply: bool | None = None,
        silent: bool | None = False,
    ) -> bool:
        """Forward a message to ``recipient`` and echo it to the Chainlit UI."""
        cl.run_sync(
            cl.Message(
                content=f'*Sending message to "{recipient.name}":*\n\n{message}',
                author=self.name,
            ).send()
        )
        super().send(
            message=message,
            recipient=recipient,
            request_reply=request_reply,
            silent=silent,
        )
        return True


class ChainlitUserProxyAgent(UserProxyAgent):
    """Wrapper around AutoGen's UserProxyAgent with Chainlit action buttons."""

    def get_human_input(self, prompt: str) -> str:
        """Present an interactive prompt in the Chainlit UI and return user input."""
        if prompt.startswith(
            "Provide feedback to chat_manager. Press enter to skip and use auto-reply"
        ):
            res = cl.run_sync(
                ask_helper(
                    cl.AskActionMessage,
                    content="Continue or provide feedback?",
                    actions=[
                        cl.Action(
                            name="continue",
                            payload={"value": "continue"},
                            label="✅ Continue",
                        ),
                        cl.Action(
                            name="feedback",
                            payload={"value": "feedback"},
                            label="💬 Provide feedback",
                        ),
                        cl.Action(
                            name="exit",
                            payload={"value": "exit"},
                            label="🔚 Exit Conversation",
                        ),
                    ],
                )
            )
            if res.get("value") == "continue":
                return ""
            if res.get("value") == "exit":
                return "exit"

        reply = cl.run_sync(ask_helper(cl.AskUserMessage, content=prompt, timeout=60))

        return reply["output"].strip()

    def send(
        self,
        message: dict | str,
        recipient: Agent,
        request_reply: bool | None = None,
        silent: bool | None = False,
    ) -> None:
        """Forward a message to ``recipient`` via the parent agent."""
        # cl.run_sync(
        # cl.Message(
        #    content=f'*Sending message to "{recipient.name}"*:\n\n{message}',
        #    author=self.name,
        # ).send()
        # )
        super().send(
            message=message,
            recipient=recipient,
            request_reply=request_reply,
            silent=silent,
        )
