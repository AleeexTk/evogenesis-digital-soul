import os
import unittest
from unittest import mock

from packages.integration.bridge_config import BridgeConfig


class BridgeConfigTests(unittest.TestCase):
    def test_from_env(self):
        env = {
            "DIGITAL_SOUL_API_BASE": "http://localhost:9000",
            "EVOGENESIS_API_BASE": "https://evogenesis.local",
            "EVOPYRAMID_API_BASE": "http://localhost:5173",
            "EVO_BRIDGE_AUTH_TOKEN": "secret",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = BridgeConfig.from_env()
        self.assertEqual(cfg.digital_soul_api_base, env["DIGITAL_SOUL_API_BASE"])
        self.assertEqual(cfg.evogenesis_api_base, env["EVOGENESIS_API_BASE"])
        self.assertEqual(cfg.evopyramid_api_base, env["EVOPYRAMID_API_BASE"])
        self.assertEqual(cfg.auth_token, env["EVO_BRIDGE_AUTH_TOKEN"])

    def test_validate_rejects_invalid_url(self):
        cfg = BridgeConfig(evogenesis_api_base="ftp://bad")
        with self.assertRaises(ValueError):
            cfg.validate()


if __name__ == "__main__":
    unittest.main()
