import os
import tempfile
import unittest

from steam_local_config import resolve_steam_config


class SteamLocalConfigTests(unittest.TestCase):
    def setUp(self):
        self.original_env = os.environ.copy()
        for key in (
            "STEAM_API_KEY",
            "STEAM_ID",
            "STEAM_SESSION_ID",
            "STEAM_COOKIES",
            "ADD_DELAY_SECONDS",
            "FRIEND_CODES_FILE",
            "EXCLUDE_FILE",
            "STEAM_CONFIG_PATH",
        ):
            os.environ.pop(key, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_env_config_injects_sessionid_into_cookies(self):
        os.environ["STEAM_API_KEY"] = "A" * 32
        os.environ["STEAM_ID"] = "76561198012345678"
        os.environ["STEAM_SESSION_ID"] = "session123"
        os.environ["STEAM_COOKIES"] = "steamLoginSecure=secure-cookie"

        config, errors = resolve_steam_config()

        self.assertEqual([], errors)
        self.assertIn("steamLoginSecure=secure-cookie", config.cookies)
        self.assertIn("sessionid=session123", config.cookies)

    def test_json_config_is_loaded_from_local_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "steam_friend_bot.local.json")
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(
                    '{"api_key":"%s","steam_id":"76561198012345678",'
                    '"session_id":"abc","cookies":"steamLoginSecure=secure"}'
                    % ("B" * 32)
                )
            os.environ["STEAM_CONFIG_PATH"] = config_path

            config, errors = resolve_steam_config()

            self.assertEqual([], errors)
            self.assertEqual(config_path, config.config_path)
            self.assertTrue(config.config_file_found)
            self.assertEqual("76561198012345678", config.steam_id)
            self.assertIn("sessionid=abc", config.cookies)

    def test_invalid_fields_are_reported_clearly(self):
        os.environ["STEAM_API_KEY"] = "invalid"
        os.environ["STEAM_ID"] = "123"
        os.environ["STEAM_SESSION_ID"] = "abc"
        os.environ["STEAM_COOKIES"] = "foo=bar"

        _, errors = resolve_steam_config()

        self.assertIn("Steam API Key 格式无效，应为 32 位十六进制字符串", errors)
        self.assertIn("SteamID64 格式无效，应为 17 位且以 7656 开头", errors)
        self.assertIn("Cookies 缺少 steamLoginSecure，无法复用本地登录态", errors)


if __name__ == "__main__":
    unittest.main()
