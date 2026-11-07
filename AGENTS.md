# Working Agreements

Use GitHub as the durable project record. Start each task by reading the current
branch, open pull requests, related issues, README.md, and METHODOLOGY.md. Record
new source and verification in a branch and pull request; record missing inputs
and follow-up work in repository documentation or issues.

- Inspect existing code and follow established patterns before editing.
- Preserve unrelated local work. Use an isolated checkout when reconciling it.
- Use quotient and remainder explicitly in new arithmetic work.
- Keep credentials, payment details, ledgers, local outputs, browser profiles,
  downloaded toolchains, and third-party project folders outside commits.
- Run `python -m unittest discover -s tests` for source changes. The default
  `unittest discover` invocation does not discover this repository's tests.
- Verify a GitHub Actions run for the current PR commit before calling CI passed.
- Keep measured results distinct from reports inherited from another chat.
- Ask before destructive operations, public releases, or materially expanding
  scope. Do not infer deployment or payment authorization from passing CI.

Follow docs/GITHUB_WORKFLOW.md for commands, ownership, and migration status.
