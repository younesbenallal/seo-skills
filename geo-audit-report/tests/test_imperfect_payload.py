import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ImperfectPayloadIntegrationTests(unittest.TestCase):
    def test_partial_run_survives_provider_drift(self):
        skill_dir = Path(__file__).parents[1]
        fixture = Path(__file__).parent / "fixtures" / "brightdata-imperfect.json"

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "results.json"
            subprocess.run(
                [
                    sys.executable,
                    str(skill_dir / "scripts" / "normalize-brightdata-geo.py"),
                    "--raw",
                    str(fixture),
                    "--out",
                    str(output),
                    "--check-url",
                    "https://target.example",
                    "--target-domains",
                    "target.example",
                    "--brand-terms",
                    "Target Brand",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        diagnostics = payload["collection_diagnostics"]
        self.assertEqual(diagnostics["status"], "partial")
        self.assertEqual(diagnostics["records_received"], 3)
        self.assertEqual(diagnostics["records_normalized"], 2)
        self.assertEqual(diagnostics["records_rejected"], 1)
        self.assertGreater(diagnostics["warning_count"], 0)
        self.assertIn("future_provider_field", diagnostics["unknown_provider_fields"])

        first, second = payload["responses"]
        self.assertEqual(first["actual_citations"], [])
        self.assertEqual(
            first["evidence_status"]["actual_citations"]["state"],
            "missing",
        )
        self.assertEqual(first["evidence_status"]["search_sources"]["state"], "inferred")
        self.assertEqual(second["evidence_status"]["maps"]["state"], "malformed")
        self.assertEqual(second["evidence_status"]["web_search"]["state"], "malformed")


if __name__ == "__main__":
    unittest.main()
