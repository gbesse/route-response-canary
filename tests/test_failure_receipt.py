import contextlib
import io
import json
import unittest
from pathlib import Path

from failure_receipt import analyze, events, main, output_usable, read_pair

BASE = Path(__file__).parents[1] / "examples" / "failure-receipt"


class FailureReceiptTests(unittest.TestCase):
    def test_false_success_with_nonstandard_upstream_error(self):
        report = analyze(read_pair(BASE / "false-success.json"))
        self.assertEqual(report["verdict"], "false_success")
        self.assertTrue(report["empty_completion"])

    def test_error_object_and_http_failure_stay_failures(self):
        pair = read_pair(BASE / "preserved.json")
        self.assertEqual(analyze(pair)["verdict"], "preserved")
        pair["upstream"] = {
            "status": 503,
            "content_type": "application/json",
            "body": "{}",
        }
        pair["downstream"] = {
            "status": 502,
            "content_type": "application/json",
            "body": "{}",
        }
        self.assertEqual(analyze(pair)["verdict"], "preserved")

    def test_healthy_control_and_function_or_refusal_output(self):
        self.assertEqual(
            analyze(read_pair(BASE / "healthy.json"))["verdict"], "healthy"
        )
        self.assertTrue(
            output_usable(
                [{"type": "function_call", "name": "lookup", "arguments": "{}"}]
            )
        )
        self.assertTrue(
            output_usable(
                [
                    {
                        "type": "message",
                        "content": [{"type": "refusal", "refusal": "declined"}],
                    }
                ]
            )
        )
        self.assertFalse(output_usable([{"type": "reasoning", "summary": []}]))
        self.assertFalse(
            output_usable(
                [{"type": "message", "content": [{"type": "output_text", "text": " "}]}]
            )
        )

    def test_sse_multiline_data_crlf_comments_and_no_space(self):
        rows = events(
            '\ufeff:comment\r\nevent:error\r\ndata:{"type":\r\ndata:"error"}\r\n\r\n'
        )
        self.assertEqual(rows[0]["event"], "error")
        self.assertEqual(rows[0]["payload"], {"type": "error"})

    def test_unicode_line_separator_inside_json_is_not_sse_newline(self):
        rows = events('data:{"type":"delta","text":"one\u2028two"}\n\n')
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["valid"])

    def test_undispatched_or_malformed_terminal_cannot_pass(self):
        pair = read_pair(BASE / "healthy.json")
        pair["downstream"]["body"] = pair["downstream"]["body"].rstrip() + "\n"
        self.assertEqual(analyze(pair)["verdict"], "inconclusive")
        pair = read_pair(BASE / "healthy.json")
        pair["downstream"]["body"] += "data:broken\n\n"
        self.assertEqual(analyze(pair)["verdict"], "inconclusive")
        pair["downstream"]["body"] = "data:[]\n\n"
        self.assertEqual(analyze(pair)["verdict"], "inconclusive")

    def test_false_success_even_when_output_is_nonempty(self):
        pair = read_pair(BASE / "false-success.json")
        pair["downstream"] = read_pair(BASE / "healthy.json")["downstream"]
        self.assertEqual(analyze(pair)["verdict"], "false_success")

    def test_terminal_type_alone_is_not_a_usable_answer(self):
        pair = read_pair(BASE / "healthy.json")
        pair["downstream"]["body"] = 'data:{"type":"response.completed"}\n\n'
        report = analyze(pair)
        self.assertTrue(report["empty_completion"])
        self.assertEqual(report["verdict"], "inconclusive")

    def test_no_capture_contents_in_reports(self):
        pair = read_pair(BASE / "healthy.json")
        pair["downstream"]["body"] = pair["downstream"]["body"].replace(
            "synthetic answer", "PRIVATE_SENTINEL"
        )
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(analyze(pair)))

    def test_localized_cli_demo_and_exit_codes(self):
        for lang in ("fr", "en", "es"):
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(main(["demo", "--lang", lang]), 0)
                self.assertEqual(
                    main(["check", str(BASE / "false-success.json"), "--lang", lang]), 2
                )
                self.assertEqual(
                    main(["check", str(BASE / "preserved.json"), "--lang", lang]), 0
                )
                self.assertEqual(main(["check", "--lang", lang]), 1)


if __name__ == "__main__":
    unittest.main()
