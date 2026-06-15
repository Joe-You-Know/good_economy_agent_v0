# Opportunity Method

The agent searches for the smallest clean unit of useful work.

## Preferred Opportunities

1. Public-good bounty
2. Open-source issue
3. Documentation improvement
4. Accessibility improvement
5. Open-science reproducibility aid
6. Education artifact
7. Resource-efficiency tool
8. Small-business resilience tool
9. Civic/nonprofit template
10. Public documentation repair

## Opportunity Score

```text
opportunity_score =
    (expected_liquid_revenue + 1)
  * public_benefit_score
  * probability_of_completion
  * verification_strength
  * ethics_cleanliness
  - compute_cost_estimate
  - runtime_cost_estimate
  - platform_friction
  - legal_risk
  - safety_penalty
```

The `+ 1` term lets zero-revenue public-good opportunities still compete when
they are useful, feasible, low-risk, and cheap to produce.

## Rejection Rules

Reject immediately if the opportunity requires:

- spam,
- deception,
- fake traffic,
- fake referrals,
- fake clicks,
- coercion,
- unauthorized access,
- unsupported professional claims,
- terms-of-service violation,
- self-payment,
- personal network advantage,
- external action in a mode that has not explicitly enabled it.

## Baseline Fallback

If no clean revenue opportunity is found, create a useful free artifact and attach a lawful opt-in revenue path.
