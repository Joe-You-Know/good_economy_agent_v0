import os
from pathlib import Path
from typing import Any, Dict, List

from .config import environment_capabilities
from .controls import KillSwitch, RateLimiter
from .payment_gateway import PaymentGateway


class LiveReadiness:
    def __init__(self, root: Path, config: Dict[str, Any]):
        self.root = Path(root)
        self.config = config
        self.kill_switch = KillSwitch(self.root, config["kill_switch_path"])
        self.rate_limiter = RateLimiter(self.root / config["rate_limit_state_path"])
        self.payment_gateway = PaymentGateway()

    def evaluate(self) -> Dict[str, Any]:
        kill_status = self.kill_switch.status()
        payment_status = self.payment_gateway.readiness()
        capabilities = environment_capabilities()

        blockers: List[str] = []
        warnings: List[str] = []

        if kill_status["triggered"]:
            blockers.append("Kill switch is active.")
        if not self.config.get("read_only_external_apis_allowed", False):
            blockers.append("Read-only external API calls are disabled.")
        if self.config.get("external_write_actions_allowed", False):
            warnings.append("External write actions are enabled; v0 should normally keep this false.")
        if not os.environ.get("COURTLISTENER_TOKEN"):
            warnings.append("COURTLISTENER_TOKEN is not configured; legal precedent checks will be skipped.")
        if not os.environ.get("GITHUB_TOKEN"):
            warnings.append("GITHUB_TOKEN is not configured; GitHub search will use unauthenticated limits or be skipped by policy.")
        if not (os.environ.get("OPENLAWS_API_BASE_URL") or self.config.get("openlaws_api_base_url")):
            warnings.append("OpenLaws base URL is not configured; OpenLaws checks will be skipped.")
        if not payment_status["valid_support_paths"]:
            warnings.append(
                "No valid donation or sponsorship support URL is configured. "
                "Support is not revenue and this does not block earned revenue."
            )

        return {
            "ready_for_read_only_live_discovery": not blockers,
            "ready_for_live_write_actions": False,
            "blockers": blockers,
            "warnings": warnings,
            "kill_switch": kill_status,
            "environment_capabilities": capabilities,
            "payment": payment_status,
            "rate_limit_state_path": str(self.root / self.config["rate_limit_state_path"]),
            "monitoring_state_path": str(self.root / self.config["monitoring_state_path"]),
            "external_write_boundary": (
                "Publishing, outbound messages, pull requests, payment collection, and marketplace actions "
                "remain disabled in v0."
            ),
        }

    def write_report(self, output_dir: Path, readiness: Dict[str, Any]) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "live_readiness_report.md"
        path.write_text(_render_readiness_report(readiness), encoding="utf-8")
        return path


def _render_readiness_report(readiness: Dict[str, Any]) -> str:
    blockers = _lines(readiness["blockers"])
    warnings = _lines(readiness["warnings"])
    capabilities = _capability_lines(readiness["environment_capabilities"])
    payment = readiness["payment"]
    support_paths = _lines(
        f'{item["label"]}: {item["url"]}'
        for item in payment["valid_support_paths"]
    )

    return f"""# Live Readiness Report

## Status

- Ready for read-only live discovery: {readiness["ready_for_read_only_live_discovery"]}
- Ready for live write actions: {readiness["ready_for_live_write_actions"]}

## Blockers

{blockers}

## Warnings

{warnings}

## Environment

{capabilities}

## Revenue and Support Boundary

- Public support paths: {support_paths}
- Payment provider can charge: {payment["payment_provider"]["can_charge"]}
- Revenue boundary: {payment["clean_revenue_boundary"]}
- Support boundary: {payment["support_boundary"]}

## Kill Switch

- Path: `{readiness["kill_switch"]["path"]}`
- Triggered: {readiness["kill_switch"]["triggered"]}

## State Files

- Rate limits: `{readiness["rate_limit_state_path"]}`
- Monitoring: `{readiness["monitoring_state_path"]}`

## External Write Boundary

{readiness["external_write_boundary"]}
"""


def _lines(values) -> str:
    values = list(values or [])
    if not values:
        return "- none"
    return "\n".join(f"- {value}" for value in values)


def _capability_lines(capabilities) -> str:
    lines = []
    for item in capabilities:
        status = "configured" if item.get("configured") else "not configured"
        lines.append(f'- {item.get("name")}: {status} ({item.get("classification")})')
    return "\n".join(lines)
