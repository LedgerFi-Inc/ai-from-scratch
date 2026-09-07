# MVP readiness ledger — ai-from-scratch

Plan: `~/.claude/plans/audit-and-harden-ledgerfi-inc-ai-from-sc-jiggly-parrot.md`.
Branch `mvp-readiness/2026-09`, baseline commit `64b28e2`. Model routing and
delegation protocol: see `/Users/alpadev/Desktop/course/READINESS-SESSIONS.md`.

## Cycle 0 — baseline (done 2026-09-07)
- `pnpm verify`: 22/22 gates green (`docs/readiness/evidence/00-baseline-verify.log`).
- `pnpm --dir web i18n`: clean. `pnpm audit:passwords` local: 3 expected matches.
- Production: HTTP 530, Cloudflare Tunnel has no active connector, Mac uplink `en9` inactive. Owner action O1 open.
- Mercado Pago account (read-only, production token): merchant active (MCO), can sell. 18 payments total (4 approved, 14 rejected), 14 subscription preapprovals **all `pending`, none ever authorized** — no live subscribers exist to protect. One already-approved payment has no resolvable user link (confirms the orphan-payment gap is real, not theoretical). **Nothing approved since 2026-09-05** — `ONE_TIME_EXPIRES_FROM` can move to any deploy instant without stranding a buyer (O4 still needs the actual instant from the owner). Flag: approved amounts (18.000 / 263.300 / 104.703 / one 0-COP coupon) never match this product's price history (35.000/39.900) — confirm with the owner whether this Mercado Pago account is dedicated to this product or shared.
- CLI handshakes: Grok 4.6 and agy/Gemini-3.8-Flash-High both confirmed reachable headless.

## Cycle 1 — Track A (payments, Grok 4.6): MERGED, verified independently
Merged `a797247` into `mvp-readiness/2026-09`. Astra re-ran (not trusting the
transcript): `pnpm --dir payments check` exit 0, `pnpm --dir payments test`
57/57 pass exit 0 (re-run without piping through `tail`, per house rule 2 —
the first attempt lost the real exit code that way). Full `pnpm verify` still
22/22 after merge.

Delivered: `checkout_orders` table + `assessPayment` (no more grant on
`status==='approved'` alone — checks order, amount, currency, `live_mode`,
single-use expiry); webhook routing by `type` allow-list
(`subscription_authorized_payment` now processed through a shared
`processPaymentItem` function, `merchant_order` ignored instead of dying);
manifest fix (lowercase alphanumeric `data.id`, omit empty `request-id`, +60s
future-`ts` rejection); fail-closed config (`APP_USR-`/`TEST-` prefix +
production/https checks, capped webhook window); reconciliation
(`GET /v1/payments/search` diff + `POST /v1/admin/reconcile`,
`POST /v1/admin/redrive`); `/health` + `/v1/admin/payments` expose
`mode/queue/alerts`; `grantId`/`grantAmountMinor` for the thank-you page;
`(kind,provider_id)`-scoped entitlement lookup so one poison row can't block
another grant's revocation. Terms-acceptance check (`terms_required`) added
ahead of any DB write in `/v1/checkout`, including the 100%-coupon path.

Findings closed: P0-1, P0-5, P1-4 (partial: orphan visibility done; api-side
`/api/alerts` still Cycle 2/B), P1-12, P2-1 (payments half), P2-2, P2-3.

Known gap (disclosed by the implementer, confirmed by Astra):
`PAYMENTS_TEST_DATABASE_URL` was unset, so `test/db/store.test.ts`
(migrate-idempotence, concurrent `consumeOrder`, orphan-dead-once) did not run
against real Postgres. Carried forward as the `payments-db` verify gate
(Cycle 2/3, track C).

Safety confirmed: no file outside `payments/**` touched (one line in
`payments/test/meta.test.ts` to extend its own env-cleanup list — in scope);
`payments/.env` never read or modified; no `git push`; reflog shows only
local commits on the track branch.

## Cycle 3 — E2E, legal, CI, mobile (2026-09-07, Grok)
- Legal: `web/src/data/seller.ts` + `social.ts`; terms PQR section (lawyer O9);
  PDF copy is Spanish-only until an EN PDF exists; landing footer links terms.
- Playwright `web/e2e/journey.spec.ts`; gate `e2e-journey` fails closed if api
  health is down. `scripts/smoke-prod.sh`. CI job `verify-fast`.
- Compose API/web bind default `127.0.0.1`. Mobile: `docs/readiness/MOBILE.md`
  **NO-GO for revenue**.
- Committed cycle 1–2 as `94b13af`. This cycle is the follow-up commit.

