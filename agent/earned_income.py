import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


EARNED_INCOME_TERMS = {
    "bounty",
    "bug bounty",
    "paid",
    "payment",
    "reward",
    "compensation",
    "contract",
    "commission",
    "invoice",
    "license",
    "marketplace",
}

SUPPORT_INFLOW_TERMS = {
    "donate",
    "donation",
    "patron",
    "patronage",
    "sponsor",
    "sponsorship",
    "grant",
    "gift",
}

PUBLIC_BENEFIT_TERMS = {
    "accessibility",
    "a11y",
    "documentation",
    "docs",
    "education",
    "open source",
    "bug",
    "reproducibility",
    "public good",
    "civic",
    "nonprofit",
}

HIGH_RISK_TERMS = {
    "blockchain",
    "bug bounty",
    "credit market",
    "credit markets",
    "casino",
    "defi",
    "delete me",
    "demo",
    "eur",
    "euro",
    "flow credit markets",
    "gambling",
    "crypto",
    "entitlement",
    "mrwk",
    "onflow",
    "payment gateway",
    "rtc",
    "reward points",
    "medical advice",
    "monetisation",
    "monetization",
    "legal advice",
    "phish",
    "phishing",
    "financial advice",
    "smart contract",
    "stellar",
    "stripe",
    "scrape",
    "spam",
    "token",
    "traffic",
    "wallet",
    "referral",
}

MONEY_RE = re.compile(
    r"(?:\$|usd\s*)(?P<prefix>\d+(?:,\d{3})*(?:\.\d{1,2})?)|"
    r"(?P<suffix>\d+(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:usd|dollars)",
    re.IGNORECASE,
)


class EarnedIncomeRunway:
    """Builds a local, read-only runway from discovery results to earned income."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_from_github_results(
        self,
        github_results: Iterable[Dict[str, Any]],
        candidate_limit: int = 10,
    ) -> Dict[str, Any]:
        candidates = candidates_from_github_results(github_results)
        candidates = candidates[: int(candidate_limit)]
        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "candidate_count": len(candidates),
            "candidates": candidates,
            "revenue_boundary": (
                "Only earned income from a real value exchange can count as revenue. "
                "Donation, patronage, sponsorship, grant, and gift inflows are support/funding only."
            ),
            "write_action_boundary": (
                "Discovery is read-only. Claiming work, submitting pull requests, creating listings, "
                "sending messages, invoicing, or collecting payment requires a separately reviewed mode."
            ),
            "settlement_evidence_required": [
                "accepted bounty or paid-work terms",
                "logged action that produced the value",
                "payer/source identity or platform receipt",
                "net amount after platform and transaction fees",
                "evidence that no self-payment, collusion, fake engagement, or coercion occurred",
            ],
        }
        self.write_report(report)
        return report

    def write_report(self, report: Dict[str, Any]) -> Dict[str, str]:
        json_path = self.output_dir / "earned_income_runway.json"
        md_path = self.output_dir / "earned_income_runway.md"
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        md_path.write_text(render_runway_markdown(report), encoding="utf-8")
        return {"json_path": str(json_path), "markdown_path": str(md_path)}


def candidates_from_github_results(github_results: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    seen = set()
    for query_result in github_results or []:
        query = query_result.get("query", "")
        if not query_result.get("ok"):
            continue
        for issue in query_result.get("results", []) or []:
            candidate = classify_github_issue(issue, query=query)
            if not candidate["eligible_for_earned_income_discovery"]:
                continue
            key = candidate["source_url"]
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
    return sorted(candidates, key=lambda item: item["score"], reverse=True)


def classify_github_issue(issue: Dict[str, Any], query: str = "") -> Dict[str, Any]:
    labels = [str(label) for label in issue.get("labels", [])]
    text = _search_text([
        issue.get("title", ""),
        issue.get("body_excerpt", ""),
        issue.get("repository_url", ""),
        issue.get("html_url", ""),
        " ".join(labels),
        query,
    ])
    earned_signals = _matching_terms(text, EARNED_INCOME_TERMS)
    support_signals = _matching_terms(text, SUPPORT_INFLOW_TERMS)
    benefit_signals = _matching_terms(text, PUBLIC_BENEFIT_TERMS)
    risk_signals = _matching_terms(text, HIGH_RISK_TERMS)
    amount = _extract_usd_amount(text)

    strong_earned_signals = [term for term in earned_signals if term != "reward"]
    has_earned_signal = bool(strong_earned_signals or amount or ("reward" in earned_signals and amount))
    support_only = bool(support_signals) and not has_earned_signal
    eligible = has_earned_signal and not support_only and not risk_signals
    score = _score_candidate(
        has_earned_signal=has_earned_signal,
        amount=amount,
        benefit_signals=benefit_signals,
        risk_signals=risk_signals,
        support_signals=support_signals,
    )

    reasons = []
    if has_earned_signal:
        reasons.append("explicit earned-income signal found")
    if amount:
        reasons.append("possible USD amount found")
    if benefit_signals:
        reasons.append("public-benefit signal found")
    if support_only:
        reasons.append("support-only inflow signal is not revenue")
    if risk_signals:
        reasons.append("high-risk term requires rejection or human review")
    if not has_earned_signal:
        reasons.append("no earned-income signal found")

    return {
        "candidate_id": _candidate_id(issue.get("html_url") or issue.get("title") or query),
        "source": "github",
        "source_query": query,
        "source_url": issue.get("html_url", ""),
        "repository_url": issue.get("repository_url", ""),
        "title": issue.get("title", ""),
        "labels": labels,
        "income_type": "earned_income" if has_earned_signal and not support_only else "not_revenue",
        "value_exchange_required": True,
        "expected_liquid_revenue_usd": amount or 0.0,
        "score": score,
        "eligible_for_earned_income_discovery": eligible,
        "earned_income_signals": earned_signals,
        "support_inflow_signals": support_signals,
        "public_benefit_signals": benefit_signals,
        "risk_signals": risk_signals,
        "reasons": reasons,
        "next_steps": [
            "Verify the issue or platform states payment, bounty, contract, product, or license terms.",
            "Confirm the work is allowed by platform rules and does not require cold outreach.",
            "Create or submit only the useful work requested by the recipient or platform.",
            "Record the action id, acceptance evidence, payer/source, and net amount after fees.",
            "Validate the receipt with revenue-verify before counting it as revenue.",
        ],
        "blocked_in_v0_without_review": [
            "claiming paid work",
            "submitting pull requests",
            "sending outbound messages",
            "creating invoices",
            "collecting payment",
        ],
    }


def render_runway_markdown(report: Dict[str, Any]) -> str:
    candidate_lines = []
    for index, candidate in enumerate(report.get("candidates", []), start=1):
        candidate_lines.append(
            "\n".join([
                f"### {index}. {candidate['title'] or 'Untitled candidate'}",
                "",
                f"- Source: {candidate['source_url'] or 'unknown'}",
                f"- Score: {candidate['score']}",
                f"- Expected earned revenue: ${candidate['expected_liquid_revenue_usd']:.2f}",
                f"- Earned-income signals: {_inline(candidate['earned_income_signals'])}",
                f"- Public-benefit signals: {_inline(candidate['public_benefit_signals'])}",
                f"- Support inflow signals: {_inline(candidate['support_inflow_signals'])}",
                f"- Risk signals: {_inline(candidate['risk_signals'])}",
                f"- Reasons: {_inline(candidate['reasons'])}",
            ])
        )
    if not candidate_lines:
        candidate_lines.append("No earned-income candidates were found in the current read-only snapshot.")

    evidence = "\n".join(f"- {item}" for item in report.get("settlement_evidence_required", []))
    return f"""# Earned Income Runway

