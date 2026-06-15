import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4


class JsonlLedger:
    DEFAULT_LEDGER_NAMES = (
        "actions",
        "artifacts",
        "costs",
        "ethics",
        "opportunities",
        "revenue",
    )

    def __init__(self, log_dir: Path, run_id: str = None, reset: bool = False):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or self.new_run_id()
        self._sequence = 0
        if reset:
            self.reset_known_ledgers()

    @staticmethod
    def new_run_id() -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"run_{stamp}_{uuid4().hex[:8]}"

    def reset_known_ledgers(self) -> None:
        for name in self.DEFAULT_LEDGER_NAMES:
            (self.log_dir / f"{name}.jsonl").write_text("", encoding="utf-8")

    def append(self, name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        path = self.log_dir / f"{name}.jsonl"
        self._sequence += 1
        enriched = {
            "record_id": f"{self.run_id}:{self._sequence:06d}",
            "run_id": self.run_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            **record,
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(enriched, ensure_ascii=False, sort_keys=True) + "\n")
        return enriched

    def read_all(self, name: str):
        path = self.log_dir / f"{name}.jsonl"
        if not path.exists():
            return []
        records = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