## Cycle 1 — Track B (api/auth/web): IMPLEMENTED on main by Grok 4.6
agy was still in-progress on `aifs-cycle1-app`. Owner told Grok to do the
remaining plan on this session. Implemented on `mvp-readiness/2026-09` (not
the agy worktree). Independent `pnpm verify` not re-run as a full set in this
turn; focused tests: web unit, payments 57, api `questions-http`,
session-revocation, registration, brake, data `op` catalogue. Restarted host
`data` so `auth.register` accepts `consent_at`/`consent_version`.

## Priority ledger
| priority | finding | file:line | fix | test evidence | status | owner |
|---|---|---|---|---|---|---|
| P0 | payment→access with no order/amount/currency/live_mode check | `payments/src/server.ts:80-90` (pre-fix) | `assessPayment` + `checkout_orders` | `payments/test/assess.test.ts` (9 cases), re-run by Astra | **fixed, merged** | code |
| P0 | recurring/`merchant_order` webhooks misrouted, die after 8 retries | `payments/src/server.ts:232` (pre-fix) | `classifyWebhook` + `/authorized_payments/{id}` branch | `payments/test/webhook.test.ts` | **fixed, merged** | code |
| P0 | no DB backups; prod down; Pi fed by this Mac | `docker-compose.yml:642-651` | `scripts/backup.sh`+`restore.sh`+gate | — | not started | code + owner (O1, O7) |
| P0 | `ONE_TIME_EXPIRES_FROM` already past | `payments/src/price.ts:59` | move to deploy instant | MP search shows nothing approved since 09-05 | ready, needs O4 | code + owner |
| P0 | published admin passwords still live | prod DB | rotate | `pnpm audit:passwords` on prod | not verified (prod down) | owner (O2) |
| P1 | logout doesn't revoke | `auth/src/index.ts:133-136` | `{todos:true}` → `auth.revoke_session` | `api/test/session-revocation.mts` | dispatched to Track B | code |
| P1 | no per-IP rate limit on auth/register/checkout | `api/package.json` (none) | sliding-window brake | `api/test/{brake,auth-throttle}.mts` | dispatched to Track B | code |
| P1 | `PAYMENTS_SECRET` symmetric, `/api/internal/*` edge-reachable | `api/src/server.ts:1001-1005` | dual-accept + cf-header 404 | `api/test/internal-edge.mts` | payments half merged; api half dispatched to Track B | code + owner (O6) |
| P1 | landing page has no pixel, no `ia_attr` | `web/src/pages/index.astro` | `<MetaPixel/>` + client no_ads guard | `web/test/attribution.test.mts` | dispatched to Track B | code |
| P1 | no consent at registration | `auth/src/index.ts:138-154` | `acepta` + `consent_at/version` | `api/test/registration.mts` | dispatched to Track B | code + lawyer (O9) |
| P1 | account deletion keeps chat log | `messages/src/server.ts` | `DELETE /v1/turns` | — | Cycle 2 | code |
| P1 | recovery email never sent | `auth/src/index.ts:171-173` | Resend + fail-closed 503 | — | Cycle 2 | code + owner (O5) |
| P1 | chat spend uncapped by tokens; client picks model | `api/src/server.ts:493-495,722` | free lane + token caps | `api/test/chat-brake.mts` | dispatched to Track B | code |
| P1 | 6 gates skipped in CI | `.github/workflows/ci.yml` | `verify-fast` job | — | Cycle 2/C | code |
| P1 | no browser E2E | — | Playwright journey gate | — | Cycle 3 | code |
| P2 | `/pago/gracias` forges Purchase for any `?payment_id=` | `web/src/pages/pago/gracias.astro:20-23` | `grantId` check | — | payments half merged; web half dispatched to Track B | code |
| P2 | poison row blocks other grants | `payments/src/db.ts:375-388` (pre-fix) | scoped filter | `entitlement.test.ts` | **fixed, merged** | code |
| P2 | manifest not lowercased, future ts accepted | `payments/src/security.ts:25,31-33` (pre-fix) | fixed | `security.test.ts` (+3) | **fixed, merged** | code |
| P2 | no security headers | web/api | edge Transform Rule + middleware | — | Cycle 3 | code + owner (O6) |
| P2 | `ai/.../app.py:84` `!=` compare | one line | `hmac.compare_digest` | — | Cycle 2 | code |
| P2 | no `og:image`, no social links | `web/src/lib/seo.ts` | og.png + social config | — | Cycle 3 | code + owner (O10) |

## Owner actions — status
O1 uplink (open) · O2 rotate passwords (open) · O3 MP TEST creds (open — blocks sandbox matrix) · O4 deploy instant (open — code ready) · O5 Resend+DNS (open) · O6 monitor+Cloudflare rules (open) · O7 R2 bucket (open) · O8 Meta dataset (open) · O9 seller legal data (open) · O10 social URLs (open) · O11 store accounts (open) · O12 LedgerFi remote (open) · O13 JDK install (approved by "procede", not yet run — Cycle 3 mobile).
