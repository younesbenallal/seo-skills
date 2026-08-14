# Analysis reference

For each run, distinguish answer mentions, actual citations, citation candidates, retrieved search sources, attached links, maps, and competitor entities. Compare the searched → retrieved → mapped → mentioned → cited funnel without turning missing or malformed evidence into zero. Analyze answer, citation, search, and map competitors as separate channels.

For fan-out data, report per response: exact query or queries; whether search triggered; whether the brand appeared in the final answer; whether the brand was cited; and whether the target domain appeared in captured search results. Aggregate by query with count, prompts, chatbots, brand-appearance count, citation count, and target-domain appearance count.

Use the local GEO playbook only when it is available through the user's connected context; do not assume a repository-relative `obsidian/GEO Playbook.md` exists. The relevant operating pattern is: list prompts → track → wait → analyze fan-outs; create missing content for valuable fan-outs; target UGC-dominant sources strategically.
