# Readiness audit — resumable state

Plan: `~/.claude/plans/audit-and-harden-ledgerfi-inc-ai-from-sc-jiggly-parrot.md` (approved 2026-09-07, "procede").
Branch: `mvp-readiness/2026-09` · baseline commit `64b28e2` (owner's dirty tree, unchanged).

## Cycle 0 — baseline (in progress, 2026-09-07)

| step | status | evidence |
|---|---|---|
| baseline commit + branch | done | `git log -1 64b28e2` |
| `pnpm verify` (22 gates) | running | `docs/readiness/evidence/00-baseline-verify.log` |
| `web i18n`, `audit:passwords` (local) | running | `00-baseline-i18n.log`, `00-baseline-audit-passwords-local.log` |
| production inventory (Pi, read-only SSH) | BLOCKED — site 530, uplink down; owner action O1 | — |
| Mercado Pago read-only account check | pending | aggregates only in `00-mp-account.json` |
| CLI handshakes (grok, agy) | running | `00-handshake-grok.json`, `00-handshake-agy.json` |
| `docs/MVP-READINESS.md` ledger | pending | — |

## Open owner actions
O1 Pi uplink · O2 rotate published passwords · O3 Mercado Pago TEST credentials + webhook config · O4 deploy instant for `ONE_TIME_EXPIRES_FROM` · O5 Resend + DNS · O6 monitor + Cloudflare rules · O7 R2 bucket · O8 Meta dataset · O9 seller legal data · O10 social URLs · O11 store accounts · O12 LedgerFi remote · O13 JDK approval (granted by "procede").

## Next
Cycle 1: briefs `01-A.md` (payments → Grok), `01-B.md` (api/auth/web → agy), `01-C.md` (verify gate + compose/keys/release → agy).
