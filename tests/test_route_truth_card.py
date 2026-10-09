import unittest

from route_truth_card import inspect


class TruthCardTests(unittest.TestCase):
    def setUp(self):
        self.test = {"model": "a", "protocol": "responses", "config_revision": "1", "config_state": "saved", "outcome": "usable", "tested_at": "2026-10-09T10:00:00Z"}
        self.route = {"model": "a", "protocol": "responses", "config_revision": "1", "served_at": "2026-10-09T10:01:00Z"}

    def test_match_and_mismatch(self):
        self.assertEqual(inspect(self.test, self.route)["status"], "match")
        self.assertEqual(inspect(self.test, {**self.route, "model": "b"})["different_fields"], ["model"])

    def test_draft_and_stale(self):
        self.assertEqual(inspect({**self.test, "config_state": "draft"}, self.route)["status"], "inconclusive")
        self.assertEqual(inspect(self.test, self.route, 30)["status"], "stale")


if __name__ == "__main__":
    unittest.main()
