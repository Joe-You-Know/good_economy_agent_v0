from dataclasses import dataclass, asdict, fields
from typing import Dict, Any, List


@dataclass
class Opportunity:
    id: str
    title: str
    category: str
    expected_liquid_revenue_usd: float
    public_benefit_score: float
    probability_of_completion: float
    verification_strength: float
    ethics_cleanliness: float
    compute_cost_estimate_usd: float
    runtime_cost_estimate_usd: float
    platform_friction: float
    legal_risk: float
    description: str
    risk_tags: List[str] = None
    revenue_channels: List[str] = None
    support_channels: List[str] = None
    required_external_actions: List[str] = None
    beneficiary: str = "public"
    evidence_notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Opportunity":
        known_fields = {field.name for field in fields(cls)}
        cleaned = {key: value for key, value in data.items() if key in known_fields}
        opportunity = cls(**cleaned)
        opportunity.risk_tags = list(opportunity.risk_tags or [])
        opportunity.revenue_channels = list(opportunity.revenue_channels or [])
        opportunity.support_channels = list(opportunity.support_channels or [])
        opportunity.required_external_actions = list(opportunity.required_external_actions or [])
        return opportunity

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EthicsDecision:
    allowed: bool
    negative_debt: float
    positive_score: float
    reasons: List[str]
    blocked_categories: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ArtifactRecord:
    artifact_id: str
    title: str
    category: str
    path: str
    files: List[str]
    public_benefit_claim: str
    revenue_path: str
    license: str
    limitations: List[str]
    support_links: Dict[str, str]
    content_source: str
    negative_ethics_debt: float
    positive_ethics_score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
