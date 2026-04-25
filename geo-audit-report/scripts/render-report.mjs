#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const parseArgs = (argv) => {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token?.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[index + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
      continue;
    }
    args[key] = next;
    index += 1;
  }
  return args;
};

const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");

const sanitizeUrl = (value) => {
  const text = String(value ?? "").trim();
  if (!text) return "";
  if (/^(https?:|mailto:)/i.test(text)) return text;
  return "";
};

const slugify = (value) =>
  String(value ?? "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "report";

const unique = (items) => [...new Set((Array.isArray(items) ? items : []).filter(Boolean))];

const numberOrZero = (value) => (Number.isFinite(Number(value)) ? Number(value) : 0);

const percent = (value, precision = 0) => {
  if (!Number.isFinite(value)) return "0%";
  return `${(value * 100).toFixed(precision)}%`;
};

const average = (values) => {
  const safe = values.filter((value) => Number.isFinite(value));
  if (!safe.length) return null;
  return safe.reduce((sum, value) => sum + value, 0) / safe.length;
};

const formatTimestamp = (value) => {
  const text = String(value ?? "").trim();
  if (!text) return "Unknown date";
  const date = new Date(text);
  if (Number.isNaN(date.getTime())) return text;
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date);
};

const markdownInline = (source) =>
  source
    .replace(/`([^`]+)`/g, (_, code) => `<code>${code}</code>`)
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => {
      const safeUrl = sanitizeUrl(url);
      return safeUrl ? `<a href="${escapeHtml(safeUrl)}" target="_blank" rel="noreferrer">${label}</a>` : label;
    })
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])\*([^*]+)\*(?=[\s).,!?:;]|$)/g, "$1<em>$2</em>")
    .replace(/(^|[\s(])_([^_]+)_(?=[\s).,!?:;]|$)/g, "$1<em>$2</em>");

const renderMarkdown = (markdown) => {
  const input = String(markdown ?? "").replace(/\r\n/g, "\n").trim();
  if (!input) return "<p>No response body available.</p>";

  const codeBlocks = [];
  let prepared = input.replace(/```([^\n`]*)\n([\s\S]*?)```/g, (_, language, code) => {
    const token = `@@CODEBLOCK_${codeBlocks.length}@@`;
    const languageClass = String(language || "").trim();
    codeBlocks.push(
      `<pre><code${languageClass ? ` class="language-${escapeHtml(languageClass)}"` : ""}>${escapeHtml(code)}</code></pre>`
    );
    return token;
  });

  const blocks = prepared.split(/\n\s*\n/);
  const html = [];

  for (const block of blocks) {
    const trimmed = block.trim();
    if (!trimmed) continue;

    if (/^@@CODEBLOCK_\d+@@$/.test(trimmed)) {
      html.push(trimmed);
      continue;
    }

    const lines = trimmed.split("\n");

    if (lines.every((line) => /^>\s?/.test(line))) {
      const body = lines.map((line) => line.replace(/^>\s?/, "")).join("\n");
      html.push(`<blockquote>${renderMarkdown(body)}</blockquote>`);
      continue;
    }

    if (lines.every((line) => /^\d+\.\s+/.test(line))) {
      const items = lines
        .map((line) => line.replace(/^\d+\.\s+/, ""))
        .map((line) => `<li>${markdownInline(escapeHtml(line))}</li>`)
        .join("");
      html.push(`<ol>${items}</ol>`);
      continue;
    }

    if (lines.every((line) => /^[-*+]\s+/.test(line))) {
      const items = lines
        .map((line) => line.replace(/^[-*+]\s+/, ""))
        .map((line) => `<li>${markdownInline(escapeHtml(line))}</li>`)
        .join("");
      html.push(`<ul>${items}</ul>`);
      continue;
    }

    const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      html.push(`<h${level}>${markdownInline(escapeHtml(heading[2]))}</h${level}>`);
      continue;
    }

    html.push(
      `<p>${markdownInline(
        escapeHtml(lines.join("\n")).replace(/\n/g, "<br />")
      )}</p>`
    );
  }

  return html
    .join("\n")
    .replace(/@@CODEBLOCK_(\d+)@@/g, (_, index) => codeBlocks[Number(index)] || "");
};

