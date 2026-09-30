import os
import tempfile
import unittest
from unittest.mock import Mock

from mpesa_kit.client import MpesaClient
from mpesa_kit.storage import EventStore


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = str(data)

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError("failed")


class ClientTests(unittest.TestCase):
    def client(self):
        session = Mock()
        session.get.return_value = FakeResponse({"access_token": "abc", "expires_in": 3600})
        session.post.return_value = FakeResponse({"ResponseCode": "0"})
        return MpesaClient(consumer_key="key", consumer_secret="secret", shortcode="174379", passkey="pass", callback_url="https://example.com/mpesa/stk/callback", initiator_name="testapi", security_credential="encrypted", session=session)

    def test_normalize_phone(self):
        self.assertEqual(MpesaClient.normalize_phone("0712 345 678"), "254712345678")
        self.assertEqual(MpesaClient.normalize_phone("+254712345678"), "254712345678")

    def test_stk_uses_normalized_phone(self):
        client = self.client()
        result = client.stk_push("0712345678", 100, "ORDER123")
        self.assertEqual(result["ResponseCode"], "0")
        payload = client.session.post.call_args.kwargs["json"]
        self.assertEqual(payload["PartyA"], "254712345678")
        self.assertEqual(payload["PhoneNumber"], "254712345678")

    def test_b2c_uses_v3_endpoint(self):
        client = self.client()
        client.b2c("0712345678", 100, "Test")
        url = client.session.post.call_args.args[0]
        self.assertTrue(url.endswith("/mpesa/b2c/v3/paymentrequest"))

    def test_token_is_cached(self):
        client = self.client()
        self.assertEqual(client.get_access_token(), "abc")
        self.assertEqual(client.get_access_token(), "abc")
        self.assertEqual(client.session.get.call_count, 1)

    def test_event_store_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EventStore(os.path.join(tmp, "events.db"))
            event_id = store.add("stk", {"ok": True}, "checkout-1")
            events = store.list()
            self.assertEqual(events[0]["id"], event_id)
            self.assertEqual(events[0]["event_key"], "checkout-1")
            self.assertEqual(events[0]["payload"], {"ok": True})


if __name__ == "__main__":
    unittest.main()
