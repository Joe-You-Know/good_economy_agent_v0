from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ComputeWallet:
    starting_credit_usd: float
    hard_stop_remaining_usd: float
    max_single_charge_usd: float = None
    spent_usd: float = 0.0

    @property
    def remaining_usd(self) -> float:
        return max(0.0, self.starting_credit_usd - self.spent_usd)

    def can_spend(self, estimated_usd: float) -> bool:
        if estimated_usd < 0:
            return False
        return (self.remaining_usd - estimated_usd) >= self.hard_stop_remaining_usd

    def charge(self, amount_usd: float, reason: str) -> Dict[str, Any]:
        if amount_usd < 0:
            raise ValueError("Cannot charge a negative amount.")
        if self.max_single_charge_usd is not None and amount_usd > self.max_single_charge_usd:
            raise RuntimeError(
                f"Budget gate refused charge ${amount_usd:.4f}. "
                f"Single-charge cap is ${self.max_single_charge_usd:.4f}."
            )
        if not self.can_spend(amount_usd):
            raise RuntimeError(
                f"Budget gate refused charge ${amount_usd:.4f}. "
                f"Remaining ${self.remaining_usd:.4f}, hard stop ${self.hard_stop_remaining_usd:.4f}."
            )
        self.spent_usd += amount_usd
        return {
            "event": "compute_charge",
            "amount_usd": round(amount_usd, 6),
            "reason": reason,
            "spent_total_usd": round(self.spent_usd, 6),
            "remaining_usd": round(self.remaining_usd, 6),
        }


@dataclass
class EconomicWallet:
    starting_cash_usd: float = 0.0
    earned_usd: float = 0.0
    spent_usd: float = 0.0

    @property
    def balance_usd(self) -> float:
        return self.starting_cash_usd + self.earned_usd - self.spent_usd

    def record_revenue(self, amount_usd: float, source: str) -> Dict[str, Any]:
        if amount_usd < 0:
            raise ValueError("Revenue cannot be negative.")
        self.earned_usd += amount_usd
        return {
            "event": "revenue_recorded",
            "amount_usd": round(amount_usd, 6),
            "source": source,
            "earned_total_usd": round(self.earned_usd, 6),
            "economic_balance_usd": round(self.balance_usd, 6),
        }

    def can_spend(self, amount_usd: float) -> bool:
        return amount_usd >= 0 and self.balance_usd >= amount_usd

    def spend(self, amount_usd: float, reason: str) -> Dict[str, Any]:
        if not self.can_spend(amount_usd):
            raise RuntimeError("Economic wallet cannot spend unearned money.")
        self.spent_usd += amount_usd
        return {
            "event": "economic_spend",
            "amount_usd": round(amount_usd, 6),
            "reason": reason,
            "spent_total_usd": round(self.spent_usd, 6),
            "economic_balance_usd": round(self.balance_usd, 6),
        }
