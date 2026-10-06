import unittest

from canary import inspect, inspect_attempts


class CanaryTests(unittest.TestCase):
    def test_html_200_is_not_model_success(self):
        self.assertEqual(inspect(200, "text/html", "<html/>")["reason"], "wrong_content_type")

    def test_stream_without_completion_is_not_success(self):
        body = 'data: {"type":"response.created"}\n\n'
        self.assertEqual(inspect(200, "text/event-stream", body)["reason"], "missing_completion")

    def test_second_valid_attempt_proves_observed_fallback(self):
        attempts = [{"status": 200, "content_type": "text/html", "body": "error"},
                    {"status": 200, "content_type": "text/event-stream",
                     "body": 'data: {"type":"response.completed"}\n\n'}]
        self.assertTrue(inspect_attempts(attempts)["fallback_observed"])


if __name__ == "__main__":
    unittest.main()
