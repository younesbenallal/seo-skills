import json
import os
import unittest
from types import SimpleNamespace
from unittest import mock

import collect_serp_outlines as collector


class CollectorTests(unittest.TestCase):
    def test_extracts_html_headings_and_skips_navigation(self):
        document = """
        <html><body>
          <nav><h2>Menu</h2></nav>
          <main><h1>Guide <em>title</em></h1><h2>First   section</h2><h4>Detail</h4></main>
          <footer><h2>Company</h2></footer>
        </body></html>
        """
        self.assertEqual(
            collector.headings_from_html(document),
            [
                {"level": 1, "text": "Guide title"},
                {"level": 2, "text": "First section"},
                {"level": 4, "text": "Detail"},
            ],
        )

    def test_extracts_markdown_headings_outside_code_fences(self):
        markdown = "# Title\n\n## Section\n```md\n# Not a heading\n```\n#### Detail"
        self.assertEqual(
            collector.headings_from_markdown(markdown),
            [
                {"level": 1, "text": "Title"},
                {"level": 2, "text": "Section"},
                {"level": 4, "text": "Detail"},
            ],
        )

    def test_normalizes_only_organic_results_by_rank(self):
        payload = {
            "tasks": [
                {
                    "cost": 0.002,
                    "result": [
                        {
                            "check_url": "https://google.test/",
                            "items": [
                                {"type": "people_also_ask", "rank_group": 1},
                                {
                                    "type": "people_also_ask",
                                    "items": [{"title": "What is an audit?"}],
                                },
                                {
                                    "type": "related_searches",
                                    "items": ["audit template"],
                                },
                                {
                                    "type": "organic",
                                    "rank_group": 2,
                                    "title": "Second",
                                    "url": "https://example.com/two",
                                },
                                {
                                    "type": "organic",
                                    "rank_group": 1,
                                    "title": "First",
                                    "url": "https://example.com/one",
                                },
                                {
                                    "type": "organic",
                                    "rank_group": 3,
                                    "title": "Duplicate",
                                    "url": "https://example.com/one#section",
                                },
                                {
                                    "type": "organic",
                                    "rank_group": 4,
                                    "title": ["malformed"],
                                    "description": {"malformed": True},
                                    "url": 123,
                                },
                            ],
                        }
                    ],
                }
            ]
        }
        results, metadata = collector.normalize_organic_results(payload, 10)
        self.assertEqual([result["title"] for result in results], ["First", "Second"])
        self.assertEqual(metadata["returned_organic_count"], 2)
        self.assertEqual(metadata["people_also_ask"], ["What is an audit?"])
        self.assertEqual(metadata["related_searches"], ["audit template"])

    def test_rejects_local_files_and_private_networks(self):
        with self.assertRaisesRegex(RuntimeError, r"http\(s\)"):
            collector.validate_public_http_url("file:///etc/hosts")
        private_address = [(None, None, None, None, ("127.0.0.1", 80))]
        with mock.patch.object(collector.socket, "getaddrinfo", return_value=private_address):
            with self.assertRaisesRegex(RuntimeError, "non-public"):
                collector.validate_public_http_url("http://example.test/")

    def test_rejects_private_connected_peer(self):
        connection = mock.MagicMock()
        connection.sock.getpeername.return_value = ("169.254.169.254", 80)
        with self.assertRaisesRegex(RuntimeError, "non-public peer"):
            collector.validate_connected_peer(connection)
        connection.close.assert_called_once()

    def test_caps_response_size(self):
        public_address = [(None, None, None, None, ("93.184.216.34", 443))]
        response = mock.MagicMock()
        response.headers = {"Content-Type": "text/html"}
        response.read.return_value = b"x" * (collector.MAX_RESPONSE_BYTES + 1)
        response.geturl.return_value = "https://example.com/"
        context = mock.MagicMock()
        context.__enter__.return_value = response
        opener = mock.MagicMock()
        opener.open.return_value = context
        with (
            mock.patch.object(collector.socket, "getaddrinfo", return_value=public_address),
            mock.patch.object(collector.urllib.request, "build_opener", return_value=opener),
        ):
            with self.assertRaisesRegex(RuntimeError, "response exceeds"):
                collector.request_bytes("https://example.com/", timeout=1)

    def test_builds_localized_dataforseo_request(self):
        args = SimpleNamespace(
            keyword="seo audit",
            language="en",
            depth=10,
            device="desktop",
            os="windows",
            location_code=None,
            country="Malaysia",
            timeout=10,
        )
        response = {
            "status_code": 20000,
            "tasks": [{"status_code": 20000, "result": [{"items": []}]}],
        }
        with (
            mock.patch.dict(
                os.environ,
                {"DATA_FOR_SEO_LOGIN": "login", "DATA_FOR_SEO_PASSWORD": "password"},
                clear=True,
            ),
            mock.patch.object(
                collector,
                "request_bytes",
                return_value=(json.dumps(response).encode(), "application/json", collector.DATAFORSEO_URL),
            ) as request,
        ):
            collector.fetch_dataforseo_serp(args)
        task = json.loads(request.call_args.kwargs["data"])[0]
        self.assertEqual(task["location_name"], "Malaysia")
        self.assertEqual(task["language_code"], "en")
        self.assertEqual(task["depth"], 10)
        self.assertTrue(request.call_args.kwargs["headers"]["Authorization"].startswith("Basic "))

    def test_rejects_malformed_provider_result(self):
        with self.assertRaisesRegex(RuntimeError, "invalid task"):
            collector.normalize_organic_results({"tasks": ["not-a-task"]}, 10)

    def test_render_flattens_and_escapes_untrusted_markdown(self):
        report = {
            "keyword": "example\n## keyword injection",
            "market": {
                "country": "US\n## country injection",
                "location_code": None,
                "language": "en\n## language injection",
            },
            "serp": {"people_also_ask": ["Question\n## injected"], "related_searches": []},
            "organic_count": 1,
            "outline_success_count": 1,
            "results": [
                {
                    "position": 1,
                    "title": "Title\n## injected",
                    "url": "https://example.com/",
                    "snippet": "Snippet\n- fake item",
                    "headings": [{"level": 2, "text": "Section\n# fake heading"}],
                    "error": None,
                }
            ],
        }
        rendered = collector.render_markdown(report)
        self.assertNotIn("\n## injected", rendered)
        self.assertNotIn("\n## keyword injection", rendered)
        self.assertNotIn("\n## country injection", rendered)
        self.assertNotIn("\n## language injection", rendered)
        self.assertNotIn("\n- fake item", rendered)
        self.assertIn(r"\#\# injected", rendered)
        self.assertIn("untrusted external data", rendered)


if __name__ == "__main__":
    unittest.main()
