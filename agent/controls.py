import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List


class KillSwitchTriggered(RuntimeError):
    pass


class KillSwitch:
    def __init__(self, root: Path, relative_path: str):
        self.path = _safe_project_path(root, relative_path)

    def status(self) -> Dict[str, Any]:
        exists = self.path.exists()
        return {
            "path": str(self.path),
            "triggered": exists,
            "message": self.path.read_text(encoding="utf-8").strip() if exists else "",
        }

    def assert_not_triggered(self) -> None:
        status = self.status()
        if status["triggered"]:
            raise KillSwitchTriggered(
                f"Kill switch is active at {status['path']}. "
                "Remove the file only when you intentionally want live reads to resume."
            )


class RateLimiter:
    def __init__(self, state_path: Path, clock: Callable[[], float] = None):
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock or time.time

    def check(self, bucket: str, limits: Dict[str, Dict[str, int]], cost: int = 1) -> Dict[str, Any]:
        state = self._load()
        now = float(self.clock())
        bucket_state = state.setdefault(bucket, [])
        bucket_state[:] = [
            item for item in bucket_state
            if _is_within_any_window(now, float(item["timestamp"]), limits)
        ]

        violations = []
        for name, limit in limits.items():
            window = int(limit["window_seconds"])
            max_requests = int(limit["max_requests"])
            used = sum(1 for item in bucket_state if now - float(item["timestamp"]) < window)
            if used + cost > max_requests:
                oldest = min(
                    (float(item["timestamp"]) for item in bucket_state if now - float(item["timestamp"]) < window),
                    default=now,
                )
                retry_after_seconds = max(0.0, window - (now - oldest))
                violations.append({
                    "limit": name,
                    "used": used,
                    "max_requests": max_requests,
                    "window_seconds": window,
                    "retry_after_seconds": round(retry_after_seconds, 3),
                })

        allowed = not violations
        state[bucket] = bucket_state
        self._save(state)
        return {
            "allowed": allowed,
            "bucket": bucket,
            "cost": cost,
            "violations": violations,
        }

    def record(self, bucket: str, count: int = 1) -> Dict[str, Any]:
        state = self._load()
        now = float(self.clock())
        bucket_state = state.setdefault(bucket, [])
        for _ in range(count):
            bucket_state.append({"timestamp": now})
        state[bucket] = bucket_state
        self._save(state)
        return {"bucket": bucket, "recorded": count, "timestamp": now}

    def snapshot(self) -> Dict[str, Any]:
        return self._load()

    def _load(self) -> Dict[str, List[Dict[str, Any]]]:
        if not self.state_path.exists():
            return {}
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def _save(self, state: Dict[str, Any]) -> None:
        self.state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _is_within_any_window(now: float, timestamp: float, limits: Dict[str, Dict[str, int]]) -> bool:
    return any(now - timestamp < int(limit["window_seconds"]) for limit in limits.values())


def _safe_project_path(root: Path, relative_path: str) -> Path:
    root = Path(root).resolve()
    candidate = (root / relative_path).resolve()
    if root != candidate and root not in candidate.parents:
        raise ValueError(f"Path escapes project root: {relative_path}")
    return candidate
