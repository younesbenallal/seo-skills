# Crawl data sources

`scripts/crawl.py` is the default. It needs nothing installed, crawls a few hundred pages a minute, and reads raw HTML, which is exactly what AI crawlers see. Use a dedicated crawler when:

- the site has more than about 2,000 URLs and the user wants a complete crawl,
- the client wants a crawl file they can open themselves,
- the site is JS-dependent (`render_check.py` says so) and a full rendered crawl is needed.

In every case, normalize the export to the same questions as `summary.json` (status, indexability, canonical, title, H1, depth, inlinks), and say which tool and settings produced the data.

## Screaming Frog (paid licence for more than 500 URLs, JS rendering, saving)

Check whether it is available before suggesting it:

1. **MCP**: look for callable Screaming Frog tools (the official MCP shipped with SEO Spider v24, enabled under Configuration > MCP Server; community wrapper: [bzsasson/screaming-frog-mcp](https://github.com/bzsasson/screaming-frog-mcp)). If present, start a crawl and read the Internal, Response Codes, Canonicals, and All Inlinks data through it.
2. **CLI**: macOS `/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher`, Linux `screamingfrogseospider`, Windows `ScreamingFrogSEOSpiderCli.exe`.

```bash
"/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher" \
  --crawl https://example.com --headless --save-crawl --output-folder ./audit-run/sf \
  --export-tabs "Internal:All,Response Codes:Client Error (4xx),Canonicals:All" \
  --bulk-export "Links:All Inlinks"
```

JavaScript rendering and exclusions can only be set through a config file saved from the GUI (`--config file.seospiderconfig`). Tab names must match the UI labels exactly.

3. **User export**: if the user runs the crawl in the GUI, ask for `internal_all.csv` and `all_inlinks.csv` (Bulk Export > Links > All Inlinks).

Useful columns in `internal_all.csv`: `Address`, `Status Code`, `Indexability`, `Indexability Status`, `Title 1`, `H1-1`, `Canonical Link Element 1`, `Meta Robots 1`, `Crawl Depth`, `Unique Inlinks`, `Word Count`. In `all_inlinks.csv`: `Source`, `Destination`, `Anchor`, `Link Position` (Content / Navigation / Footer), `Follow`.

## LibreCrawl (free, open source)

[LibreCrawl](https://librecrawl.com) ([GitHub](https://github.com/PhialsBasement/LibreCrawl), MIT) is a Flask web app with optional Playwright rendering and CSV/JSON/XLSX exports. It has no crawl CLI: the user starts crawls in its local web UI.

Install it only with the user's approval, in a folder they choose (not inside the client project):

```bash
git clone https://github.com/PhialsBasement/LibreCrawl.git
cd LibreCrawl
cp .env.example .env
docker compose up -d
```

Without Docker: `pip install -r requirements.txt`, `playwright install chromium`, then `python main.py --local`. Open the local URL it prints, run the crawl, and export URLs and links as CSV. Its local API (`/api/start_crawl`, `/api/crawl_status`, `/api/export_stream?format=csv&type=urls|links|issues`) exists but is untested here; prefer the UI.

## Other options

- **SEOnaut** (free, Go + MySQL, Docker): issue buckets by severity; web UI only.
- **Sitebulb**: paid desktop crawler with good JS rendering and internal-link reports.
- A full-site rendered crawl is rarely needed for B2B SaaS sites: `render_check.py` on one URL per template usually settles whether rendering is a problem.
