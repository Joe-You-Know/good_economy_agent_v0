import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List


class ConfigError(ValueError):
    pass


REQUIRED_NUMERIC_FIELDS = (
    "starting_compute_credit_usd",
    "starting_economic_cash_usd",
    "runtime_limit_cpu_hours",
    "hard_stop_compute_remaining_usd",
    "max_single_call_usd",
    "max_planning_budget_usd",
    "max_search_budget_usd",
    "max_build_budget_usd",
    "max_publish_budget_usd",
    "max_final_report_budget_usd",
)

REQUIRED_BOOL_FIELDS = (
    "cold_outreach_allowed",
    "paid_tools_allowed_before_revenue",
    "negative_ethics_allowed",
)

REQUIRED_LIST_FIELDS = (
    "allowed_categories",
    "forbidden_actions",
    "baseline_revenue_channels",
    "non_revenue_support_channels",
)

NON_REVENUE_SUPPORT_CHANNELS = {
    "donation",
    "voluntary_donation",
    "patronage",
    "sponsorship",
    "grant",
    "gift",
}

SECRET_ENV_KEYS = (
    "OPENAI_API_KEY",
    "GITHUB_TOKEN",
    "COURTLISTENER_TOKEN",
    "OPENLAWS_API_KEY",
    "PAYMENT_PROVIDER_API_KEY",
)

PUBLIC_ENV_KEYS = (
    "DONATION_URL",
    "SPONSORSHIP_URL",
    "OPENLAWS_API_BASE_URL",
)