const toLink = (url, label) => {
  const safeUrl = sanitizeUrl(url);
  const safeLabel = escapeHtml(label || url || "");
  return safeUrl
    ? `<a href="${escapeHtml(safeUrl)}" target="_blank" rel="noreferrer">${safeLabel}</a>`
    : safeLabel;
};

const listHtml = (items, formatter) => {
  const safe = Array.isArray(items) ? items.filter(Boolean) : [];
  if (!safe.length) return `<p class="section-copy">No items captured.</p>`;
  return `<ul class="list">${safe.map((item) => `<li>${formatter(item)}</li>`).join("")}</ul>`;
};

const collectPromptSummaries = (responses) => {
  const byPrompt = new Map();

  for (const response of responses) {
    const prompt = String(response.prompt || "").trim();
    if (!prompt) continue;

    const current =
      byPrompt.get(prompt) || {
        prompt,
        responses: [],
        mentions: 0,
        citations: 0,
        usedWebSearchCount: 0,
      };

    current.responses.push(response);
    if (numberOrZero(response.mentions) > 0) current.mentions += 1;
    if (response.cited) current.citations += 1;
    if (response.used_web_search) current.usedWebSearchCount += 1;
    byPrompt.set(prompt, current);
  }

  return [...byPrompt.values()]
    .map((group) => ({
      ...group,
      visibilityRate: group.responses.length ? group.mentions / group.responses.length : 0,
      citationRate: group.responses.length ? group.citations / group.responses.length : 0,
    }))
    .sort((left, right) => right.visibilityRate - left.visibilityRate || right.citationRate - left.citationRate);
};

const collectDomainSummary = (responses) => {
  const domains = new Map();

  for (const response of responses) {
    for (const source of Array.isArray(response.sources) ? response.sources : []) {
      const domain = String(source.domain || "").trim();
      if (!domain) continue;

      const current =
        domains.get(domain) || {
          domain,
          count: 0,
          pages: new Set(),
        };

      current.count += 1;
      if (source.url) current.pages.add(String(source.url));
      domains.set(domain, current);
    }
  }

  return [...domains.values()]
    .map((entry) => ({
      domain: entry.domain,
      count: entry.count,
      pages: entry.pages.size,
    }))
    .sort((left, right) => right.count - left.count)
    .slice(0, 10);
};

const buildRecommendations = ({
  responses,
  snapshots,
  promptSummaries,
  fanOutSummary,
  competitorMentions,
}) => {
  const recommendations = [];
  const totalResponses = responses.length || 1;
  const citedResponses = responses.filter((response) => response.cited).length;
  const visibilityResponses = responses.filter((response) => numberOrZero(response.mentions) > 0).length;
  const searchTriggered = responses.filter((response) => response.used_web_search).length;

  if (visibilityResponses / totalResponses < 0.5) {
    recommendations.push("Strengthen category and comparison pages for the prompts where the brand is absent, because visibility is still under half of captured responses.");
  }

  if (citedResponses / totalResponses < 0.25) {
    recommendations.push("Prioritize citation-ready assets such as original research, benchmark pages, and answer-first comparison content so assistants have clearer sources to cite.");
  }

  if (searchTriggered / totalResponses > 0.5) {
    recommendations.push("Search is triggering frequently, so on-site discoverability and third-party citation coverage matter as much as prompt phrasing.");
  }

  if (fanOutSummary.length > 0) {
    recommendations.push("Use the captured fan-out queries as the next content backlog, especially the queries where the domain appears in search results but not in final answers.");
  }

  if (competitorMentions.length > 0) {
    recommendations.push(`Create direct comparison and alternative pages around ${competitorMentions.slice(0, 3).join(", ")} because competitors are appearing in assistant responses.`);
  }

  const failedSnapshots = snapshots.filter((snapshot) => snapshot.status !== "ready");
  if (failedSnapshots.length > 0) {
    recommendations.push("Re-run the failed providers before making hard conclusions, because this export includes incomplete chatbot coverage.");
  }

  if (!recommendations.length && promptSummaries[0]) {
    recommendations.push(`Double down on prompt clusters similar to "${promptSummaries[0].prompt}" because they already show the strongest baseline visibility.`);
  }

  return recommendations.slice(0, 5);
};

