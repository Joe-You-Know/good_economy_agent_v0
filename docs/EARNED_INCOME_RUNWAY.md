# Earned Income Runway

The agent may count revenue only when the money is earned income from a real
value exchange. Donation, patronage, sponsorship, grant, and gift support is
allowed to be disclosed as support, but it is not revenue.

## Read-Only Discovery

`live-discovery` now writes:

```text
outputs/earned_income_runway.json
outputs/earned_income_runway.md
```

The runway ranks public candidates that show explicit earned-income signals,
such as bounty, paid work, reward, contract, marketplace sale, product sale, or
license fee language.

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