def load_json_config(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Config JSON is invalid: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Config must be a JSON object.")
    return validate_config(data)


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    validated = dict(config)
    errors: List[str] = []

    for field in REQUIRED_NUMERIC_FIELDS:
        if field not in validated:
            errors.append(f"Missing numeric config field: {field}")
            continue
        try:
            validated[field] = float(validated[field])
        except (TypeError, ValueError):
            errors.append(f"Config field must be numeric: {field}")

    for field in REQUIRED_BOOL_FIELDS:
        if field not in validated:
            errors.append(f"Missing boolean config field: {field}")
        elif not isinstance(validated[field], bool):
            errors.append(f"Config field must be boolean: {field}")

    for field in REQUIRED_LIST_FIELDS:
        value = validated.get(field)
        if not isinstance(value, list) or not value:
            errors.append(f"Config field must be a non-empty list: {field}")

    if errors:
        raise ConfigError("; ".join(errors))

    if validated["starting_compute_credit_usd"] < 0:
        errors.append("starting_compute_credit_usd cannot be negative")
    if validated["starting_economic_cash_usd"] != 0:
        errors.append("v0 baseline must start with exactly $0 economic cash")
    if validated["hard_stop_compute_remaining_usd"] < 0:
        errors.append("hard_stop_compute_remaining_usd cannot be negative")
    if validated["starting_compute_credit_usd"] < validated["hard_stop_compute_remaining_usd"]:
        errors.append("compute credit cannot start below the hard stop")
    if validated["max_single_call_usd"] > (
        validated["starting_compute_credit_usd"] - validated["hard_stop_compute_remaining_usd"]
    ):
        errors.append("max_single_call_usd exceeds spendable compute credit")

    if validated["negative_ethics_allowed"]:
        errors.append("v0 baseline requires negative_ethics_allowed=false")
    if validated["cold_outreach_allowed"]:
        errors.append("v0 baseline requires cold_outreach_allowed=false")
    if validated["paid_tools_allowed_before_revenue"]:
        errors.append("v0 baseline requires paid_tools_allowed_before_revenue=false")

    revenue_channels = {
        str(channel).lower()
        for channel in validated.get("baseline_revenue_channels", [])
    }
    support_overlap = sorted(revenue_channels & NON_REVENUE_SUPPORT_CHANNELS)
    if support_overlap:
        errors.append(
            "baseline_revenue_channels cannot include non-revenue support inflows: "
            + ", ".join(support_overlap)
        )

    if errors:
        raise ConfigError("; ".join(errors))

    validated.setdefault("external_actions_allowed", False)
    validated.setdefault("read_only_external_apis_allowed", True)
    validated.setdefault("external_write_actions_allowed", False)
    validated.setdefault("kill_switch_path", "KILL_SWITCH")
    validated.setdefault("rate_limit_state_path", "data/rate_limits.json")
    validated.setdefault("monitoring_state_path", "data/monitoring_state.json")
    validated.setdefault("courtlistener_api_base_url", "https://www.courtlistener.com/api/rest/v4")
    validated.setdefault(
        "courtlistener_rate_limits",
        {
            "minute": {"max_requests": 5, "window_seconds": 60},
            "hour": {"max_requests": 50, "window_seconds": 3600},
            "day": {"max_requests": 125, "window_seconds": 86400},
        },
    )
    validated.setdefault("courtlistener_citation_lookup_max_chars", 64000)
    validated.setdefault("courtlistener_citation_lookup_max_citations", 250)
    validated.setdefault("github_api_base_url", "https://api.github.com")
    validated.setdefault("github_rate_limits", {"minute": {"max_requests": 10, "window_seconds": 60}})
    validated.setdefault("openlaws_api_base_url", "")
    validated.setdefault("openlaws_rate_limits", {"minute": {"max_requests": 5, "window_seconds": 60}})
    validated.setdefault("live_discovery_query_limit", 5)
    validated.setdefault(
        "github_live_queries",
        [
            "is:issue is:open label:documentation label:\"good first issue\"",
            "is:issue is:open label:accessibility label:\"help wanted\"",
            "is:issue is:open label:\"public good\"",
        ],
    )
    validated.setdefault(
        "earned_income_live_queries",
        [
            "is:issue is:open bounty label:accessibility",
            "is:issue is:open bounty label:documentation",
            "is:issue is:open bounty label:\"good first issue\"",
            "is:issue is:open reward accessibility",
            "is:issue is:open reward documentation",
        ],
    )
    validated.setdefault("earned_income_candidate_limit", 10)
    validated.setdefault(
        "legal_precedent_queries",
        [
            "AI generated legal information disclaimer unauthorized practice of law",
            "charitable solicitation donation platform disclosure online",
            "accessibility checklist legal compliance disclaimer",
        ],
    )
    validated.setdefault("openai_assist_model", "gpt-4.1-mini")
    validated.setdefault("openai_assist_estimated_call_usd", 0.05)
    validated.setdefault("openai_assist_max_output_tokens", 1200)
    validated.setdefault("openai_assist_timeout_seconds", 45)
    validated.setdefault("artifact_license", "MIT for code, CC BY 4.0 for documentation unless changed by operator")
    return validated


def load_env_file(path: Path, override: bool = False) -> List[str]:
    loaded: List[str] = []
    env_path = Path(path)
    if not env_path.exists():
        return loaded

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded


def environment_capabilities(keys: Iterable[str] = None) -> List[Dict[str, Any]]:
    selected = list(keys or (SECRET_ENV_KEYS + PUBLIC_ENV_KEYS))
    capabilities: List[Dict[str, Any]] = []
    for key in selected:
        capabilities.append(
            {
                "name": key,
                "configured": bool(os.environ.get(key)),
                "classification": "secret" if key in SECRET_ENV_KEYS else "public_url",
            }
        )
    return capabilities


def public_support_links() -> Dict[str, str]:
    links: Dict[str, str] = {}
    for key, label in (("DONATION_URL", "donation"), ("SPONSORSHIP_URL", "sponsorship")):
        value = os.environ.get(key, "").strip()
        if _is_public_http_url(value):
            links[label] = value
    return links


def _is_public_http_url(value: str) -> bool:
    if not value:
        return False
    return bool(re.match(r"^https?://[^\s]+$", value))