Generated: {report["timestamp_utc"]}

## Boundary

{report["revenue_boundary"]}

{report["write_action_boundary"]}

## Candidates

{chr(10).join(candidate_lines)}

## Settlement Evidence Required

{evidence}
"""


def _score_candidate(
    has_earned_signal: bool,
    amount: float,
    benefit_signals: List[str],
    risk_signals: List[str],
    support_signals: List[str],
) -> float:
    score = 0.0
    if has_earned_signal:
        score += 0.45
    if amount:
        score += min(0.25, amount / 400.0)
    score += min(0.2, len(benefit_signals) * 0.05)
    if support_signals:
        score -= 0.1
    if risk_signals:
        score -= 1.0
    return round(max(0.0, score), 6)


def _matching_terms(text: str, terms: Iterable[str]) -> List[str]:
    matches = []
    for term in sorted(terms):
        pattern = r"\b" + re.escape(term).replace(r"\ ", r"\s+") + r"\b"
        if re.search(pattern, text):
            matches.append(term)
    return matches


def _extract_usd_amount(text: str) -> float:
    amounts = []
    for match in MONEY_RE.finditer(text):
        value = match.group("prefix") or match.group("suffix")
        if not value:
            continue
        try:
            amounts.append(float(value.replace(",", "")))
        except ValueError:
            continue
    return max(amounts) if amounts else 0.0


def _candidate_id(value: str) -> str:
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]
    return f"earned_income_{digest}"


def _search_text(values: Iterable[Any]) -> str:
    combined = " ".join(str(value or "").lower() for value in values)
    combined = combined.replace("€", " euro ")
    return re.sub(r"[^a-z0-9$.,]+", " ", combined)


def _inline(values: Iterable[Any]) -> str:
    values = list(values or [])
    return "; ".join(str(value) for value in values) if values else "none"
