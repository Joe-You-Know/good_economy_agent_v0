import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class EnvSpec:
    name: str
    classification: str
    required_for: str
    default: str = ""
    acquire_url: str = ""
    notes: str = ""


ENV_SPECS = [
    EnvSpec(
        "OPENAI_API_KEY",
        "secret",
        "assist-run model drafting",
        acquire_url="https://platform.openai.com/api-keys",
        notes="Configured already in this workspace during the last check.",
    ),
    EnvSpec(
        "GITHUB_TOKEN",
        "secret",
        "higher-confidence GitHub discovery and future PR submission modes",
        acquire_url="https://github.com/settings/tokens",
        notes="Read-only discovery can use public GitHub search without this, but authenticated use is more stable.",
    ),
    EnvSpec(
        "COURTLISTENER_TOKEN",
        "secret",
        "CourtListener case-law search and citation checks",
        acquire_url="https://www.courtlistener.com/profile/api-token/",
        notes="Use token auth in the form required by CourtListener; the code adds the Token prefix.",
    ),
    EnvSpec(
        "OPENLAWS_API_BASE_URL",
        "public_url",
        "OpenLaws search adapter",
        notes="Set this to the provider's API base URL. The default adapter calls /search with q and limit parameters.",
    ),
    EnvSpec(
        "OPENLAWS_API_KEY",
        "secret",
        "OpenLaws authenticated search if required by the configured endpoint",
        notes="Optional when the configured OpenLaws endpoint allows unauthenticated search.",
    ),
    EnvSpec(
        "PAYMENT_PROVIDER_API_KEY",
        "secret",
        "future payment provider verification",
        notes="Presence never enables charging in v0.",
    ),
    EnvSpec(
        "DONATION_URL",
        "public_url",
        "voluntary opt-in donation path",
        notes="Must be a public http(s) URL. The agent cannot create charges.",
    ),
    EnvSpec(
        "SPONSORSHIP_URL",
        "public_url",
        "voluntary opt-in sponsorship path",
        notes="Must be a public http(s) URL. The agent cannot create subscriptions.",
    ),
]


class EnvManager:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.env_path = self.root / ".env"

    def bootstrap(self) -> Dict[str, Any]:
        existing = self._read_env_map()
        missing = [spec for spec in ENV_SPECS if spec.name not in existing]
        if missing:
            lines = []
            if self.env_path.exists() and self.env_path.read_text(encoding="utf-8").strip():
                lines.append("")
            lines.append("# Added by Good Economy Agent env bootstrap")
            for spec in missing:
                lines.append(f"{spec.name}={spec.default}")
            self._append_lines(lines)
        return {
            "env_path": str(self.env_path),
            "added": [spec.name for spec in missing],
            "existing": sorted(existing.keys()),
        }

    def sync_from_process(self, overwrite_blank_only: bool = True) -> Dict[str, Any]:
        entries = self._read_env_map()
        changed = []
        skipped = []

        for spec in ENV_SPECS:
            process_value = os.environ.get(spec.name)
            if process_value is None:
                skipped.append({"name": spec.name, "reason": "not present in process environment"})
                continue
            current_value = entries.get(spec.name, "")
            if current_value and overwrite_blank_only:
                skipped.append({"name": spec.name, "reason": "project .env already has a value"})
                continue
            entries[spec.name] = process_value
            changed.append(spec.name)

        if changed:
            self._write_env_map(entries)

        return {
            "env_path": str(self.env_path),
            "changed": changed,
            "skipped": skipped,
        }

    def report(self) -> Dict[str, Any]:
        entries = self._read_env_map()
        rows = []
        for spec in ENV_SPECS:
            value = entries.get(spec.name) or os.environ.get(spec.name, "")
            configured = bool(value)
            valid = _valid_value(spec, value)
            rows.append({
                "name": spec.name,
                "classification": spec.classification,
                "required_for": spec.required_for,
                "configured": configured,
                "valid": valid,
                "source": _source_for(spec.name, entries),
                "acquire_url": spec.acquire_url,
                "notes": spec.notes,
                "display_value": value if spec.classification == "public_url" and valid else "",
            })
        return {
            "env_path": str(self.env_path),
            "entries": rows,
            "missing": [row["name"] for row in rows if not row["configured"]],
            "invalid": [row["name"] for row in rows if row["configured"] and not row["valid"]],
        }

    def write_report(self, output_dir: Path) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report = self.report()
        path = output_dir / "env_readiness_report.md"
        path.write_text(_render_env_report(report), encoding="utf-8")
        return path

    def _read_env_map(self) -> Dict[str, str]:
        entries: Dict[str, str] = {}
        if not self.env_path.exists():
            return entries
        for line in self.env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            entries[key.strip()] = value.strip().strip('"').strip("'")
        return entries

    def _append_lines(self, lines: List[str]) -> None:
        existing_text = self.env_path.read_text(encoding="utf-8") if self.env_path.exists() else ""
        separator = "" if not existing_text or existing_text.endswith("\n") else "\n"
        self.env_path.write_text(existing_text + separator + "\n".join(lines) + "\n", encoding="utf-8")

    def _write_env_map(self, entries: Dict[str, str]) -> None:
        lines = ["# Good Economy Agent local environment"]
        for spec in ENV_SPECS:
            lines.append(f"{spec.name}={entries.get(spec.name, '')}")
        self.env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _valid_value(spec: EnvSpec, value: str) -> bool:
    if not value:
        return False
    if spec.classification == "public_url":
        return value.startswith("http://") or value.startswith("https://")
    return True


def _source_for(name: str, entries: Dict[str, str]) -> str:
    if entries.get(name):
        return ".env"
    if os.environ.get(name):
        return "process"
    if name in entries:
        return ".env_blank"
    return "missing"


def _render_env_report(report: Dict[str, Any]) -> str:
    rows = []
    for entry in report["entries"]:
        value_note = f" Value: {entry['display_value']}" if entry["display_value"] else ""
        acquire = f" Acquire: {entry['acquire_url']}" if entry["acquire_url"] else ""
        rows.append(
            f"- {entry['name']}: configured={entry['configured']}, valid={entry['valid']}, "
            f"source={entry['source']}, class={entry['classification']}.{value_note}{acquire}"
        )
    missing = "\n".join(f"- {name}" for name in report["missing"]) or "- none"
    invalid = "\n".join(f"- {name}" for name in report["invalid"]) or "- none"
    return f"""# Environment Readiness Report

Path: `{report["env_path"]}`

Secret values are never printed in this report.

## Entries

{chr(10).join(rows)}

## Missing

{missing}

## Invalid

{invalid}
"""
