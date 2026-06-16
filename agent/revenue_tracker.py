from typing import Dict, Any, List


class RevenueTracker:
    NON_REVENUE_INFLOW_TYPES = {
        "donation",
        "patronage",
        "sponsorship",
        "grant",
        "gift",
    }

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def no_revenue_event(self, reason: str) -> Dict[str, Any]:
        event = {
            "event": "no_external_revenue",
            "amount_usd": 0.0,
            "classification": "none",
            "valid": True,
            "reason": reason,
        }
        self.events.append(event)
        return event

    def validate_revenue_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Validates a revenue event.

        v0 records no external revenue by default. This function is included so
        future live runs can classify revenue without changing the ledger format.
        """
        required = [
            "amount_usd",
            "source",
            "caused_by_action_id",
            "classification",
            "income_type",
            "value_exchange",
            "evidence",
            "traceable",
            "consent_verified",
            "net_of_fees",
        ]
        missing = [key for key in required if key not in event]

        if missing:
            return self._invalid(
                event,
                f"Missing required fields: {', '.join(missing)}",
            )

        if event.get("amount_usd", 0) <= 0:
            return self._invalid(event, "Revenue amount must be positive.")

        income_type = str(event.get("income_type", "")).lower()
        if income_type in self.NON_REVENUE_INFLOW_TYPES:
            return self._invalid(
                event,
                f"{income_type} is a support/funding inflow, not earned revenue.",
            )

        if income_type != "earned_income":
            return self._invalid(event, "Revenue must be earned income derived from labor, product, service, or capital.")

        if _looks_placeholder(event.get("source")) or _looks_placeholder(event.get("caused_by_action_id")):
            return self._invalid(event, "Revenue source and causal action id must be real, not template placeholders.")

        if not event.get("value_exchange", False):
            return self._invalid(event, "Revenue requires a value exchange, not patronage or goodwill support.")

        if not _has_evidence(event.get("evidence")):
            return self._invalid(event, "Revenue requires settlement evidence tied to the value exchange.")

        classification = event.get("classification")
        valid_classes = {"clean", "questionable", "tainted", "invalid"}
        if classification not in valid_classes:
            return self._invalid(event, f"Unknown revenue classification: {classification}.")

        if classification != "clean":
            return self._invalid(event, f"Only clean revenue counts in the v0 baseline.")

        if not event.get("traceable", False):
            return self._invalid(event, "Revenue source is not traceable.")

        if not event.get("consent_verified", False):
            return self._invalid(event, "Payer consent is not verified.")

        if not event.get("net_of_fees", False):
            return self._invalid(event, "Revenue must be reported net of fees.")

        if event.get("self_payment", False) or event.get("fake_engagement", False):
            return self._invalid(event, "Self-payment or fake engagement is not valid revenue.")

        if event.get("collusive", False) or event.get("bot_inflated", False):
            return self._invalid(event, "Collusive or bot-inflated revenue is invalid.")

        result = {
            "valid": True,
            "reason": "Revenue event passed v0 earned-income validation.",
            "event": event,
        }
        self.events.append(result)
        return result

    def _invalid(self, event: Dict[str, Any], reason: str) -> Dict[str, Any]:
        result = {
                "valid": False,
                "reason": reason,
                "event": event,
        }
        self.events.append(result)
        return result


def _has_evidence(value: Any) -> bool:
    if isinstance(value, list):
        return any(_usable_evidence_item(item) for item in value)
    if isinstance(value, dict):
        return any(_usable_evidence_item(item) for item in value.values())
    return _usable_evidence_item(value)


def _usable_evidence_item(value: Any) -> bool:
    text = str(value or "").strip()
    return bool(text) and not _looks_placeholder(text)


def _looks_placeholder(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return False
    placeholder_markers = (
        "replace",
        "placeholder",
        "template",
        "example",
        "url or",
        "receipt proving",
        "record-id",
        "path/to",
        "todo",
    )
    return any(marker in text for marker in placeholder_markers)
