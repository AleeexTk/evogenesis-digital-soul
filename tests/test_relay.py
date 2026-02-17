import unittest

from packages.integration.bridge_config import BridgeConfig
from packages.integration.relay import RelayClient


class RelayClientTests(unittest.TestCase):
    def test_auth_header_present_when_token_set(self):
        client = RelayClient(BridgeConfig(auth_token="abc"))
        headers = client._headers()
        self.assertEqual(headers["Authorization"], "Bearer abc")

    def test_relay_payload_shape(self):
        client = RelayClient(BridgeConfig())
        sent = {}

        def fake_send(event_type, payload):
            sent["event_type"] = event_type
            sent["payload"] = payload
            return {"ok": True}

        client.send_event_to_evopyramid = fake_send  # type: ignore[assignment]
        out = client.relay_task_update("t1", "complete", "omega", "done")

        self.assertEqual(out, {"ok": True})
        self.assertEqual(sent["event_type"], "task.state.updated")
        self.assertEqual(sent["payload"]["task_id"], "t1")
        self.assertEqual(sent["payload"]["status"], "complete")
        self.assertEqual(sent["payload"]["agent"], "omega")


if __name__ == "__main__":
    unittest.main()
