import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .controls import KillSwitch, RateLimiter


class Monitor:
    def __init__(self, root: Path, config: Dict[str, Any]):
        self.root = Path(root)
        self.config = config
        self.kill_switch = KillSwitch(self.root, config["kill_switch_path"])
        self.rate_limiter = RateLimiter(self.root / config["rate_limit_state_path"])
        self.state_path = self.root / config["monitoring_state_path"]
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def snapshot(self) -> Dict[str, Any]:
        log_dir = self.root / "logs"
        output_dir = self.root / "outputs"
        snapshot = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "kill_switch": self.kill_switch.status(),
            "rate_limits": self.rate_limiter.snapshot(),
            "ledger_counts": _ledger_counts(log_dir),
            "outputs": {
                "final_report_exists": (output_dir / "final_report.md").exists(),
                "public_artifact_dir_exists": (output_dir / "public_artifact").exists(),
                "live_readiness_report_exists": (output_dir / "live_readiness_report.md").exists(),
                "live_discovery_snapshot_exists": (output_dir / "live_discovery_snapshot.json").exists(),
            },
        }
        self.state_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        return snapshot


def _ledger_counts(log_dir: Path) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for path in Path(log_dir).glob("*.jsonl"):
        counts[path.stem] = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return counts
