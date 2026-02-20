# Prompt token audit

- tokenizer: `cl100k_base`
- prompts audited: 12
- total after tokens: 7175
- total before tokens (git HEAD): not available

## Per prompt

| Prompt | Before | After | Delta | Est. minimal | Headroom |
|---|---:|---:|---:|---:|---:|
| `assets/prompts/basic_search_system_prompt.txt` | n/a | 137 | n/a | 136 | 1 (0.7%) |
| `assets/prompts/community_report_graph.txt` | n/a | 1439 | n/a | 1365 | 74 (5.1%) |
| `assets/prompts/community_report_text.txt` | n/a | 1657 | n/a | 1578 | 79 (4.8%) |
| `assets/prompts/drift_reduce_prompt.txt` | n/a | 178 | n/a | 177 | 1 (0.6%) |
| `assets/prompts/drift_search_system_prompt.txt` | n/a | 198 | n/a | 197 | 1 (0.5%) |
| `assets/prompts/extract_claims.txt` | n/a | 1101 | n/a | 1099 | 2 (0.2%) |
| `assets/prompts/extract_graph.txt` | n/a | 1732 | n/a | 1725 | 7 (0.4%) |
| `assets/prompts/global_search_knowledge_system_prompt.txt` | n/a | 36 | n/a | 35 | 1 (2.8%) |
| `assets/prompts/global_search_map_system_prompt.txt` | n/a | 211 | n/a | 210 | 1 (0.5%) |
| `assets/prompts/global_search_reduce_system_prompt.txt` | n/a | 180 | n/a | 179 | 1 (0.6%) |
| `assets/prompts/local_search_system_prompt.txt` | n/a | 170 | n/a | 168 | 2 (1.2%) |
| `assets/prompts/summarize_descriptions.txt` | n/a | 136 | n/a | 135 | 1 (0.7%) |

## Optimization headroom ranking

1. `assets/prompts/community_report_text.txt` — 79 tokens (4.8%)
2. `assets/prompts/community_report_graph.txt` — 74 tokens (5.1%)
3. `assets/prompts/extract_graph.txt` — 7 tokens (0.4%)
4. `assets/prompts/extract_claims.txt` — 2 tokens (0.2%)
5. `assets/prompts/local_search_system_prompt.txt` — 2 tokens (1.2%)
6. `assets/prompts/basic_search_system_prompt.txt` — 1 tokens (0.7%)
7. `assets/prompts/drift_reduce_prompt.txt` — 1 tokens (0.6%)
8. `assets/prompts/drift_search_system_prompt.txt` — 1 tokens (0.5%)
9. `assets/prompts/global_search_knowledge_system_prompt.txt` — 1 tokens (2.8%)
10. `assets/prompts/global_search_map_system_prompt.txt` — 1 tokens (0.5%)
11. `assets/prompts/global_search_reduce_system_prompt.txt` — 1 tokens (0.6%)
12. `assets/prompts/summarize_descriptions.txt` — 1 tokens (0.7%)

## Notes

- `Before` comes from `git show HEAD:<path>` when available.
- `Est. minimal` is a heuristic lower bound, not a semantic rewrite.
- Use ranking to prioritize proofing work on highest-headroom prompts.