const renderMetricCard = ({ label, value, detail }) => `
  <article class="metric-card">
    <small>${escapeHtml(label)}</small>
    <strong>${escapeHtml(value)}</strong>
    <span>${escapeHtml(detail)}</span>
  </article>
`;

const buildReport = (audit) => {
  const responses = Array.isArray(audit.responses) && audit.responses.length
    ? audit.responses
    : Array.isArray(audit.results)
      ? audit.results
      : [];
  const snapshots = Array.isArray(audit.snapshots) ? audit.snapshots : [];
  const fanOutSummary = Array.isArray(audit.fan_out_summary) ? audit.fan_out_summary : [];
  const manualRecommendations = Array.isArray(audit.manual_recommendations) ? audit.manual_recommendations : [];

  const promptSummaries = collectPromptSummaries(responses);
  const citedResponses = responses.filter((response) => response.cited).length;
  const visibilityResponses = responses.filter((response) => numberOrZero(response.mentions) > 0).length;
  const searchTriggeredResponses = responses.filter((response) => response.used_web_search).length;
  const averageRank = average(
    responses
      .map((response) => response.first_citation_rank)
      .filter((value) => Number.isFinite(value))
  );
  const competitorMentions = unique(
    responses.flatMap((response) => Array.isArray(response.competitor_domains) ? response.competitor_domains : [])
  );

  const chatbotSummaries = snapshots.map((snapshot) => {
    const chatbotResponses = responses.filter((response) => response.chatbot === snapshot.chatbot);
    const visible = chatbotResponses.filter((response) => numberOrZero(response.mentions) > 0).length;
    const cited = chatbotResponses.filter((response) => response.cited).length;
    const avgRank = average(
      chatbotResponses
        .map((response) => response.first_citation_rank)
        .filter((value) => Number.isFinite(value))
    );

    return {
      chatbot: snapshot.chatbot,
      status: snapshot.status,
      total: chatbotResponses.length,
      visible,
      cited,
      searchTriggered: chatbotResponses.filter((response) => response.used_web_search).length,
      avgRank,
    };
  });

  const recommendations = manualRecommendations.length
    ? manualRecommendations.map((item) => `${item.title}: ${item.summary}`)
    : buildRecommendations({
        responses,
        snapshots,
        promptSummaries,
        fanOutSummary,
        competitorMentions,
      });

  const topPrompts = promptSummaries.slice(0, 6);
  const weakestPrompts = [...promptSummaries]
    .sort((left, right) => left.visibilityRate - right.visibilityRate || left.citationRate - right.citationRate)
    .slice(0, 4);
  const topDomains = collectDomainSummary(responses);

  const hero = `
    <section class="hero">
      <p class="eyebrow">Static Deliverable</p>
      <h1>GEO Audit Report</h1>
      <div class="hero-grid">
        <div class="hero-copy">
          <p>
            This export turns the Bright Data run into a standalone HTML page, so the audit can be opened directly from disk without a local server.
          </p>
          <p>
            Target: ${toLink(audit.check_url, audit.check_url)}<br />
            Prompts tracked: <span class="mono">${escapeHtml(String(promptSummaries.length))}</span>
          </p>
        </div>
        <div class="hero-meta">
          <div class="meta-card">
            <p class="meta-label">Generated</p>
            <p class="meta-value">${escapeHtml(formatTimestamp(audit.run_at))}</p>
          </div>
          <div class="meta-card">
            <p class="meta-label">Brand Terms</p>
            <p class="meta-value">${escapeHtml(unique(audit.brand_terms || []).join(", ") || "Not provided")}</p>
          </div>
          <div class="meta-card">
            <p class="meta-label">Target Domains</p>
            <p class="meta-value">${escapeHtml(unique(audit.target_domains || []).join(", ") || "Not provided")}</p>
          </div>
        </div>
      </div>
    </section>
  `;

  const metrics = `
    <section class="metrics-grid">
      ${renderMetricCard({
        label: "Visible Responses",
        value: `${visibilityResponses}/${responses.length}`,
        detail: `${percent(responses.length ? visibilityResponses / responses.length : 0)} mention the brand or domain.`,
      })}
      ${renderMetricCard({
        label: "Cited Responses",
        value: `${citedResponses}/${responses.length}`,
        detail: `${percent(responses.length ? citedResponses / responses.length : 0)} cite the brand directly.`,
      })}
      ${renderMetricCard({
        label: "Search Triggered",
        value: `${searchTriggeredResponses}/${responses.length}`,
        detail: `${percent(responses.length ? searchTriggeredResponses / responses.length : 0)} of responses triggered web search.`,
      })}
      ${renderMetricCard({
        label: "Average Citation Rank",
        value: averageRank === null ? "n/a" : `#${averageRank.toFixed(1)}`,
        detail: "Mean first citation position across responses with citations.",
      })}
    </section>
  `;

  const executiveSummary = `
    <section class="summary-grid">
      <article class="panel">
        <div class="panel-heading">
          <h2>Executive Summary</h2>
        </div>
        ${listHtml(recommendations, (item) => escapeHtml(item))}
      </article>
      <article class="panel">
        <div class="panel-heading">
          <h2>Coverage Notes</h2>
        </div>
        <div class="kv-list">
          <div class="kv-item">
            <strong>Best prompt cluster</strong>
            <span>${escapeHtml(topPrompts[0]?.prompt || "No prompt data available.")}</span>
          </div>
          <div class="kv-item">
            <strong>Weakest prompt cluster</strong>
            <span>${escapeHtml(weakestPrompts[0]?.prompt || "No prompt data available.")}</span>
          </div>
          <div class="kv-item">
            <strong>Competitor mentions</strong>
            <span>${escapeHtml(competitorMentions.join(", ") || "None captured.")}</span>
          </div>
        </div>
      </article>
    </section>
  `;

  const chatbotSection = `
    <section class="split">
      <article class="panel">
        <div class="panel-heading">
          <h2>By Chatbot</h2>
        </div>
        <div class="chatbot-list">
          ${chatbotSummaries
            .map((summary) => {
              const visibility = summary.total ? summary.visible / summary.total : 0;
              return `
                <div class="domain-card">
                  <div class="stat-row">
                    <strong>${escapeHtml(summary.chatbot)}</strong>
                    <span class="chip ${summary.status === "ready" ? "chip--good" : "chip--warn"}">${escapeHtml(summary.status)}</span>
                  </div>
                  <span>${summary.total} responses, ${summary.cited} cited, ${summary.searchTriggered} with search triggered.</span>
                  <div class="bar"><span style="width: ${Math.max(visibility * 100, 6).toFixed(1)}%"></span></div>
                  <div class="stat-row">
                    <span>Visibility rate</span>
                    <strong>${percent(visibility)}</strong>
                  </div>
                  <div class="stat-row">
                    <span>Average citation rank</span>
                    <strong>${summary.avgRank === null ? "n/a" : `#${summary.avgRank.toFixed(1)}`}</strong>
                  </div>
                </div>
              `;
            })
            .join("")}
        </div>
      </article>
      <article class="panel">
        <div class="panel-heading">
          <h2>Fan-Out Queries</h2>
        </div>
        <div class="fanout-list">
          ${fanOutSummary.length
            ? fanOutSummary
                .slice(0, 8)
                .map(
                  (item) => `
                    <div class="kv-item">
                      <strong>${escapeHtml(item.query || "Untitled query")}</strong>
                      <span>
                        Used ${escapeHtml(String(numberOrZero(item.count)))} times.
                        Appeared in ${escapeHtml(String(numberOrZero(item.appeared_in_responses)))} final responses.
                        Cited in ${escapeHtml(String(numberOrZero(item.cited_in_responses)))} responses.
                      </span>
                    </div>
                  `
                )
                .join("")
            : '<p class="section-copy">No fan-out queries were captured in this run.</p>'}
        </div>
      </article>
    </section>
  `;

  const sourcesSection = `
    <section class="split">
      <article class="panel">
        <div class="panel-heading">
          <h2>Prompt Coverage</h2>
        </div>
        <div class="prompt-list">
          ${topPrompts
            .map(
              (prompt) => `
                <div class="domain-card">
                  <strong>${escapeHtml(prompt.prompt)}</strong>
                  <span>
                    ${prompt.responses.length} responses.
                    Visibility ${percent(prompt.visibilityRate)}.
                    Citation rate ${percent(prompt.citationRate)}.
                    Search triggered ${prompt.usedWebSearchCount}/${prompt.responses.length}.
                  </span>
                </div>
              `
            )
            .join("")}
        </div>
      </article>
      <article class="panel">
        <div class="panel-heading">
          <h2>Most Cited Domains</h2>
        </div>
        <div class="sources-list">
          ${topDomains.length
            ? topDomains
                .map(
                  (domain) => `
                    <div class="domain-card">
                      <strong>${escapeHtml(domain.domain)}</strong>
                      <span>${domain.count} source appearances across ${domain.pages} unique pages.</span>
                    </div>
                  `
                )
                .join("")
            : '<p class="section-copy">No citation domains were captured.</p>'}
        </div>
      </article>
    </section>
  `;

  const responsesSection = `
    <section class="response-section">
      <article class="panel">
        <div class="panel-heading">
          <h2>Prompt Responses</h2>
        </div>
        <p class="section-copy">
          Each captured answer is rendered from Markdown to HTML so the audit reads like a finished deliverable instead of raw JSON.
        </p>
        <div style="margin-top: 16px;">
          ${promptSummaries
            .map(
              (promptSummary) => `
                <section class="response-card">
                  <h3>${escapeHtml(promptSummary.prompt)}</h3>
                  <div class="response-meta">
                    <span class="chip">Responses ${escapeHtml(String(promptSummary.responses.length))}</span>
                    <span class="chip ${promptSummary.visibilityRate >= 0.5 ? "chip--good" : "chip--warn"}">Visibility ${escapeHtml(percent(promptSummary.visibilityRate))}</span>
                    <span class="chip ${promptSummary.citationRate >= 0.3 ? "chip--good" : "chip--warn"}">Citations ${escapeHtml(percent(promptSummary.citationRate))}</span>
                  </div>
                  ${promptSummary.responses
                    .map((response) => {
                      const fanOutDetails = Array.isArray(response.fan_out_details) ? response.fan_out_details : [];
                      const sourceItems = Array.isArray(response.sources) ? response.sources : [];
                      return `
                        <div class="response-grid">
                          <div>
                            <div class="response-meta">
                              <span class="chip">${escapeHtml(response.model || response.chatbot || "Unknown chatbot")}</span>
                              <span class="chip ${response.cited ? "chip--good" : numberOrZero(response.mentions) > 0 ? "chip--warn" : "chip--bad"}">
                                ${response.cited ? "Cited" : numberOrZero(response.mentions) > 0 ? "Mentioned only" : "Not visible"}
                              </span>
                              <span class="chip">${response.used_web_search ? "Search triggered" : "No search"}</span>
                              <span class="chip">Captured ${escapeHtml(formatTimestamp(response.captured_at || audit.run_at))}</span>
                            </div>
                            <div class="markdown-body" style="margin-top: 12px;">
                              ${renderMarkdown(response.answer_text_markdown)}
                            </div>
                          </div>
                          <div class="kv-list">
                            <div class="kv-item">
                              <strong>Visibility</strong>
                              <span>
                                Mentions: ${escapeHtml(String(numberOrZero(response.mentions)))}.
                                Citations: ${escapeHtml(String(numberOrZero(response.citations_count)))}.
                                First citation rank: ${response.first_citation_rank ? `#${escapeHtml(String(response.first_citation_rank))}` : "n/a"}.
                              </span>
                            </div>
                            <div class="kv-item">
                              <strong>Brands mentioned</strong>
                              <span>${escapeHtml(unique(response.brands_mentioned || []).join(", ") || "None captured.")}</span>
                            </div>
                            <div class="kv-item">
                              <strong>Fan-out</strong>
                              <span>${escapeHtml(
                                fanOutDetails.length
                                  ? fanOutDetails.map((detail) => detail.query).filter(Boolean).join(" | ")
                                  : Array.isArray(response.fan_out_queries) && response.fan_out_queries.length
                                    ? response.fan_out_queries.join(" | ")
                                    : "No fan-out queries captured."
                              )}</span>
                            </div>
                            <div class="kv-item">
                              <strong>Top sources</strong>
                              <span>
                                ${
                                  sourceItems.length
                                    ? sourceItems
                                        .slice(0, 5)
                                        .map((source) => {
                                          const label = source.title || source.domain || source.url || "Untitled source";
                                          return toLink(source.url, label);
                                        })
                                        .join("<br />")
                                    : "No source list available."
                                }
                              </span>
                            </div>
                          </div>
                        </div>
                      `;
                    })
                    .join("")}
                </section>
              `
            )
            .join("")}
        </div>
      </article>
    </section>
  `;

  const footer = `
    <p class="footer">
      Generated from <span class="mono">results.json</span> as a standalone HTML export.
    </p>
  `;

  return [hero, metrics, executiveSummary, chatbotSection, sourcesSection, responsesSection, footer].join("\n");
};

const main = async () => {
  const args = parseArgs(process.argv.slice(2));
  const inputPath = String(args.in ?? args.input ?? "").trim();
  if (!inputPath) {
    console.error("Missing --in <results.json>");
    process.exit(2);
  }

  const inputAbsolutePath = path.resolve(process.cwd(), inputPath);
  const inputDir = path.dirname(inputAbsolutePath);
  const raw = await fs.readFile(inputAbsolutePath, "utf8");
  const audit = JSON.parse(raw);

  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  const templatePath = String(args.template ?? path.resolve(scriptDir, "../templates/report.html")).trim();
  const outFileName = String(args.out ?? "report.html").trim();
  const outPath = path.resolve(inputDir, outFileName);
  const duplicateToCwd = String(args["copy-to-cwd"] ?? "true").trim() !== "false";
  const cwdOutPath = path.resolve(
    process.cwd(),
    String(args["cwd-out"] ?? `geo-audit-report-${slugify(path.basename(inputDir))}.html`).trim()
  );

  const template = await fs.readFile(templatePath, "utf8");
  const reportContent = buildReport(audit);
  const html = template.replace("__REPORT_CONTENT__", reportContent);

  await fs.writeFile(outPath, html, "utf8");

  if (duplicateToCwd && cwdOutPath !== outPath) {
    await fs.writeFile(cwdOutPath, html, "utf8");
  }

  const result = {
    report_path: outPath,
    report_url: `file://${outPath}`,
    cwd_report_path: duplicateToCwd ? cwdOutPath : null,
    cwd_report_url: duplicateToCwd ? `file://${cwdOutPath}` : null,
  };

  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
};

main().catch((error) => {
  console.error(error?.stack || String(error));
  process.exit(1);
});
