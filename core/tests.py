from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase


class _FakeQuery:
	def __init__(self, data):
		self._data = data

	def select(self, *_args, **_kwargs):
		return self

	def eq(self, *_args, **_kwargs):
		return self

	def order(self, *_args, **_kwargs):
		return self

	def limit(self, *_args, **_kwargs):
		return self

	def execute(self):
		return {"data": self._data}


class _FakeClient:
	def __init__(self, sign_in_result=None, sign_in_exception=None, subscription_data=None):
		self._sign_in_result = sign_in_result
		self._sign_in_exception = sign_in_exception
		self._subscription_data = subscription_data
		self.auth = SimpleNamespace(sign_in_with_password=self.sign_in_with_password)

	def sign_in_with_password(self, _payload):
		if self._sign_in_exception:
			raise self._sign_in_exception
		return self._sign_in_result

	def table(self, _name):
		return _FakeQuery(self._subscription_data)


class DesktopLoginViewTests(TestCase):
	endpoint = "/api/desktop-login/"

	def test_missing_credentials_returns_400(self):
		response = self.client.post(
			self.endpoint,
			data={"email": ""},
			content_type="application/json",
		)
		self.assertEqual(response.status_code, 400)

	@patch("core.views._get_supabase_auth_client")
	def test_invalid_credentials_returns_401(self, mock_auth_client):
		mock_auth_client.return_value = _FakeClient(
			sign_in_exception=Exception("Invalid login credentials")
		)

		response = self.client.post(
			self.endpoint,
			data={"email": "user@example.com", "password": "wrong"},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 401)
		self.assertEqual(response.json()["status"], "unauthorized")

	@patch("core.views._get_supabase_admin_client")
	@patch("core.views._get_supabase_auth_client")
	def test_valid_login_with_active_subscription_returns_200_active(self, mock_auth_client, mock_admin_client):
		mock_auth_client.return_value = _FakeClient(
			sign_in_result={"user": {"email": "User@Example.com"}},
		)
		mock_admin_client.return_value = _FakeClient(
			sign_in_result={"user": {"email": "User@Example.com"}},
			subscription_data=[
				{
					"status": "active",
					"renews_at": "2026-06-01T00:00:00Z",
					"ends_at": "2026-06-30T00:00:00Z",
				}
			],
		)

		response = self.client.post(
			self.endpoint,
			data={"email": "user@example.com", "password": "correct"},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 200)
		body = response.json()
		self.assertEqual(body["status"], "active")
		self.assertEqual(body["email"], "user@example.com")
		self.assertEqual(body["offline_valid_days"], 30)

	@patch("core.views._get_supabase_admin_client")
	@patch("core.views._get_supabase_auth_client")
	def test_valid_login_without_subscription_returns_200_inactive(self, mock_auth_client, mock_admin_client):
		mock_auth_client.return_value = _FakeClient(
			sign_in_result={"user": {"email": "user@example.com"}},
		)
		mock_admin_client.return_value = _FakeClient(
			sign_in_result={"user": {"email": "user@example.com"}},
			subscription_data=[],
		)

		response = self.client.post(
			self.endpoint,
			data={"email": "user@example.com", "password": "correct"},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 200)
		body = response.json()
		self.assertEqual(body["status"], "inactive")
		self.assertEqual(body["email"], "user@example.com")
