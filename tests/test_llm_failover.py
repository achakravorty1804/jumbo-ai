"""Confirms complete() falls back to the backup provider only after the primary
is fully exhausted, and that a backup failure surfaces both errors clearly.
Fully mocked -- no real network calls, no tokens spent, no API keys needed."""
import unittest
from unittest.mock import Mock, patch

from agent import llm


def make_response(status_code, json_data=None, text=""):
    resp = Mock()
    resp.status_code = status_code
    resp.text = text
    resp.headers = {}
    if json_data is not None:
        resp.json.return_value = json_data
    return resp


SUCCESS_JSON = {
    "choices": [{"message": {"content": "ok"}}],
    "usage": {"total_tokens": 10, "prompt_tokens": 5, "completion_tokens": 5},
}


class LLMFailoverTests(unittest.TestCase):
    def setUp(self):
        # Give the module a backup config for the duration of each test,
        # regardless of what's actually in .env.
        self.patchers = [
            patch.object(llm, "BACKUP_BASE_URL", "https://backup.example.com/v1"),
            patch.object(llm, "BACKUP_MODEL", "backup-model"),
            patch.object(llm, "BACKUP_API_KEY", "fake-backup-key"),
            patch.object(llm, "API_KEY", "fake-primary-key"),
        ]
        for p in self.patchers:
            p.start()
            self.addCleanup(p.stop)

    def test_primary_success_never_touches_backup(self):
        with patch("requests.post", return_value=make_response(200, SUCCESS_JSON)) as mock_post:
            result = llm.complete([{"role": "user", "content": "hi"}], max_retries=0)
        self.assertEqual(result, "ok")
        mock_post.assert_called_once()  # only the primary was called

    def test_falls_back_to_backup_when_primary_exhausted(self):
        primary_fail = make_response(500, text="server error")
        backup_ok = make_response(200, SUCCESS_JSON)
        with patch("requests.post", side_effect=[primary_fail, backup_ok]):
            result = llm.complete([{"role": "user", "content": "hi"}], max_retries=0)
        self.assertEqual(result, "ok")

    def test_both_providers_failing_raises_combined_error(self):
        primary_fail = make_response(500, text="primary down")
        backup_fail = make_response(500, text="backup down")
        with patch("requests.post", side_effect=[primary_fail, backup_fail]):
            with self.assertRaises(llm.LLMError) as ctx:
                llm.complete([{"role": "user", "content": "hi"}], max_retries=0)
        self.assertIn("backup also failed", str(ctx.exception))

    def test_no_backup_configured_raises_primary_error_only(self):
        with patch.object(llm, "BACKUP_BASE_URL", ""), \
             patch.object(llm, "BACKUP_MODEL", ""), \
             patch.object(llm, "BACKUP_API_KEY", ""):
            primary_fail = make_response(500, text="primary down")
            with patch("requests.post", return_value=primary_fail):
                with self.assertRaises(llm.LLMError) as ctx:
                    llm.complete([{"role": "user", "content": "hi"}], max_retries=0)
            self.assertNotIn("backup", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()