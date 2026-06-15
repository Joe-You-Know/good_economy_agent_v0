import unittest

from agent.payment_gateway import PaymentGateway


class PaymentGatewayTests(unittest.TestCase):
    def test_valid_donation_url_is_public_path(self):
        gateway = PaymentGateway({"DONATION_URL": "https://example.test/donate"})
        readiness = gateway.readiness()
        self.assertEqual(readiness["valid_public_paths"][0]["label"], "donation")
        self.assertFalse(readiness["payment_provider"]["can_charge"])

    def test_invalid_url_rejected(self):
        gateway = PaymentGateway({"DONATION_URL": "javascript:alert(1)"})
        self.assertFalse(gateway.donation_status()["valid"])

    def test_provider_key_does_not_enable_charging(self):
        gateway = PaymentGateway({"PAYMENT_PROVIDER_API_KEY": "secret"})
        status = gateway.payment_provider_status()
        self.assertTrue(status["configured"])
        self.assertFalse(status["can_charge"])


if __name__ == "__main__":
    unittest.main()
