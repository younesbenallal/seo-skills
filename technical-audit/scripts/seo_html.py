"""Shared helpers for the technical-audit scripts: HTTP fetch, HTML extraction, robots.txt, sitemaps.

Python 3 standard library only.
"""

import gzip
import json
import re
import ssl
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)
MAX_BYTES = 6_000_000
ASSET_EXT = re.compile(
    r"\.(jpe?g|png|gif|webp|avif|svg|ico|css|js|mjs|json|xml|txt|pdf|zip|gz|mp4|webm|mp3|wav|woff2?|ttf|eot|docx?|xlsx?|pptx?|csv)$",
    re.I,
)
TRACKING_PARAMS = re.compile(r"^(utm_|gclid|fbclid|msclkid|mc_|ref$|hsa_|_hs)", re.I)


# ---------- URLs ----------


def normalize_url(url, base=None):
    """Absolute URL without fragment, lowercase scheme and host, default path '/'."""
    if base:
        url = urljoin(base, url)
    url, _ = urldefrag(url.strip())
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return None
    host = (parts.hostname or "").lower()
    if not host:
        return None
    netloc = host if not parts.port or parts.port in (80, 443) else f"{host}:{parts.port}"
    return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, ""))


def bare_host(url_or_host):
    host = urlsplit(url_or_host).hostname if "://" in url_or_host else url_or_host
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


def same_site(url, site_host):
    return bare_host(url) == bare_host(site_host)


def is_asset(url):
    return bool(ASSET_EXT.search(urlsplit(url).path))


# ---------- HTTP ----------


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_OPENER = urllib.request.build_opener(
    _NoRedirect, urllib.request.HTTPSHandler(context=ssl.create_default_context())
)


def _decode_body(raw, encoding):
    encoding = (encoding or "").lower()
    if encoding == "gzip" or raw[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(raw)
        except OSError:
            return raw
    if encoding == "deflate":
        try:
            return zlib.decompress(raw)
        except zlib.error:
            return zlib.decompress(raw, -zlib.MAX_WBITS)
    return raw


def _charset(content_type, raw):
    match = re.search(r"charset=([\w-]+)", content_type or "", re.I)
    if match:
        return match.group(1)
    match = re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", raw[:4096], re.I)
    return match.group(1).decode("ascii", "ignore") if match else "utf-8"


def fetch_once(url, user_agent=BROWSER_UA, timeout=20, method="GET"):
    """One request, no redirect following. Returns a dict with status, headers, text, elapsed."""
    request = urllib.request.Request(
        url,
        method=method,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en,fr;q=0.8",
            "Accept-Encoding": "gzip",
        },
    )
    started = time.monotonic()
    try:
        response = _OPENER.open(request, timeout=timeout)
        status = response.status
    except urllib.error.HTTPError as error:
        response = error
        status = error.code
    except Exception as error:  # DNS, TLS, timeout
        return {"url": url, "status": 0, "error": f"{type(error).__name__}: {error}", "headers": {}, "text": "", "elapsed": round(time.monotonic() - started, 2)}
    headers = {key.lower(): value for key, value in response.headers.items()}
    raw = b""
    if method != "HEAD":
        try:
            raw = response.read(MAX_BYTES)
        except Exception:
            raw = b""
    raw = _decode_body(raw, headers.get("content-encoding"))
    text = raw.decode(_charset(headers.get("content-type"), raw), errors="replace")
    return {"url": url, "status": status, "headers": headers, "text": text, "elapsed": round(time.monotonic() - started, 2)}


def fetch(url, user_agent=BROWSER_UA, timeout=20, max_hops=10):
    """Follow redirects manually and keep the chain. Returns the final response plus `chain`."""
    chain = []
    current = url
    for _ in range(max_hops + 1):
        response = fetch_once(current, user_agent=user_agent, timeout=timeout)
        location = response["headers"].get("location")
        if response["status"] in (301, 302, 303, 307, 308) and location:
            chain.append({"url": current, "status": response["status"]})
            nxt = normalize_url(location, base=current)
            if not nxt or nxt in [hop["url"] for hop in chain]:
                response["error"] = "redirect loop or invalid location"
                break
            current = nxt
            continue
        break
    response["chain"] = chain
    response["requested_url"] = url
    response["final_url"] = current
    return response


# ---------- HTML extraction ----------

