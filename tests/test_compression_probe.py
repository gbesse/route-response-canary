import gzip
import json
import unittest

from compression_probe import demo, encode


class CompressionProbeTests(unittest.TestCase):
    def test_identity_and_gzip_are_same_payload(self):
        payload = {"model": "demo", "input": "synthetic", "stream": True}
        self.assertEqual(json.loads(encode(payload, "identity")), payload)
        self.assertEqual(json.loads(gzip.decompress(encode(payload, "gzip"))), payload)

    def test_zstd_is_same_payload(self):
        import zstandard
        payload = {"model": "demo", "input": "synthetic", "stream": True}
        self.assertEqual(json.loads(zstandard.ZstdDecompressor().decompress(encode(payload, "zstd"))), payload)

    def test_local_demo_distinguishes_transport_and_completion(self):
        report = demo()
        self.assertEqual([row["http_status"] for row in report["results"]], [200, 400, 400])
        self.assertEqual([row["usable_response"] for row in report["results"]], [True, False, False])
        self.assertIsNone(report["backend_fallback_observed"])


if __name__ == "__main__":
    unittest.main()
