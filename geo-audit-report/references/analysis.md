# Analysis reference

For each run, distinguish answer mentions, actual citations, citation candidates, retrieved search sources, attached links, maps, and competitor entities. Compare the searched → retrieved → mapped → mentioned → cited funnel without turning missing or malformed evidence into zero. Analyze answer, citation, search, and map competitors as separate channels.

For fan-out data, report per response: exact query or queries; whether search triggered; whether the brand appeared in the final answer; whether the brand was cited; and whether the target domain appeared in captured search results. Aggregate by query with count, prompts, chatbots, brand-appearance count, citation count, and target-domain appearance count.

## Diagnose lost prompts before recommending

A lost prompt is one where the brand is absent from the answer or citations while competitors appear. Before proposing content, assign each important lost prompt one cause:

- `missing_page`: no page on the target site answers the prompt or its main fan-out queries. Only this cause justifies a new page.
- `weak_page`: a relevant page exists but does not answer the question directly, misses the fan-out angles, or is not retrieved. Improve that page instead of publishing another one on the same question.
- `technical`: the relevant page exists but is blocked, not indexed, slow, or otherwise hard to crawl. Check robots, indexing, and rendering on that page; do not turn site-wide warnings into priorities unless they affect pages tied to lost buyer prompts.
- `third_party`: the answer relies on Reddit threads, review sites, directories, listicles, or articles that barely mention the brand.

Check the site's sitemap, pages, or Search Console before choosing between `missing_page` and `weak_page`. Say when the evidence cannot separate two causes.

## Act on third-party sources

For `third_party` prompts, list the sources shaping the answer (citations first, then search sources) and compare how the brand and competitors are represented on each. Classify each important source by the action it needs:

- `own`: pages the client controls → create or improve.
- `claim`: profiles and listings the client can take over, such as G2, Capterra, marketplaces, or directories → claim and complete.
- `earn`: editorial mentions, reviews, and community discussions the client has to deserve → outreach, review requests, or community participation. For Reddit, join the threads tied to the tracked buyer prompts rather than posting everywhere.
- `contest`: outdated or incorrect information about the client → request a correction.

## Measure and iterate

Treat each recommendation as one change to test on named prompts. On the next run, rerun the same prompts, say which changes moved visibility, retire the ones that did not, and double down on the ones that did. Google rankings and AI visibility move independently: do not read a Search Console gain as a GEO gain, or the reverse. When conversion data is available, prefer activated users from AI referrals over mention counts as the outcome.

In `report-analysis.json`, set a recommendation's optional `diagnosis` to the cause it fixes and `source_action` to the source action when it targets a third-party source.

Use the local GEO playbooks only when they are available through the user's connected context; do not assume a repository-relative `obsidian/GEO Playbook.md` exists. The relevant operating pattern is: list prompts → track → wait → analyze fan-outs → diagnose each lost prompt → make one change → rerun.
