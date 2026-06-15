import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class AccountRegister:
    """Private register for non-secret account metadata.

    Passwords and raw API tokens do not belong here. Use `.env` for API tokens
    and a real password manager or OS credential store for passwords.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "private" / "account_register.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def upsert(self, service: str, email: str, purpose: str, login_url: str = "", notes: str = "") -> Dict[str, Any]:
        data = self._load()
        accounts: List[Dict[str, Any]] = data.setdefault("accounts", [])
        existing = next((item for item in accounts if item["service"] == service), None)
        record = {
            "service": service,
            "email": email,
            "purpose": purpose,
            "login_url": login_url,
            "notes": notes,
            "password_storage": "external password manager or provider account flow; not stored in repo",
            "updated_utc": datetime.now(timezone.utc).isoformat(),
        }
        if existing:
            existing.update(record)
        else:
            accounts.append(record)
        self._save(data)
        return record

    def list_accounts(self) -> Dict[str, Any]:
        return self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"accounts": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"accounts": []}
        if not isinstance(data, dict):
            return {"accounts": []}
        data.setdefault("accounts", [])
        return data

    def _save(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
