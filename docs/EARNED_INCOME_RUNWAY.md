# Earned Income Runway

The agent may count revenue only when the money is earned income from a real
value exchange. Donation, patronage, sponsorship, grant, and gift support is
allowed to be disclosed as support, but it is not revenue.

## Read-Only Discovery

`live-discovery` writes:

```text
outputs/earned_income_runway.json
outputs/earned_income_runway.md
```

The runway ranks public candidates that show explicit earned-income signals,
such as bounty, paid work, reward, contract, marketplace sale, product sale, or
license fee language.

`asset-discovery` writes:

```text
outputs/asset_income_runway.json
outputs/asset_income_runway.md
```

This runway inventories configured local owned-asset paths and ranks product,
license, marketplace, or paid-service candidates. The current configured paths
include `C:\ConstructiveRT` and the Causal Impedance Model PDF folder. Discovery
is read-only and does not copy, publish, list, sell, or alter the source assets.

## Trading Boundary

Trading is a separate high-risk economic lane. The v0 default permits only
read-only market research, risk-policy drafting, backtests, and paper-trade
simulation. Real-money trading, brokerage connections, fund transfers, and live
orders are disabled unless a future reviewed mode explicitly authorizes them.

## Write Boundary

The runway does not claim work, submit pull requests, send messages, create
invoices, or collect payment. Those are external write actions and require a
separately reviewed mode.

## Receipt Validation

After a clean value exchange settles, validate the event before counting it:

```powershell
py run_agent.py --config config.json --mode revenue-verify --revenue-event path\to\settled_earned_revenue_event.json
```

The event must include earned income type, value exchange, traceability, consent,
an explicit income destination, net-of-fees reporting, and settlement evidence.
Support inflows and template placeholder events fail validation.

The local private destination file is:

```text
private/income_destination.json
```

It is intentionally gitignored. The current local destination is PayPal in USD.

## Supervised Work Selection

After `live-discovery`, run:

```powershell
py run_agent.py --config config.json --mode supervised-work
```

The agent chooses the cleanest current candidate and creates a local work
package, or refuses with reasons if no candidate survives the filters. External
submission remains a separate reviewed write action.

After `asset-discovery`, run:

```powershell
py run_agent.py --config config.json --mode asset-work
```

The agent prepares a local product/service package draft for the strongest
owned-asset candidate. Public listings, payment setup, outbound offers, or any
performance/legal/financial/security/scientific claims still require review and
fresh approval.
