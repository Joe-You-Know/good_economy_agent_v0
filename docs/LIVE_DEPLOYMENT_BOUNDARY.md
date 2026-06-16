# Live Deployment Boundary

## Current Live Capability

Good Economy Agent v0 is live-capable for **read-only discovery**:

- CourtListener case-law and citation checks,
- GitHub issue search for public-good/documentation/accessibility opportunities,
- earned-income runway generation from explicit bounty/paid-work/value-exchange signals,
- configurable OpenLaws search,
- local monitoring snapshots,
- local rate-limit accounting,
- local kill switch enforcement,
- non-revenue donation/sponsorship support URL validation.

## Deliberately Disabled

The agent cannot currently:

- publish externally,
- send outbound messages,
- cold-contact people,
- submit pull requests,
- create accounts,
- click ads,
- collect payment,
- create invoices,
- create subscriptions,
- spend economic money,
- provide legal, medical, financial, or compliance advice.

These are write actions and require a later reviewed mode.

## CourtListener Integration

CourtListener is used for legal-source grounding and citation checks, not legal advice. The default configured limits match CourtListener's baseline authenticated limits:

```text
5 requests per minute
50 requests per hour
125 requests per day
```

The citation lookup guardrail is intended to reduce hallucinated citations. It does not determine whether an action is legal.

## OpenLaws Integration

OpenLaws is configured by:

```text
OPENLAWS_API_BASE_URL
OPENLAWS_API_KEY
```

The adapter calls:

```text
GET {OPENLAWS_API_BASE_URL}/search?q=...&limit=...
```

If the actual OpenLaws API contract differs, update `agent/live_clients.py` rather than weakening the safety boundary.

## Payment and Support Integration

The agent validates these public non-revenue support links:

```text
DONATION_URL
SPONSORSHIP_URL
```

It may disclose valid links in local artifacts as support only. It cannot charge a card, create an invoice, create a subscription, or treat a support link or configured payment-provider key as revenue.

## Earned Income Integration

`live-discovery` may produce a local earned-income runway from public issue
search results. The runway is not permission to claim work, submit work, invoice,
or collect payment. A settled event counts only after `revenue-verify` validates
earned income, value exchange, consent, traceability, net-of-fees accounting, and
settlement evidence.

## Kill Switch

Create this file to stop live discovery:

```text
KILL_SWITCH
```

The live discovery runner checks this before network use.

## Rate Limits

Rate-limit state is stored at:

```text
data/rate_limits.json
```

The limiter uses rolling windows and records local request attempts. This is a local safety layer in addition to provider-side throttles.

## Monitoring

Run:

```powershell
py run_agent.py --config config.json --mode monitor
```

The monitor writes:

```text
data/monitoring_state.json
```

## Moral Boundary

Live autonomy is acceptable only when it increases or preserves adaptive agency. If a live path requires deception, spam, unwanted attention, fake engagement, platform abuse, unsupported professional claims, hidden fees, or privacy violations, it must be blocked.
