#!/usr/bin/env node
/**
 * Lightweight "site:" link opportunity miner using Serper.dev.
 *
 * This script is intentionally simple: it builds a set of Google queries and returns
 * candidate prospect URLs where a link could reasonably be added.
 *
 * Requirements:
 * - SERPER_API_KEY env var (or --api-key)
 *
 * Example:
 *   SERPER_API_KEY=... node linking-opportunities/scripts/link-opps.mjs \
 *     --prospect example.com \
 *     --keywords "seo agency,content update,internal linking" \
 *     --pages 2
 */

import process from "node:process";

const SERPER_ENDPOINT = "https://google.serper.dev/search";

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

const toInt = (value, fallback) => {
	const parsed = Number.parseInt(String(value ?? ""), 10);
	return Number.isFinite(parsed) ? parsed : fallback;
};

const uniq = (arr) => Array.from(new Set(arr));

const normalizeHost = (domain) => domain.replace(/^https?:\/\//, "").replace(/\/.*$/, "").trim().toLowerCase();

const callSerper = async ({ apiKey, q, gl, hl, page }) => {
	const response = await fetch(SERPER_ENDPOINT, {
		method: "POST",
		headers: {
			"X-API-KEY": apiKey,
			"Content-Type": "application/json",
		},
		body: JSON.stringify({ q, gl, hl, page, num: 10 }),
	});

	if (!response.ok) {
		const text = await response.text().catch(() => "");
		throw new Error(`Serper error (${response.status}): ${text || response.statusText}`);
	}
	return response.json();
};

const main = async () => {
	const args = parseArgs(process.argv.slice(2));
	const apiKey = String(args["api-key"] ?? process.env.SERPER_API_KEY ?? "").trim();
	if (!apiKey) {
		console.error("Missing SERPER_API_KEY (env) or --api-key");
		process.exit(2);
	}

	const prospect = normalizeHost(String(args.prospect ?? ""));
	if (!prospect) {
		console.error("Missing required --prospect (domain, e.g. example.com)");
		process.exit(2);
	}

	const keywordsRaw = String(args.keywords ?? "").trim();
	const keywords = uniq(
		keywordsRaw
			.split(",")
			.map((k) => k.trim())
			.filter(Boolean),
	);

	const gl = String(args.gl ?? "us");
	const hl = String(args.hl ?? "en");
	const pages = Math.min(5, Math.max(1, toInt(args.pages ?? 2, 2)));

	const baseQueries = [
		`site:${prospect} (resources OR tools OR glossary OR directory OR partners OR integrations)`,
		`site:${prospect} ("recommended" OR "we use" OR "stack" OR "alternatives")`,
	];

	const keywordQueries = keywords.flatMap((keyword) => [
		`site:${prospect} "${keyword}"`,
		`site:${prospect} ${keyword}`,
		`site:${prospect} (resources OR tools OR guide OR checklist) ${keyword}`,
	]);

	const queries = uniq([...baseQueries, ...keywordQueries]).slice(0, 40);

	const candidates = new Map();

	for (const query of queries) {
		for (let page = 1; page <= pages; page += 1) {
			const result = await callSerper({ apiKey, q: query, gl, hl, page });
			const organic = Array.isArray(result?.organic) ? result.organic : [];
			for (const item of organic) {
				const url = String(item?.link ?? "").trim();
				if (!url) continue;
				if (!candidates.has(url)) {
					candidates.set(url, { url, firstSeenQuery: query, title: item?.title ?? null, snippet: item?.snippet ?? null });
				}
			}
			if (organic.length === 0) break;
		}
	}

	const output = {
		prospect,
		gl,
		hl,
		queryCount: queries.length,
		candidates: Array.from(candidates.values()),
	};

	process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
};

main().catch((error) => {
	console.error(error?.stack || String(error));
	process.exit(1);
});
