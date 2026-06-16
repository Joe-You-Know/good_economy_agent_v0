import os
import re
from typing import Any, Dict


class PaymentGateway:
    """Readiness checks for support and future payment infrastructure.

    v0 deliberately does not initiate charges, invoices, subscriptions, or
    payouts. It only validates that configured support paths are explicit,
    voluntary, non-revenue, and safe to disclose.
    """

    def __init__(self, env=None):
        self.env = env or os.environ

    def donation_status(self) -> Dict[str, Any]:
        return self._support_url_status("DONATION_URL", "donation")

    def sponsorship_status(self) -> Dict[str, Any]:
        return self._support_url_status("SPONSORSHIP_URL", "sponsorship")

    def payment_provider_status(self) -> Dict[str, Any]:
        configured = bool(self.env.get("PAYMENT_PROVIDER_API_KEY"))
        return {
            "name": "PAYMENT_PROVIDER_API_KEY",
            "configured": configured,
            "can_charge": False,
            "reason": (
                "Provider key is configured, but v0 has no charge/invoice/subscription execution path."
                if configured else
                "Provider key is not configured."
            ),
        }

    def readiness(self) -> Dict[str, Any]:
        donation = self.donation_status()
        sponsorship = self.sponsorship_status()
        provider = self.payment_provider_status()
        valid_support_paths = [
            item for item in (donation, sponsorship)
            if item["configured"] and item["valid"]
        ]
        return {
            "valid_support_paths": valid_support_paths,
            "donation": donation,
            "sponsorship": sponsorship,
            "payment_provider": provider,
            "clean_revenue_boundary": (
                "Donation, patronage, sponsorship, grants, and gifts are support/funding inflows, "
                "not revenue. No payment collection is executed by the agent."
            ),
            "support_boundary": (
                "Configured donation/sponsorship links may be disclosed as non-revenue support paths only."
            ),
        }

    def _support_url_status(self, env_key: str, label: str) -> Dict[str, Any]:
        value = self.env.get(env_key, "").strip()
        configured = bool(value)
        valid = _is_public_http_url(value)
        return {
            "name": env_key,
            "label": label,
            "configured": configured,
            "valid": valid,
            "url": value if valid else "",
            "reason": _url_reason(configured, valid),
        }


def _is_public_http_url(value: str) -> bool:
    return bool(re.match(r"^https?://[^\s]+$", value or ""))


def _url_reason(configured: bool, valid: bool) -> str:
    if not configured:
        return "No URL configured."
    if not valid:
        return "Configured value is not a valid public HTTP(S) URL."
    return "URL is configured as an opt-in public support path."
