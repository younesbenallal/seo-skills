import importlib.util
import sys
import unittest
from pathlib import Path


def load_collector():
    path = Path(__file__).parents[1] / "scripts" / "brightdata-geo.py"
    spec = importlib.util.spec_from_file_location("brightdata_geo_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


collector = load_collector()


class BrightDataNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "prompt": "Best video agency in Paris?",
            "answer_text_markdown": "Give feedback\n\n**Couloir 3** is a strong option.",
            "model": "gpt-test",
            "country": "FR",
            "index": 1,
            "web_search_triggered": True,
            "web_search_query": ["video agency paris"],
            "citations": [
                {
                    "url": "https://couloir3.com/?utm_source=chatgpt.com",
                    "title": "Couloir 3 - Video agency",
                    "domain": "Couloir3",
                    "cited": True,
                    "position": 1,
                    "answer_position": 1,
                },
                {
                    "url": "https://candidate.example/work",
                    "title": "Candidate Studio",
                    "domain": "Candidate Studio",
                    "cited": False,
                    "position": 2,
                },
            ],
            "search_sources": [
                {
                    "url": "https://search.example/page",
                    "title": "Search result",
                    "rank": 1,
                }
            ],
            "links_attached": [
                {
                    "url": "https://couloir3.com/",
                    "text": "Couloir 3",
                    "position": 1,
                }
            ],
            "is_map": True,
            "map": [
                {
                    "name": "Map Studio",
                    "category": "Video production service",
                    "rating": 4.9,
                    "review_count": 27,
                    "website_url": "http://mapstudio.example/",
                    "position": 1,
                }
            ],
        }

    def analyze(self):
        return collector.analyze_record(
            "chatgpt",
            self.record,
            run_at="2026-07-22T00:00:00Z",
            target_domains=["brand.example"],
            brand_terms=["Target Brand"],
            competitor_domains=[],
        )

    def test_splits_actual_citations_from_candidates(self):
        result = self.analyze()
        self.assertEqual(len(result.actual_citations), 1)
        self.assertEqual(len(result.citation_candidates), 2)
        self.assertEqual(len(result.uncited_citation_candidates), 1)
        self.assertEqual(result.citations_count, 1)
        self.assertEqual(result.sources, result.actual_citations)

    def test_derives_canonical_domain_from_url(self):
        result = self.analyze()
        citation = result.citation_candidates[0]
        self.assertEqual(citation["domain"], "couloir3.com")
        self.assertEqual(citation["display_domain"], "Couloir3")

    def test_preserves_search_map_and_link_evidence(self):
        result = self.analyze()
        self.assertEqual(result.search_sources[0]["domain"], "search.example")
        self.assertEqual(result.map_results[0]["review_count"], 27)
        self.assertEqual(result.map_results[0]["domain"], "mapstudio.example")
        self.assertEqual(result.attached_links[0]["domain"], "couloir3.com")

    def test_cleans_provider_ui_boilerplate_and_extracts_answer_entity(self):
        result = self.analyze()
        self.assertTrue(result.answer_text_markdown.startswith("**Couloir 3**"))
        entity = next(
            item for item in result.competitor_entities if item["domain"] == "couloir3.com"
        )
        self.assertIn("answer", entity["channels"])
        self.assertIn("citation", entity["channels"])

    def test_target_signals_are_channel_specific(self):
        self.record["search_sources"].append(
            {"url": "https://brand.example/paris", "title": "Target Brand", "rank": 2}
        )
        result = self.analyze()
        self.assertTrue(result.target_found_in_search)
        self.assertFalse(result.target_found_in_maps)
        self.assertFalse(result.cited)
        self.assertEqual(result.mentions, 0)

    def test_missing_evidence_is_unknown_not_zero(self):
        self.record.pop("citations")
        self.record.pop("map")
        self.record.pop("search_sources")
        self.record.pop("web_search_triggered")
        result = self.analyze()

        self.assertEqual(result.actual_citations, [])
        self.assertEqual(result.map_results, [])
        self.assertIsNone(result.used_web_search)
        self.assertEqual(result.evidence_status["actual_citations"]["state"], "missing")
        self.assertEqual(result.evidence_status["maps"]["state"], "missing")
        self.assertEqual(result.evidence_status["search_sources"]["state"], "missing")
        self.assertEqual(result.evidence_status["web_search"]["state"], "missing")

    def test_missing_cited_flags_do_not_promote_candidates(self):
        for citation in self.record["citations"]:
            citation.pop("cited")
        result = self.analyze()

        self.assertEqual(result.actual_citations, [])
        self.assertEqual(len(result.citation_candidates), 2)
        self.assertEqual(result.evidence_status["actual_citations"]["state"], "missing")
        self.assertIn(
            "citation_flags_missing",
            [warning["code"] for warning in result.normalization["warnings"]],
        )

    def test_malformed_cited_flags_are_not_promoted(self):
        self.record["citations"][0]["cited"] = "perhaps"
        result = self.analyze()

        self.assertEqual(result.actual_citations, [])
        self.assertEqual(result.evidence_status["actual_citations"]["state"], "malformed")
        self.assertIn(
            "citation_flags_malformed",
            [warning["code"] for warning in result.normalization["warnings"]],
        )

    def test_safe_provider_variations_are_coerced_with_warnings(self):
        self.record["web_search_triggered"] = "true"
        self.record["citations"][0]["cited"] = "true"
        self.record["citations"][0]["position"] = "1"
        self.record["map"][0]["rating"] = "4.9"
        self.record["map"][0]["review_count"] = "27"
        result = self.analyze()

        self.assertTrue(result.used_web_search)
        self.assertEqual(result.actual_citations[0]["position"], 1)
        self.assertEqual(result.map_results[0]["rating"], 4.9)
        self.assertEqual(result.map_results[0]["review_count"], 27)
        self.assertEqual(result.evidence_status["web_search"]["state"], "inferred")
        self.assertGreater(len(result.normalization["warnings"]), 0)

    def test_malformed_arrays_warn_instead_of_crashing(self):
        self.record["map"] = "not-an-array"
        self.record["search_sources"] = {
            "url": "https://single.example",
            "title": "Singleton",
        }
        result = self.analyze()

        self.assertEqual(result.map_results, [])
        self.assertEqual(result.evidence_status["maps"]["state"], "malformed")
        self.assertEqual(len(result.search_sources), 1)
        self.assertEqual(result.evidence_status["search_sources"]["state"], "inferred")

    def test_unknown_fields_are_preserved_and_aggregated(self):
        self.record["future_brightdata_field"] = {"new": True}
        result = self.analyze()
        payload = collector.build_results_payload(
            run_at="2026-07-22T00:00:00Z",
            check_url="https://brand.example",
            target_domains=["brand.example"],
            brand_terms=["Target Brand"],
            snapshots=[],
            all_results=[result],
            rejected_records=[
                {"chatbot": "chatgpt", "index": 2, "reason": "broken fixture"}
            ],
        )

        self.assertEqual(
            result.provider_metadata["unknown_fields"]["future_brightdata_field"],
            {"new": True},
        )
        self.assertIn(
            "future_brightdata_field",
            payload["collection_diagnostics"]["unknown_provider_fields"],
        )
        self.assertEqual(payload["collection_diagnostics"]["records_rejected"], 1)
        self.assertEqual(payload["collection_diagnostics"]["status"], "partial")

    def test_empty_evidence_objects_are_malformed_not_supported_zeroes(self):
        self.record["citations"] = [{"cited": True}]
        self.record["map"] = [{}]
        self.record["search_sources"] = [{}]
        result = self.analyze()

        self.assertEqual(result.actual_citations, [])
        self.assertEqual(result.map_results, [])
        self.assertEqual(result.search_sources, [])
        self.assertEqual(result.evidence_status["actual_citations"]["state"], "malformed")
        self.assertEqual(result.evidence_status["citation_candidates"]["state"], "malformed")
        self.assertEqual(result.evidence_status["maps"]["state"], "malformed")
        self.assertEqual(result.evidence_status["search_sources"]["state"], "malformed")

    def test_metadata_boolean_strings_are_coerced_safely(self):
        self.record["is_map"] = "false"
        self.record["shopping_visible"] = "0"
        result = self.analyze()

        self.assertFalse(result.provider_metadata["is_map"])
        self.assertFalse(result.provider_metadata["shopping_visible"])

    def test_malformed_singleton_fan_out_is_not_counted(self):
        self.record["web_search_query"] = {"query": "video agency paris"}
        result = self.analyze()

        self.assertEqual(result.fan_out_count, 0)
        self.assertEqual(result.fan_out_queries, [])
        self.assertEqual(result.fan_out_details, [])
        self.assertEqual(result.evidence_status["fan_out_queries"]["state"], "malformed")


if __name__ == "__main__":
    unittest.main()