TEMPLATE_TAGS = {"nav", "header", "footer"}
SKIP_TEXT_TAGS = {"script", "style", "noscript", "template", "svg", "head"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self._in_title = False
        self.meta = {}
        self.links_rel = {}
        self.hreflang = []
        self.h1 = []
        self._h1_buf = None
        self.html_lang = None
        self.links = []
        self._anchor = None
        self.fake_links = []
        self.jsonld = []
        self._jsonld_buf = None
        self.words = 0
        self.texts = []
        self.unique_words = 0
        self._seen_text = set()
        self._skip = 0
        self._template = 0
        self.scripts = 0
        self.forms = 0
        self.iframes = []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.html_lang = a.get("lang") or None
        elif tag == "title" and self.title is None:
            self._in_title = True
            self.title = ""
        elif tag == "meta":
            name = (a.get("name") or a.get("property") or a.get("http-equiv") or "").lower()
            if name:
                self.meta.setdefault(name, a.get("content", ""))
        elif tag == "link":
            rel = a.get("rel", "").lower()
            if "canonical" in rel.split():
                self.links_rel.setdefault("canonical", []).append(a.get("href", ""))
            if "alternate" in rel.split() and a.get("hreflang"):
                self.hreflang.append({"hreflang": a["hreflang"], "href": a.get("href", "")})
        elif tag == "h1":
            self._h1_buf = ""
        elif tag == "a":
            href = a.get("href")
            if href is not None:
                self._anchor = {"href": href, "text": "", "rel": a.get("rel", "").lower(), "template": self._template > 0}
            elif a.get("role") == "link" or "onclick" in a:
                self.fake_links.append({"tag": "a", "attrs": _fake_link_attrs(a)})
        elif tag == "script":
            self.scripts += 1
            if "ld+json" in a.get("type", "").lower():
                self._jsonld_buf = ""
        elif tag == "form":
            self.forms += 1
        elif tag == "iframe":
            self.iframes.append(a.get("src", ""))
        if tag != "a" and (a.get("role") == "link" or any(k in a for k in ("data-href", "data-url", "data-link", "data-ofb64"))):
            self.fake_links.append({"tag": tag, "attrs": _fake_link_attrs(a)})
        if tag in TEMPLATE_TAGS:
            self._template += 1
        if tag in SKIP_TEXT_TAGS:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1" and self._h1_buf is not None:
            self.h1.append(" ".join(self._h1_buf.split()))
            self._h1_buf = None
        elif tag == "a" and self._anchor is not None:
            self._anchor["text"] = " ".join(self._anchor["text"].split())[:200]
            self.links.append(self._anchor)
            self._anchor = None
        elif tag == "script" and self._jsonld_buf is not None:
            self.jsonld.append(self._jsonld_buf)
            self._jsonld_buf = None
        if tag in TEMPLATE_TAGS and self._template:
            self._template -= 1
        if tag in SKIP_TEXT_TAGS and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._jsonld_buf is not None:
            self._jsonld_buf += data
            return
        if self._in_title:
            self.title += data
            return
        if self._skip:
            return
        if self._h1_buf is not None:
            self._h1_buf += data
        if self._anchor is not None:
            self._anchor["text"] += data
        self.words += len(re.findall(r"\w+", data))
        chunk = " ".join(data.split())
        if chunk and chunk not in self._seen_text:
            # Responsive sites often repeat blocks for mobile and desktop: count each text once.
            self._seen_text.add(chunk)
            self.unique_words += len(re.findall(r"\w+", chunk))
        if len(chunk) >= 40 and len(self.texts) < 3000:
            self.texts.append(chunk)


def _fake_link_attrs(attrs):
    keep = ("role", "onclick", "data-href", "data-url", "data-link", "data-ofb64", "class")
    return {k: v[:120] for k, v in attrs.items() if k in keep}


def _jsonld_types(blocks):
    types = []

    def walk(node):
        if isinstance(node, dict):
            value = node.get("@type")
            if isinstance(value, str):
                types.append(value)
            elif isinstance(value, list):
                types.extend(str(v) for v in value)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    invalid = 0
    for block in blocks:
        try:
            walk(json.loads(block))
        except (json.JSONDecodeError, ValueError):
            invalid += 1
    return sorted(set(types)), invalid


def extract(html, url):
    """SEO-relevant fields from one HTML document."""
    parser = PageParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass
    canonicals = [normalize_url(c, base=url) or c for c in parser.links_rel.get("canonical", [])]
    links = []
    for link in parser.links:
        target = normalize_url(link["href"], base=url)
        if target:
            links.append({"url": target, "text": link["text"], "nofollow": "nofollow" in link["rel"], "template": link["template"]})
    schema_types, schema_invalid = _jsonld_types(parser.jsonld)
    robots = ", ".join(v for k, v in parser.meta.items() if k in ("robots", "googlebot") and v)
    return {
        "title": " ".join((parser.title or "").split()) or None,
        "meta_description": parser.meta.get("description") or None,
        "meta_robots": robots or None,
        "canonical": canonicals[0] if canonicals else None,
        "canonical_count": len(canonicals),
        "h1": parser.h1,
        "lang": parser.html_lang,
        "viewport": bool(parser.meta.get("viewport")),
        "hreflang": parser.hreflang,
        "word_count": parser.words,
        "unique_word_count": parser.unique_words,
        "texts": parser.texts,
        "links": links,
        "fake_links": parser.fake_links,
        "schema_types": schema_types,
        "schema_invalid_blocks": schema_invalid,
        "scripts": parser.scripts,
        "forms": parser.forms,
        "iframes": parser.iframes[:10],
        "og_title": parser.meta.get("og:title") or None,
    }


def is_noindex(meta_robots, x_robots_tag):
    values = f"{meta_robots or ''},{x_robots_tag or ''}".lower()
    return "noindex" in values or re.search(r"\bnone\b", values) is not None


# ---------- robots.txt (Google's rules: most specific group, longest match, * and $) ----------


def parse_robots(text):
    """Return groups [{agents: [...], rules: [(allow: bool, path)]}], sitemaps, other directives."""
    groups, sitemaps, other = [], [], []
    current = None
    last_was_agent = False
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if not last_was_agent or current is None:
                current = {"agents": [], "rules": []}
                groups.append(current)
            current["agents"].append(value.lower())
            last_was_agent = True
            continue
        last_was_agent = False
        if key in ("allow", "disallow") and current is not None:
            if value or key == "allow":
                current["rules"].append((key == "allow", value))
        elif key == "sitemap":
            sitemaps.append(value)
        else:
            other.append({"directive": key, "value": value})
    return {"groups": groups, "sitemaps": sitemaps, "other": other}


def _group_for(parsed, token):
    token = token.lower()
    best, best_len = None, -1
    for group in parsed["groups"]:
        for agent in group["agents"]:
            if agent != "*" and token.startswith(agent) and len(agent) > best_len:
                best, best_len = group, len(agent)
    if best is not None:
        # Google merges every group that names the same agent.
        name = next(a for a in best["agents"] if token.startswith(a) and len(a) == best_len)
        rules = [r for g in parsed["groups"] if name in g["agents"] for r in g["rules"]]
        return {"agents": [name], "rules": rules}
    rules = [r for g in parsed["groups"] if "*" in g["agents"] for r in g["rules"]]
    return {"agents": ["*"], "rules": rules} if any("*" in g["agents"] for g in parsed["groups"]) else None


def _rule_regex(path):
    anchored = path.endswith("$")
    body = re.escape(path[:-1] if anchored else path).replace(r"\*", ".*")
    return re.compile("^" + body + ("$" if anchored else ""))


def robots_allows(parsed, token, url):
    """(allowed, matched_group, matched_rule) for a user-agent token and a URL."""
    group = _group_for(parsed, token)
    if group is None:
        return True, None, None
    parts = urlsplit(url)
    path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
    best = None
    for allow, rule in group["rules"]:
        if rule == "":
            continue
        if _rule_regex(rule).match(path):
            length = len(rule)
            if best is None or length > best[0] or (length == best[0] and allow):
                best = (length, allow, rule)
    if best is None:
        return True, group["agents"][0], None
    return best[1], group["agents"][0], ("Allow: " if best[1] else "Disallow: ") + best[2]


# ---------- sitemaps ----------

COMMON_SITEMAPS = ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml", "/wp-sitemap.xml")


def sitemap_seeds(origin, declared):
    """Sitemaps declared in robots.txt, or the common default paths that exist."""
    if declared:
        return declared
    found = [origin + path for path in COMMON_SITEMAPS if fetch_once(origin + path, method="HEAD")["status"] == 200]
    return found or [origin + "/sitemap.xml"]

SM_NS = re.compile(r"^\{[^}]+\}")


def _local(tag):
    return SM_NS.sub("", tag)


def load_sitemaps(urls, user_agent=BROWSER_UA, limit_files=200, limit_urls=50000):
    """Fetch sitemap files recursively. Returns {files: [...], urls: {url: lastmod}}."""
    files, found = [], {}
    queue, seen = list(urls), set()
    while queue and len(seen) < limit_files and len(found) < limit_urls:
        sitemap_url = queue.pop(0)
        if sitemap_url in seen:
            continue
        seen.add(sitemap_url)
        response = fetch(sitemap_url, user_agent=user_agent)
        entry = {"url": sitemap_url, "status": response["status"], "final_url": response["final_url"], "type": None, "count": 0, "lastmod_count": 0}
        files.append(entry)
        if response["status"] != 200 or not response["text"].strip():
            entry["error"] = response.get("error") or "empty or non-200"
            continue
        try:
            root = ET.fromstring(response["text"].encode("utf-8", "replace"))
        except ET.ParseError as error:
            entry["error"] = f"XML parse error: {error}"
            continue
        entry["type"] = _local(root.tag)
        for node in root:
            loc = lastmod = None
            for child in node:
                name = _local(child.tag)
                if name == "loc":
                    loc = (child.text or "").strip()
                elif name == "lastmod":
                    lastmod = (child.text or "").strip()
            if not loc:
                continue
            entry["count"] += 1
            entry["lastmod_count"] += 1 if lastmod else 0
            if entry["type"] == "sitemapindex":
                queue.append(loc)
            else:
                found.setdefault(normalize_url(loc) or loc, lastmod)
    return {"files": files, "urls": found}
