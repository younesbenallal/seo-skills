import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ANSWER_TEXT = """Voici ma sélection.

<box gap={3}>
  <row align=start gap={3}>
    <AsyncImage query="Target dashboard" aspectRatio="4:3"/>
    <box flex="1" gap={1}>
      <title size="lg">1. <Entity value="Target Brand" category="software" disambig="treasury"/></title>
      <badge color="success">Premier choix</badge>
      **Pour les groupes.** <Cite refs={["turn1search2"]}/>
      <text color="secondary" size="sm">Site : <Link url="https://www.target.example/" title="target.example"/></text>
    </box>
  </row>
</box>

2. <Entity value="Rival" category="company" disambig="rival"/>"""


SKILL_DIR = Path(__file__).parents[1]


def answer(**extra):
    return {
        "prompt": "Meilleur logiciel ?",
        "url": "https://chatgpt.com/c/abc-123",
        "text": "ChatGPT said: Voici ma sélection.",
        "links": [
            {"text": "target.example", "href": "https://www.target.example/"},
            {"text": "Share", "href": "https://chatgpt.com/share"},
        ],
        "at": "2026-10-12T09:51:08.123Z",
        **extra,
    }


CAPTURE = {
    "convKey": "chatgpt:abc-123",
    "capture": {
        "query": "Meilleur logiciel ?",
        "model": {"requested": "auto", "resolved": "gpt-test"},
        "searchedWeb": True,
        "fanout": ["logiciel tresorerie comparatif"],
        "sources": [
            {"url": "https://www.target.example/page", "title": "Target", "host": "target.example", "cited": False},
            {"url": "https://www.target.example/page", "title": "Target", "host": "target.example", "cited": False},
            {"url": "https://rival.example/", "title": "Rival", "host": "rival.example", "cited": False},
        ],
        "raw": {"answerText": ANSWER_TEXT},
    },
}


def normalize(answers, captures):
    with tempfile.TemporaryDirectory() as directory:
        run_dir = Path(directory)
        (run_dir / "raw").mkdir()
        (run_dir / "raw" / "answers.json").write_text(json.dumps(answers), encoding="utf-8")
        (run_dir / "raw" / "fanoutfox.json").write_text(json.dumps(captures), encoding="utf-8")
        subprocess.run(
            [
                sys.executable,
                str(SKILL_DIR / "scripts" / "normalize-chatgpt-browser.py"),
                "--run-dir", str(run_dir),
                "--check-url", "https://www.target.example",
                "--target-domains", "target.example",
                "--brand-terms", "Target Brand",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads((run_dir / "results.json").read_text(encoding="utf-8"))


class ChatGPTBrowserNormalizationTests(unittest.TestCase):
    def test_answers_and_captures_become_v3_results(self):
        payload = normalize(
            [answer(), {"prompt": "Autre prompt ?", "error": "Timeout", "at": "2026-10-12T09:52:00.000Z"}],
            [CAPTURE],
        )

        self.assertEqual(payload["provider"], "chatgpt_browser")
        self.assertEqual(payload["run_at"], "2026-10-12T09:51:08Z")
        self.assertEqual(payload["collection_diagnostics"]["records_rejected"], 1)

        (response,) = payload["responses"]
        markdown = response["answer_text_markdown"]
        self.assertNotIn("<", markdown)
        self.assertIn("### 1. Target Brand", markdown)
        self.assertIn("[target.example](https://www.target.example/)", markdown)
        self.assertGreater(response["mentions"], 0)
        self.assertEqual(response["model"], "gpt-test")
        self.assertEqual(response["brands_mentioned"], ["Target Brand", "Rival"])
        self.assertEqual(response["fan_out_queries"], ["logiciel tresorerie comparatif"])
        self.assertTrue(response["used_web_search"])
        self.assertEqual(len(response["search_sources"]), 2)
        self.assertTrue(response["target_found_in_search"])
        self.assertEqual(len(response["attached_links"]), 1)
        self.assertEqual(response["actual_citations"], [])
        self.assertEqual(response["evidence_status"]["actual_citations"]["state"], "missing")

    def test_resolved_citations_become_actual_citations(self):
        citations = [
            {"code": "turn1search2", "url": "https://rival.example/?utm_source=chatgpt.com", "title": "Rival"},
            {"code": "turn1search0", "url": "https://www.target.example/page", "title": "Target"},
            {"code": "turn1search9", "url": None, "title": None},
        ]
        (response,) = normalize([answer(citations=citations)], [CAPTURE])["responses"]

        self.assertEqual(response["evidence_status"]["actual_citations"]["state"], "supported")
        self.assertEqual([c["domain"] for c in response["actual_citations"]], ["rival.example", "target.example"])
        self.assertTrue(response["cited"])
        self.assertEqual(response["first_citation_rank"], 2)
        self.assertEqual(response["uncited_citation_candidates"], [])


if __name__ == "__main__":
    unittest.main()
