import io
import json
import unittest
from unittest.mock import Mock

from jev import fixture_evaluator
from signals import open_state, process, send_ilp, validate_write_url


class SignalsTests(unittest.TestCase):
    def setUp(self):
        with open("examples/policy.json", encoding="utf-8") as source:
            self.policy = json.load(source)
        with open("examples/fixtures.json", encoding="utf-8") as source:
            self.fixtures = json.load(source)

    def test_materializes_distinct_templates_without_raw_text(self):
        published = []
        with open_state(":memory:") as db:
            with open("examples/templates.jsonl", encoding="utf-8") as source:
                count = process(source, db, self.policy,
                                fixture_evaluator(self.fixtures, self.policy), published.append)
        self.assertEqual(count, 2)
        self.assertEqual(len(published), 2)
        self.assertNotIn("payment", "".join(published))
        self.assertIn('outcome="incident"', published[0])

    def test_failed_delivery_does_not_mark_decision_complete(self):
        template = '{"template":"payment call failed after <*> retries"}\n'
        fail = Mock(side_effect=OSError("offline"))
        with open_state(":memory:") as db:
            with self.assertRaises(OSError):
                process(io.StringIO(template), db, self.policy,
                        fixture_evaluator(self.fixtures, self.policy), fail)
            output = []
            self.assertEqual(process(io.StringIO(template), db, self.policy,
                                     fixture_evaluator(self.fixtures, self.policy), output.append), 1)
            self.assertEqual(process(io.StringIO(template), db, self.policy,
                                     fixture_evaluator(self.fixtures, self.policy), output.append), 0)

    def test_write_url_restrictions(self):
        self.assertEqual(validate_write_url("http://127.0.0.1:9000/write"),
                         "http://127.0.0.1:9000/write")
        for url in ("http://example.org/write", "https://user:pass@example.org/write",
                    "https://example.org/exec"):
            with self.assertRaises(ValueError):
                validate_write_url(url)

    def test_http_write_uses_questdb_ilp_endpoint(self):
        requests = []
        def open_response(request, timeout):
            requests.append(request)
            return io.BytesIO(b"")
        send_ilp("http://127.0.0.1:9000/write", "jev_signals x=1\n", opener=open_response)
        self.assertEqual(requests[0].full_url, "http://127.0.0.1:9000/write")
        self.assertEqual(requests[0].get_method(), "POST")
        self.assertEqual(requests[0].data, b"jev_signals x=1\n")


if __name__ == "__main__":
    unittest.main()
