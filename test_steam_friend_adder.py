"""
Unit tests for steam_friend_adder.py

All tests mock HTTP interactions so no real Steam network calls are made.
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, call, patch

# ---------------------------------------------------------------------------
# Ensure the module under test is importable from this directory
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

from steam_friend_adder import SteamFriendAdder  # noqa: E402


def _make_adder() -> SteamFriendAdder:
    """Return a SteamFriendAdder instance with logging suppressed."""
    adder = SteamFriendAdder(api_key="FAKE_KEY", steam_id="76561198000000001")
    # Suppress log output during tests
    adder.logger.handlers = []
    return adder


# ---------------------------------------------------------------------------
# Helper: build a minimal mock response
# ---------------------------------------------------------------------------

def _mock_response(status_code: int = 200, json_data: dict = None, text: str = ""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("no JSON")
    resp.raise_for_status = MagicMock()
    return resp


# ===========================================================================
# _steam_web_login tests
# ===========================================================================

class TestSteamWebLogin(unittest.TestCase):
    """Tests for _steam_web_login()."""

    # --- happy path: plain login (no Steam Guard) ---------------------------

    @patch("steam_friend_adder.requests.Session")
    def test_login_success_no_guard(self, MockSession):
        adder = _make_adder()
        session_instance = MagicMock()
        MockSession.return_value = session_instance

        rsa_resp = _mock_response(200, {
            "success": True,
            "publickey_mod": hex(65537)[2:],   # trivially small for test
            "publickey_exp": "10001",           # 65537 in hex
            "timestamp": "12345",
        })

        login_resp = _mock_response(200, {
            "success": True,
            "login_complete": True,
            "transfer_parameters": {"auth": "FAKE_AUTH_TOKEN"},
        })

        session_instance.post.side_effect = [rsa_resp, login_resp]

        import rsa as _rsa
        encoded_mock = MagicMock()
        encoded_mock.decode.return_value = "ENCODED"

        # Patch rsa.encrypt so we don't need real RSA key sizes
        with patch("steam_friend_adder.base64") as mock_b64, \
             patch.object(sys.modules.get("rsa", _rsa), "encrypt", return_value=b"ENCRYPTED"), \
             patch.object(sys.modules.get("rsa", _rsa), "PublicKey", return_value=MagicMock()):
            mock_b64.b64encode.return_value = encoded_mock

            ok, err = adder._steam_web_login("user", "pass")

        self.assertTrue(ok, err)
        self.assertEqual(err, "")
        self.assertIsNotNone(adder._web_session)

    # --- RSA key fetch failure -----------------------------------------------

    @patch("steam_friend_adder.requests.Session")
    def test_login_rsa_failure(self, MockSession):
        adder = _make_adder()
        session_instance = MagicMock()
        MockSession.return_value = session_instance

        rsa_resp = _mock_response(200, {"success": False})
        session_instance.post.return_value = rsa_resp

        ok, err = adder._steam_web_login("user", "pass")

        self.assertFalse(ok)
        self.assertIn("RSA key", err)

    # --- Steam Guard email required ------------------------------------------

    @patch("steam_friend_adder.requests.Session")
    def test_login_email_guard(self, MockSession):
        adder = _make_adder()
        session_instance = MagicMock()
        MockSession.return_value = session_instance

        rsa_resp = _mock_response(200, {
            "success": True,
            "publickey_mod": hex(65537)[2:],
            "publickey_exp": "10001",
            "timestamp": "12345",
        })
        guard_needed_resp = _mock_response(200, {
            "success": False,
            "emailauth_needed": True,
            "emailsteamid": "76561198000000001",
        })
        login_ok_resp = _mock_response(200, {
            "success": True,
            "login_complete": True,
            "transfer_parameters": {"auth": "TOKEN2"},
        })

        session_instance.post.side_effect = [rsa_resp, guard_needed_resp, login_ok_resp]

        import rsa as _rsa
        guard_callback = MagicMock(return_value="AB123")
        encoded_mock = MagicMock()
        encoded_mock.decode.return_value = "ENC"

        with patch.object(sys.modules.get("rsa", _rsa), "encrypt", return_value=b"ENC"), \
             patch.object(sys.modules.get("rsa", _rsa), "PublicKey", return_value=MagicMock()), \
             patch("steam_friend_adder.base64") as mock_b64:
            mock_b64.b64encode.return_value = encoded_mock

            ok, err = adder._steam_web_login("user", "pass", guard_callback=guard_callback)

        guard_callback.assert_called_once()
        self.assertTrue(ok, err)

    # --- Steam Guard mobile (2FA) required ------------------------------------

    @patch("steam_friend_adder.requests.Session")
    def test_login_twofactor_guard(self, MockSession):
        adder = _make_adder()
        session_instance = MagicMock()
        MockSession.return_value = session_instance

        rsa_resp = _mock_response(200, {
            "success": True,
            "publickey_mod": hex(65537)[2:],
            "publickey_exp": "10001",
            "timestamp": "99",
        })
        guard_needed_resp = _mock_response(200, {
            "success": False,
            "requires_twofactor": True,
        })
        login_ok_resp = _mock_response(200, {
            "success": True,
            "login_complete": True,
            "transfer_parameters": {},
        })

        session_instance.post.side_effect = [rsa_resp, guard_needed_resp, login_ok_resp]

        import rsa as _rsa
        guard_callback = MagicMock(return_value="XY99Z")
        encoded_mock = MagicMock()
        encoded_mock.decode.return_value = "E"

        with patch.object(sys.modules.get("rsa", _rsa), "encrypt", return_value=b"E"), \
             patch.object(sys.modules.get("rsa", _rsa), "PublicKey", return_value=MagicMock()), \
             patch("steam_friend_adder.base64") as mock_b64:
            mock_b64.b64encode.return_value = encoded_mock

            ok, err = adder._steam_web_login("user", "pass", guard_callback=guard_callback)

        guard_callback.assert_called_once()
        self.assertTrue(ok, err)

    # --- login rejected (wrong password) -------------------------------------

    @patch("steam_friend_adder.requests.Session")
    def test_login_wrong_password(self, MockSession):
        adder = _make_adder()
        session_instance = MagicMock()
        MockSession.return_value = session_instance

        rsa_resp = _mock_response(200, {
            "success": True,
            "publickey_mod": hex(65537)[2:],
            "publickey_exp": "10001",
            "timestamp": "0",
        })
        failed_resp = _mock_response(200, {
            "success": False,
            "login_complete": False,
            "message": "Incorrect login.",
        })

        session_instance.post.side_effect = [rsa_resp, failed_resp]

        import rsa as _rsa
        encoded_mock = MagicMock()
        encoded_mock.decode.return_value = "E"

        with patch.object(sys.modules.get("rsa", _rsa), "encrypt", return_value=b"E"), \
             patch.object(sys.modules.get("rsa", _rsa), "PublicKey", return_value=MagicMock()), \
             patch("steam_friend_adder.base64") as mock_b64:
            mock_b64.b64encode.return_value = encoded_mock

            ok, err = adder._steam_web_login("user", "wrong")

        self.assertFalse(ok)
        self.assertIn("Incorrect login", err)

    # --- rsa import missing --------------------------------------------------

    def test_login_missing_rsa_import(self):
        adder = _make_adder()
        with patch.dict(sys.modules, {"rsa": None}):
            ok, err = adder._steam_web_login("u", "p")
        self.assertFalse(ok)
        self.assertIn("rsa", err.lower())


# ===========================================================================
# _get_chat_members_via_web_session tests
# ===========================================================================

class TestGetChatMembersViaWebSession(unittest.TestCase):
    """Tests for _get_chat_members_via_web_session()."""

    def test_not_authenticated(self):
        adder = _make_adder()
        adder._web_session = None
        ok, members, err = adder._get_chat_members_via_web_session("123456")
        self.assertFalse(ok)
        self.assertEqual(members, [])
        self.assertIn("Not authenticated", err)

    def test_summary_returns_top_members(self):
        adder = _make_adder()
        adder._web_session = MagicMock()
        adder._web_access_token = "TOKEN"

        summary_resp = _mock_response(200, {
            "response": {
                "summary": {
                    "top_members": ["76561198000000002", "76561198000000003"],
                }
            }
        })
        # GetChatRoomGroupMembers returns 200 with empty members
        members_resp = _mock_response(200, {"response": {"members": []}})

        adder._web_session.get.side_effect = [summary_resp, members_resp]

        ok, members, err = adder._get_chat_members_via_web_session("999")

        self.assertTrue(ok, err)
        self.assertIn("76561198000000002", members)
        self.assertIn("76561198000000003", members)

    def test_members_endpoint_supplements_top_members(self):
        adder = _make_adder()
        adder._web_session = MagicMock()

        summary_resp = _mock_response(200, {
            "response": {
                "summary": {
                    "top_members": ["76561198000000002"],
                }
            }
        })
        members_resp = _mock_response(200, {
            "response": {
                "members": [
                    {"ulfriendid": "76561198000000002"},
                    {"ulfriendid": "76561198000000099"},
                ]
            }
        })

        adder._web_session.get.side_effect = [summary_resp, members_resp]

        ok, members, err = adder._get_chat_members_via_web_session("888")

        self.assertTrue(ok, err)
        self.assertIn("76561198000000002", members)
        self.assertIn("76561198000000099", members)
        # No duplicates
        self.assertEqual(len(members), len(set(members)))

    def test_auth_rejected_401(self):
        adder = _make_adder()
        adder._web_session = MagicMock()

        adder._web_session.get.return_value = _mock_response(401)

        ok, members, err = adder._get_chat_members_via_web_session("777")
        self.assertFalse(ok)
        self.assertIn("401", err)

    def test_access_denied_403(self):
        adder = _make_adder()
        adder._web_session = MagicMock()

        adder._web_session.get.return_value = _mock_response(403)

        ok, members, err = adder._get_chat_members_via_web_session("555")
        self.assertFalse(ok)
        self.assertIn("403", err)

    def test_no_members_returned(self):
        adder = _make_adder()
        adder._web_session = MagicMock()

        summary_resp = _mock_response(200, {
            "response": {"summary": {"top_members": []}}
        })
        members_resp = _mock_response(200, {"response": {"members": []}})

        adder._web_session.get.side_effect = [summary_resp, members_resp]

        ok, members, err = adder._get_chat_members_via_web_session("111")
        self.assertFalse(ok)
        self.assertEqual(members, [])

    def test_members_endpoint_exception_is_ignored(self):
        """GetChatRoomGroupMembers failure should not prevent returning top_members."""
        adder = _make_adder()
        adder._web_session = MagicMock()

        summary_resp = _mock_response(200, {
            "response": {
                "summary": {"top_members": ["76561198000000010"]}
            }
        })

        import requests as req

        adder._web_session.get.side_effect = [
            summary_resp,
            req.exceptions.RequestException("endpoint unavailable"),
        ]

        ok, members, err = adder._get_chat_members_via_web_session("222")
        self.assertTrue(ok, err)
        self.assertIn("76561198000000010", members)


# ===========================================================================
# get_chat_members integration: authenticated flow
# ===========================================================================

class TestGetChatMembersAuthFlow(unittest.TestCase):
    """Tests for get_chat_members() when STEAM_USERNAME/PASSWORD are set."""

    def _patch_env(self, username="testuser", password="testpass"):
        return patch.dict(os.environ, {"STEAM_USERNAME": username, "STEAM_PASSWORD": password})

    def test_uses_auth_flow_when_credentials_set(self):
        adder = _make_adder()

        # Invite info returns private group (no clan_steamid)
        adder.get_chat_invite_info = MagicMock(return_value=(
            True,
            {"group_name": "TestGroup", "chat_group_id": "424242", "active_member_count": 5},
            "",
        ))

        # Login succeeds
        adder._steam_web_login = MagicMock(return_value=(True, ""))
        adder._get_chat_members_via_web_session = MagicMock(
            return_value=(True, ["76561198000000002", "76561198000000003"], "")
        )

        with self._patch_env():
            ok, members, err = adder.get_chat_members("ZiMUFTC2")

        adder._steam_web_login.assert_called_once_with("testuser", "testpass")
        adder._get_chat_members_via_web_session.assert_called_once_with("424242")
        self.assertTrue(ok)
        self.assertEqual(len(members), 2)

    def test_no_auth_attempted_when_no_credentials(self):
        adder = _make_adder()

        adder.get_chat_invite_info = MagicMock(return_value=(
            True,
            {"group_name": "PrivateGroup", "chat_group_id": "424242"},
            "",
        ))
        adder._steam_web_login = MagicMock()

        with patch.dict(os.environ, {"STEAM_USERNAME": "", "STEAM_PASSWORD": ""}):
            ok, members, err = adder.get_chat_members("ZiMUFTC2")

        adder._steam_web_login.assert_not_called()
        self.assertFalse(ok)
        self.assertIn("STEAM_USERNAME", err)

    def test_login_failure_propagates(self):
        adder = _make_adder()

        adder.get_chat_invite_info = MagicMock(return_value=(
            True,
            {"group_name": "G", "chat_group_id": "1"},
            "",
        ))
        adder._steam_web_login = MagicMock(
            return_value=(False, "Steam login failed: Incorrect login.")
        )

        with self._patch_env():
            ok, members, err = adder.get_chat_members("code")

        self.assertFalse(ok)
        self.assertIn("authentication failed", err)

    def test_reuses_existing_session(self):
        """If _web_session is already set, _steam_web_login should not be called again."""
        adder = _make_adder()
        adder._web_session = MagicMock()  # already authenticated

        adder.get_chat_invite_info = MagicMock(return_value=(
            True,
            {"group_name": "G", "chat_group_id": "5000"},
            "",
        ))
        adder._steam_web_login = MagicMock()
        adder._get_chat_members_via_web_session = MagicMock(
            return_value=(True, ["76561198000000007"], "")
        )

        with self._patch_env():
            ok, members, err = adder.get_chat_members("code")

        adder._steam_web_login.assert_not_called()
        self.assertTrue(ok)

    def test_missing_chat_group_id(self):
        adder = _make_adder()

        # group_id missing or empty
        adder.get_chat_invite_info = MagicMock(return_value=(
            True,
            {"group_name": "NoID", "chat_group_id": ""},
            "",
        ))

        with self._patch_env():
            ok, members, err = adder.get_chat_members("code")

        self.assertFalse(ok)
        self.assertIn("no group ID", err)


# ===========================================================================
# Existing behaviour: linked Community Group still uses XML API
# ===========================================================================

class TestGetChatMembersClanFallback(unittest.TestCase):
    def test_linked_clan_uses_xml_api(self):
        adder = _make_adder()

        adder.get_chat_invite_info = MagicMock(return_value=(
            True,
            {"group_name": "ClanGroup", "chat_group_id": "7", "clan_steamid": "103582791429521408"},
            "",
        ))
        adder.get_group_members = MagicMock(
            return_value=(True, ["76561198000000005"], "")
        )

        ok, members, err = adder.get_chat_members("somecode")

        adder.get_group_members.assert_called_once_with("103582791429521408")
        self.assertTrue(ok)
        self.assertIn("76561198000000005", members)


if __name__ == "__main__":
    unittest.main()
