# Campaign log

Read this reference when a campaign starts or resumes. Keep one flexible Markdown file in the user's project. It is a working log, not a database.

## File

Create or reuse:

```text
.seo-context/backlink-outreach.md
```

This is separate from the existing `.seo-context.md` shared SEO context file. Create the `.seo-context/` directory when needed. If the log already exists, read it first and update the matching campaign and website section instead of creating a duplicate. If the legacy `.seo-context/guest-post-outreach.md` exists, reuse it or migrate it once, but do not split one campaign across two logs.

Use a simple hierarchy:

```md
# Backlink outreach

## Campaign: Analytics guest posts

Focus: analytics, onboarding

### example.com

- Status: contacted
- Guidelines: https://example.com/write-for-us
- Contacted: 2026-08-20 via form
- Ask: Would you like an outline for "A practical onboarding benchmark"?
- Response: Waiting for a reply
- Price: not discussed
- Content: idea
- Published: none
- Notes: Follow up next week if there is no response.
```

A niche-edit section can be just as loose:

```md
## Campaign: Competitor link gaps (niche edits)

### example.org

- Status: drafted
- Page: https://example.org/relevant-guide
- Suggested link: https://my-site.example/research
- Placement: after the paragraph about onboarding benchmarks
- Notes: Contact route is the editor's form. Waiting for approval.
```

A link-exchange section can record both sides without becoming an event log:

```md
## Campaign: Partner link exchanges

### example.net

- Status: drafted
- Target page: https://example.net/guide
- User page: https://my-site.example/research
- Anchor options: onboarding benchmark, practical onboarding data
- Reverse direction: not requested
- Notes: Contact route is email. Awaiting approval.
```

The labels are suggestions, not a schema. Keep only the fields that matter for the website. You can add free-form notes, links, checklists, or a short paragraph when that is clearer than more labels.

## Minimum rules

- Keep one section per website under the relevant campaign.
- Include the website and a current status. Add a contact date when a message was actually sent.
- Record the latest ask, response, price, content status, published URL, or next action when those details exist.
- Update the existing section in place. Do not create an event history or separate per-prospect file unless the user asks for one.
- Keep previous details in `Notes` only when they still matter. Otherwise replace stale values so the log stays useful.
- Use ISO dates such as `2026-08-20` and keep URLs clickable.
- Do not store passwords, API keys, one-time codes, or unnecessary personal data.

Suggested status values are `candidate`, `qualified`, `drafted`, `contacted`, `replied`, `negotiating`, `accepted`, `rejected`, `published`, `submission uncertain`, and `blocked`. Use another plain status when the situation needs one.

## Update points

Update a website section when:

1. it is qualified or rejected;
2. a pitch is drafted or sent;
3. an editor replies;
4. the editor shares a price or changes the terms;
5. the article moves from idea to draft, submission, revision, or publication;
6. a link-exchange pairing, reverse-direction suggestion, or reciprocal term changes.

A draft does not count as contact. Add the contact date only after the email connector or form gives a sent/submission result. If no confirmation exists, write `Status: submission uncertain`, describe what happened, and pause before retrying. A retry needs an explicit user decision.

The log does not grant permission to contact anyone. Keep the approval gate in [references/submission.md](submission.md).

## Reporting

Return the log path and a compact summary of the website sections changed in the current run. Generate a table or CSV only when the user asks for one.
