import json
import os
from pathlib import Path
from typing import Any, Dict


DEFAULT_DESTINATION_PATH = "private/income_destination.json"


class IncomeDestination:
    """Loads the explicit destination for earned income payouts."""

    def __init__(self, root: Path, env=None):
        self.root = Path(root)
        self.env = env or os.environ
        self.path = self.root / DEFAULT_DESTINATION_PATH

    def load(self) -> Dict[str, Any]:
        data = self._load_private_file()
        if not data:
            data = self._load_env()

        method = str(data.get("method", "")).strip()
        account = str(data.get("account", "")).strip()
        currency = str(data.get("currency", "USD")).strip() or "USD"
        configured = bool(method and account)
        return {
            "configured": configured,
            "method": method,
            "account": account,
            "currency": currency,
            "support_excluded": bool(data.get("support_excluded", True)),
            "routing_note": data.get("routing_note", ""),
            "source": data.get("source", str(self.path) if self.path.exists() else "missing"),
            "display": _display_destination(method, account, currency) if configured else "not configured",
        }

    def _load_private_file(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"source": str(self.path), "routing_note": "income destination file is invalid JSON"}
        if not isinstance(data, dict):
            return {"source": str(self.path), "routing_note": "income destination file must be a JSON object"}
        data["source"] = str(self.path)
        return data

    def _load_env(self) -> Dict[str, Any]:
        method = self.env.get("EARNED_INCOME_DESTINATION_METHOD", "")
        account = self.env.get("EARNED_INCOME_DESTINATION_ACCOUNT", "")
        if not method and not account:
            return {}
        return {
            "method": method,
            "account": account,
            "currency": self.env.get("EARNED_INCOME_DESTINATION_CURRENCY", "USD"),
            "support_excluded": True,
            "source": "process environment",
        }


def _display_destination(method: str, account: str, currency: str) -> str:
    return f"{method}: {account} ({currency})"
