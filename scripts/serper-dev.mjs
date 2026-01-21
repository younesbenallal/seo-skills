#!/usr/bin/env node
/**
 * Minimal Serper.dev client (Google SERP API).
 *
 * Usage:
 *   SERPER_API_KEY=... node scripts/serper-dev.mjs --q 'site:example.com pricing' --pages 3
 *
 * Notes:
 * - The Serper API is paid and requires an API key.
 * - This script returns raw JSON (plus a convenience `organic_all` array when paginating).
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

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const callSerper = async ({ apiKey, q, gl, hl, num, page }) => {
	const body = {
		q,
		num,
		gl,
		hl,
		page,
	};

	const response = await fetch(SERPER_ENDPOINT, {
		method: "POST",
		headers: {
			"X-API-KEY": apiKey,
			"Content-Type": "application/json",
		},
		body: JSON.stringify(body),
	});

	if (!response.ok) {
		const text = await response.text().catch(() => "");
		throw new Error(`Serper error (${response.status}): ${text || response.statusText}`);
	}

	return response.json();
};

const main = async () => {
	const args = parseArgs(process.argv.slice(2));
	const q = String(args.q ?? args.query ?? "").trim();
	if (!q) {
		console.error("Missing required argument: --q");
		process.exit(2);
	}

	const apiKey = String(args["api-key"] ?? process.env.SERPER_API_KEY ?? "").trim();
	if (!apiKey) {
		console.error("Missing SERPER_API_KEY (env) or --api-key");
		process.exit(2);
	}

	const gl = String(args.gl ?? "us");
	const hl = String(args.hl ?? "en");
	const num = Math.min(100, Math.max(1, toInt(args.num ?? 10, 10)));
	const pages = Math.min(10, Math.max(1, toInt(args.pages ?? 1, 1)));
	const delayMs = Math.max(0, toInt(args["delay-ms"] ?? 200, 200));

	const results = [];
	const organicAll = [];

	for (let page = 1; page <= pages; page += 1) {
		const result = await callSerper({ apiKey, q, gl, hl, num: Math.min(10, num), page });
		results.push({ page, result });

		const organic = Array.isArray(result?.organic) ? result.organic : [];
		for (const item of organic) {
			if (item && typeof item === "object") organicAll.push(item);
		}

		if (organic.length === 0) break;
		if (delayMs > 0 && page < pages) await sleep(delayMs);
	}

	const output = {
		query: q,
		gl,
		hl,
		pagesRequested: pages,
		pagesReturned: results.length,
		organic_all: organicAll.map((item, index) => ({ ...item, position: index + 1 })),
		raw: results,
	};

	process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
};

main().catch((error) => {
	console.error(error?.stack || String(error));
	process.exit(1);
});
