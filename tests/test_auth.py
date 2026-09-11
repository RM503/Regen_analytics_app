"""Regression checks for Supabase login responses and validation."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from supabase_auth.errors import AuthApiError

from src.auth.supabase_auth import supabase_auth


class AuthenticationTests(unittest.TestCase):
    def test_valid_login_returns_session(self):
        client = Mock()
        response = SimpleNamespace(
            user=SimpleNamespace(email="farmer@example.com"),
            session=SimpleNamespace(access_token="test-token"),
        )
        client.auth.sign_in_with_password.return_value = response
        self.assertIs(supabase_auth("farmer@example.com", "test-password", client), response)

    def test_rejected_credentials_return_no_session(self):
        client = Mock()
        client.auth.sign_in_with_password.side_effect = AuthApiError(
            "Invalid login credentials", 400, "invalid_credentials"
        )
        self.assertIsNone(supabase_auth("farmer@example.com", "wrong-password", client))

    def test_invalid_form_never_calls_supabase_or_logs_password(self):
        client = Mock()
        password = "private-test-password"
        with self.assertLogs("src.auth.supabase_auth", level="WARNING") as logs:
            self.assertIsNone(supabase_auth("not-an-email", password, client))
        client.auth.sign_in_with_password.assert_not_called()
        self.assertNotIn(password, "\n".join(logs.output))

    def test_empty_password_never_calls_supabase(self):
        client = Mock()
        self.assertIsNone(supabase_auth("farmer@example.com", " ", client))
        client.auth.sign_in_with_password.assert_not_called()


if __name__ == "__main__":
    unittest.main()
