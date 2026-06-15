# Environment Setup

The project maintains its own `.env` file. Secret values must not be pasted into
chat, committed to git, or written to logs.

## Agent Modes

```powershell
py run_agent.py --config config.json --mode env-bootstrap
py run_agent.py --config config.json --mode env-report
py run_agent.py --config config.json --mode env-sync
```

`env-bootstrap` adds missing key names to `.env` without changing existing values.

`env-report` writes a redacted readiness report to:

```text
outputs/env_readiness_report.md
```

`env-sync` copies matching values from the current process environment into
`.env`, but does not overwrite existing non-blank values.

## Importing One-Time Tokens

When a provider shows a one-time token:

1. Copy the token in the browser.
2. Run the clipboard helper with the matching key:

```powershell
powershell -ExecutionPolicy Bypass -File tools/import_env_from_clipboard.ps1 -Key COURTLISTENER_TOKEN
```

The helper writes the value into `.env` and prints only a redacted confirmation.
Do not paste tokens into chat.

## Variables

| Variable | Purpose | Secret | Acquisition |
|---|---|---:|---|
| `OPENAI_API_KEY` | Optional model-assisted drafting | Yes | https://platform.openai.com/api-keys |
| `GITHUB_TOKEN` | Authenticated GitHub discovery and future repo actions | Yes | https://github.com/settings/personal-access-tokens/new |
| `COURTLISTENER_TOKEN` | CourtListener legal-source checks | Yes | https://www.courtlistener.com/profile/api-token/ |
| `OPENLAWS_API_BASE_URL` | OpenLaws API endpoint | No | Provider documentation |
| `OPENLAWS_API_KEY` | OpenLaws auth, if required | Yes | Provider account |
| `PAYMENT_PROVIDER_API_KEY` | Future payment-provider verification | Yes | Provider account |
| `DONATION_URL` | Voluntary opt-in donation path | No | Donation platform |
| `SPONSORSHIP_URL` | Voluntary opt-in sponsorship path | No | Sponsorship platform |

## GitHub Token Scope

For current read-only discovery, a GitHub token is optional.

For future work, prefer a fine-grained token:

- limited to selected repositories,
- minimum permissions needed for the chosen action,
- no organization-wide access unless explicitly necessary,
- no workflow/admin/security permissions by default.

Do not create a broad classic token for convenience.

## Payment Boundary

Payment variables do not enable charging in v0. The agent can validate donation
and sponsorship URLs, but cannot charge a card, create invoices, create
subscriptions, or move money.

## CourtListener Boundary

The CourtListener token is used for authenticated legal-source search and
citation checks. It is not a license to provide legal advice.
