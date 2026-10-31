# Security policy

Report vulnerabilities privately through GitHub's "Report a vulnerability" (Security tab) on this repository. Please do not open a public issue.

Scope worth knowing: model-written survey programs run only in a sandboxed subprocess (no network, temp dir, CPU/time limit, JSON in/out); see `docs/ARCHITECTURE.md`. Escapes of that sandbox, certificate forgery (station-chain signature) and key exposure are the highest-priority reports.
