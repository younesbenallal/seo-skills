#!/usr/bin/env node
/**
 * Render a roast JSON into an HTML report.
 *
 * This is a convenience script. The assistant can also directly generate HTML.
 *
 * Input JSON shape (minimal):
 * {
 *   "title": "SEO Roast Report",
 *   "generatedAt": "2026-01-01",
 *   "pages": [{ "url": "...", "topFixes": ["..."], "quickWins": ["..."], "intentGaps": ["..."], "notes": ["..."] }],
 *   "screenshots": [{ "label": "Above the fold", "dataUrl": "data:image/jpeg;base64,..." }]
 * }
 */

import fs from "node:fs/promises";
import process from "node:process";
import path from "node:path";
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
		.replaceAll("'", "&#039;");

const renderList = (items) => {
	const safe = Array.isArray(items) ? items : [];
	return `<ul class="list">${safe.map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ul>`;
};

const main = async () => {
	const args = parseArgs(process.argv.slice(2));
	const inputPath = String(args.in ?? args.input ?? "").trim();
	const scriptDir = path.dirname(fileURLToPath(import.meta.url));
	const templatePath = String(args.template ?? path.resolve(scriptDir, "../templates/report.html")).trim();
	const outPath = String(args.out ?? "report.html").trim();

	if (!inputPath) {
		console.error("Missing --in <roast.json>");
		process.exit(2);
	}

	const raw = await fs.readFile(inputPath, "utf8");
	const data = JSON.parse(raw);

	const template = await fs.readFile(templatePath, "utf8");

	const meta = `${escapeHtml(data.generatedAt ?? new Date().toISOString())}`;
	const pages = Array.isArray(data.pages) ? data.pages : [];

	const summaryHtml = pages
		.map((p) => {
			const url = escapeHtml(p.url ?? "");
			return `
        <div class="card">
          <h2>${url ? `Page: <a href="${url}">${url}</a>` : "Page"}</h2>
          <h3 class="small">Top 5 fixes</h3>
          ${renderList(p.topFixes)}
          <h3 class="small">Quick wins</h3>
          ${renderList(p.quickWins)}
          <h3 class="small">Intent gaps</h3>
          ${renderList(p.intentGaps)}
          <h3 class="small">Notes</h3>
          ${renderList(p.notes)}
        </div>
      `;
		})
		.join("");

	const screenshots = Array.isArray(data.screenshots) ? data.screenshots : [];
	const screenshotsHtml =
		screenshots.length === 0
			? `<p class="small">No screenshots provided.</p>`
			: `<div class="screens">${screenshots
					.slice(0, 6)
					.map(
						(s) =>
							`<figure><img alt="${escapeHtml(s.label ?? "Screenshot")}" src="${escapeHtml(s.dataUrl ?? "")}" /></figure>`,
					)
					.join("")}</div>`;

	const html = template
		.replace("SEO Roast Report", escapeHtml(data.title ?? "SEO Roast Report"))
		.replace('id="meta">Replace this template by rendering your findings.</div>', `id="meta">Generated at: ${meta}</div>`)
		.replace(
			'<section class="card" id="summary">\n\t\t\t\t\t<h2>Summary</h2>\n\t\t\t\t\t<ul class="list">\n\t\t\t\t\t\t<li>Top 5 fixes: …</li>\n\t\t\t\t\t\t<li>Quick wins: …</li>\n\t\t\t\t\t\t<li>Search intent gaps: …</li>\n\t\t\t\t\t</ul>\n\t\t\t\t</section>',
			`<section class="card" id="summary"><h2>Pages</h2>${summaryHtml || "<p>No pages in input.</p>"}</section>`,
		)
		.replace(
			'<div class="screens">\n\t\t\t\t\t\t<figure><img alt="Screenshot placeholder" src="" /></figure>\n\t\t\t\t\t\t<figure><img alt="Screenshot placeholder" src="" /></figure>\n\t\t\t\t\t</div>',
			screenshotsHtml,
		);

	await fs.writeFile(outPath, html, "utf8");
	process.stdout.write(`Wrote ${outPath}\n`);
};

main().catch((error) => {
	console.error(error?.stack || String(error));
	process.exit(1);
});
