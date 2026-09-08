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
| P0 | no DB backups; prod down; Pi fed by this Mac | `docker-compose.yml:642-651` | `scripts/backup.sh`+`restore.sh`+gate | `backup-restore` gate green | **done in code** (verified 2026-09-08); prod/uplink still owner | code + owner (O1, O7) |
| P0 | `ONE_TIME_EXPIRES_FROM` already past | `payments/src/price.ts:59` | move to deploy instant | MP search shows nothing approved since 09-05 | **fixed 2026-09-08**: 2026-09-09T05:00:00Z, terms ES+EN moved with it | code + owner |
| P0 | published admin passwords still live | prod DB | rotate | `pnpm audit:passwords` on prod | not verified (prod down) | owner (O2) |
| P1 | logout doesn't revoke | `auth/src/index.ts:133-136` | `{todos:true}` → `auth.revoke_session` | `api/test/session-revocation.mts` | **verified present**: `auth/src/index.ts:136-141` | code |
| P1 | no per-IP rate limit on auth/register/checkout | `api/package.json` (none) | sliding-window brake | `brake.mts` only — **`auth-throttle.mts` DOES NOT EXIST** | **verified present**: `api/src/brake.ts` | code |
| P1 | `PAYMENTS_SECRET` symmetric, `/api/internal/*` edge-reachable | `api/src/server.ts:1001-1005` | dual-accept + cf-header 404 | `api/test/internal-edge.mts` | **verified present**: `api/src/server.ts:142-148` | code + owner (O6) |
| P1 | landing page has no pixel, no `ia_attr` | `web/src/pages/index.astro` | `<MetaPixel/>` + client no_ads guard | `web/test/attribution.test.mts` | **verified present**: `web/src/pages/index.astro:13` | code |
| P1 | no consent at registration | `auth/src/index.ts:138-154` | `acepta` + `consent_at/version` | `api/test/registration.mts` | **verified present**: `auth/src/index.ts:157` | code + lawyer (O9) |
| P1 | account deletion keeps chat log | `messages/src/server.ts` | `DELETE /v1/turns` | — | **done**: `messages/src/server.ts:29-35` | code |
| P1 | recovery email never sent | `auth/src/index.ts:171-173` | `api/src/mail.ts` (Resend, both-or-neither env) wired into `createAuth({mailer})` | `api/test/mail.mts` (7 cases), `pnpm --dir api check` exit 0, both re-run by Astra | **code done**; DNS not live (see below) | code done; owner (O5 — DNS records) |
| P1 | chat spend uncapped by tokens; client picks model | `api/src/server.ts:493-495,722` | free lane + token caps | `api/test/chat-brake.mts` (8 assertions, written 2026-09-08) | free lane **done** (`server.ts:810-811`); **token ceiling was decorative until 2026-09-08**, now enforced in `chatBrake` | code |
| P1 | 6 gates skipped in CI | `.github/workflows/ci.yml` | `verify-fast` job | job green as of 2026-09-08 | **done**; the job installed nothing until `pnpm run setup` fixed it | code |
| P1 | no browser E2E | — | Playwright journey gate | — | Cycle 3 | code |
| P2 | `/pago/gracias` forges Purchase for any `?payment_id=` | `web/src/pages/pago/gracias.astro:20-23` | `grantId` check | — | **verified present**: `web/src/pages/pago/gracias.astro:21` | code |
| P2 | poison row blocks other grants | `payments/src/db.ts:375-388` (pre-fix) | scoped filter | `entitlement.test.ts` | **fixed, merged** | code |
| P2 | manifest not lowercased, future ts accepted | `payments/src/security.ts:25,31-33` (pre-fix) | fixed | `security.test.ts` (+3) | **fixed, merged** | code |
| P2 | no security headers | web/api | edge Transform Rule + middleware | — | Cycle 3 | code + owner (O6) |
| P2 | `ai/.../app.py:84` `!=` compare | one line | `hmac.compare_digest` | — | **done**: `ai/src/course_ai/app.py:85` | code |
| P2 | no `og:image`, no social links | `web/src/lib/seo.ts` | og.png + social config | — | Cycle 3 | code + owner (O10) |

## Cycle 2 follow-up — mail (2026-09-07, Astra)
Resend MCP connected (OAuth, plugin `resend`); domain `aifromscratch.shop`
already existed in the Resend account (id `cf070a95-…`, region `sa-east-1`,
sending enabled, receiving disabled, status `not_started` — not created by
this session). `api/src/mail.ts` added: `Mailer` interface + `resendMailer`
(plain `fetch` to `api.resend.com/emails`, 10s timeout, no new dependency);
`loadMailer()` reads `RESEND_API_KEY`+`MAIL_FROM`, both-or-neither, throws at
boot on a half-set pair or a malformed key/address (mirrors
`payments/src/config.ts`'s `meta()` pattern) — never silently degrades.
Wired into `api/src/server.ts` → `createAuth({..., mailer})`; the existing
fail-closed 503 (`correo_no_configurado`) and dev link-log in
`auth/src/index.ts:164-192` are unchanged and now actually get a real mailer
in production once the env vars are set. `.env.example` documents the two
vars, still empty (no forgeable default). Tests: `api/test/mail.mts` (7
cases: both-unset no-op, each half-set throws, bad prefix throws, bad email
throws, real POST shape asserted against a stubbed `fetch`, non-2xx response
rejects). Verified by Astra: `pnpm --dir api check` exit 0 (0 new type
errors), `node --experimental-strip-types api/test/mail.mts` exit 0, 7/7.
Added to `api/package.json`'s `test:direct` chain.

**Not done, and not mine to do**: DNS. `dig NS aifromscratch.shop` confirms
Cloudflare (`paislee`/`dakota.ns.cloudflare.com`) is authoritative — Hostinger's
DNS panel for this domain is stale and has zero live effect (checked: its only
records are a bare `A @` and `CNAME www`, unrelated to the tunnel). No
Cloudflare MCP/API access this session, so the 3 records Resend requires
(DKIM TXT `resend._domainkey`, MX+TXT `send` for SPF/return-path) were handed
to the owner in chat, not written. `verify-domain` not yet triggered — do
that after the owner confirms the records are live.

## Owner actions — status
O1 uplink (open) · O2 rotate passwords (open) · O3 MP TEST creds (open — blocks sandbox matrix) · O4 deploy instant (open — code ready) · O5 Resend+DNS (**code done**; DNS records identified, owner must add them on Cloudflare — see Cycle 2 follow-up above) · O6 monitor+Cloudflare rules (open) · O7 R2 bucket (open) · O8 Meta dataset (open) · O9 seller legal data (open) · O10 social URLs (open) · O11 store accounts (open) · O12 LedgerFi remote (open) · O13 JDK install (approved by "procede", not yet run — Cycle 3 mobile).

## Cycle 4 — Astra verification pass (2026-09-08)

The ledger was audited against the code rather than against the transcripts that
wrote it. **The ledger was wrong in the direction that costs money: it
under-reported completion.** A readiness register that says "not started" about
work already merged makes someone redo it, or holds a launch that is ready.

**Marked open, actually done** (verified by reading the code, not the commit
message):

| ledger said | reality |
|---|---|
| P0 no DB backups — *not started* | `scripts/backup.sh`, `scripts/restore.sh` and the `backup-restore` gate (`scripts/backup-drill.sh`, `verify.mjs:300`) all exist |
| P1 account deletion keeps chat log — *Cycle 2* | `messages/src/server.ts:29-35`, `DELETE /v1/turns` → `store.purge(userId)` |
| P2 `ai/.../app.py:84` `!=` compare — *Cycle 2* | `ai/src/course_ai/app.py:85` already uses `hmac.compare_digest` |
| P1 6 gates skipped in CI — *Cycle 2/C* | the `verify-fast` job exists; it was BROKEN, see below |

**Marked "dispatched to Track B", verified present:** logout revocation
(`auth/src/index.ts:136-141`, `body?.todos === true` → `auth.revoke_session`) ·
the sliding-window brake (`api/src/brake.ts`) · the edge 404 on internal routes
(`api/src/server.ts:142-148`, `cf-ray` present + `/api/(interno|internal)` → 404)
· `<MetaPixel/>` on the landing (`web/src/pages/index.astro:13`) · registration
consent (`auth/src/index.ts:157`) · `grantId` on the thank-you page
(`web/src/pages/pago/gracias.astro:21`).

**P1 "chat spend uncapped by tokens; client picks model" — fixed, and the ledger
undersold it.** `api/src/server.ts:525-531` declares six ceilings —
`CHAT_PER_MINUTE` 6, `CHAT_DAY_CAP` 120 (free 20), `CHAT_GLOBAL_DAY_CAP` 4000
(free 800), `CHAT_TOKENS_DAY` 200 000 per person, `CHAT_TOKENS_DAY_GLOBAL`
5 000 000 — enforced at `:821`. The free lane is real: `:810-811` forces
`proveedor: undefined` and `esfuerzo: 'bajo'` for an unpaid user.

### Two things this pass actually found

1. **The token ceiling did not exist. It was a log line.** `CHAT_TOKENS_DAY`
   (200 000/person) and `CHAT_TOKENS_DAY_GLOBAL` (5 000 000) were declared at
   `server.ts:530-531`, incremented at `:819-820` AFTER the billed `talkToAi`
   call, compared once, and the only consequence of exceeding either was
   `app.log.warn`. `grep` proves it: those two keys are written in two places
   and read nowhere else, and `chatBrake` — the only gate before the billed call
   — never looked at them. The sole binding ceiling was the question COUNT.
   Concretely: a paying account sending its permitted 120 questions a day at
   `esfuerzo: 'alto'` on the priciest provider, at ~30 000 tokens a turn, spends
   3 600 000 tokens — **eighteen times the per-person ceiling the code claimed
   to enforce** — and two such accounts clear the platform ceiling. Nothing
   stopped either.

   **Fixed.** The decision moved to `api/src/chat-ceiling.ts` as a pure function
   and `chatBrake` now reads both counters with `readCounter` (read, never
   incremented) BEFORE `talkToAi` and returns 429 `tokens_dia` /
   `tokens_dia_global`. The gate is "already over the line", because a request's
   cost is unknowable before it runs; the overshoot is bounded by one turn.

   **Why it hid for months:** the logic lived inline in `server.ts`, which calls
   `app.listen` at import, so testing it meant booting Fastify, a session, the
   ai service and Postgres. The ledger cited `api/test/chat-brake.mts` as its
   evidence and that file did not exist. Citing a test that is not there is
   worse than citing none: it stops anyone from looking. The file exists now,
   8 assertions, wired into `test:direct`.

   **Honest limit of that test:** it covers the pure decision, including the
   `>` versus `>=` boundary and own-before-global ordering. It does NOT prove
   `chatBrake` calls it, because `chatBrake` is still unreachable from a test.
   Extracting `chatBrake` and `minuteBucket` out of `server.ts` — the same move
   `api/src/brake.ts` already made — is the follow-up.

   `api/test/auth-throttle.mts` is also cited and also does not exist; `brake.mts`
   covers the sliding window and IP extraction only.

2. **`verify-fast` never ran anything.** The job's install step was
   `pnpm setup`, and `setup` is a BUILT-IN pnpm command that shadows the script
   of the same name — so it configured pnpm's own home directory, installed
   nothing, exited 0, and the gates failed three steps later with
   `tsgo: not found`. `README.md`, `docs/PLATFORM.md` and the workspace
   `CLAUDE.md` taught the same broken command. Fixed to `pnpm run setup`.
   A second failure hid behind it: `web-types` runs tsgo directly and needs
   `.astro/types.d.ts`, which `astro sync` generates and which is not committed —
   six `Property 'env' does not exist on type 'ImportMeta'`. It passed locally
   only because `.astro/` survives from `pnpm dev`. Both fixed in `ci.yml`.

### Done this pass
- `ONE_TIME_EXPIRES_FROM` moved `2026-09-05` → `2026-09-09T05:00:00Z`. Its own
  comment forbids a date before the deploy. Safe by the Cycle 0 measurement
  above ("Nothing approved since 2026-09-05"). ES and EN terms moved with it,
  because the terms are the contract.
- Price 39.990 across the three constants and ~85 copy strings; `check-price.mjs`
  gained STALE rows for 38.899 in both notations.
- `pnpm verify` **27/27, exit 0**, with the api up on :8787 so `e2e-journey` ran
  instead of failing closed. Exit code read directly, not through a pipe.

### Still open, and why
- **Production is a 2026-09-01 build.** Verified by fetching the live site:
  `/` serves `SUSCRIBIRME · $35.000/MES` and `ANTES $99.999/MES` — the fictitious
  anchor deleted on 2026-09-05 because it is what SIC sanctions under Ley 1480 —
  and `/terminos` still describes a monthly subscription. `/api/payments/estado`
  answers `{"disponible":true}`, so checkout is live. PR #19 is green and
  unmerged; nothing reaches production until it lands.
- **`chatBrake` is still not reachable from a test.** Its token half is covered
  through the extracted pure function; the wiring is not. Extract it from
  `server.ts` the way `brake.ts` was extracted.
- Owner actions unchanged: O1, O2, O3, O5 (DNS), O6, O7, O8, O9, O10, O11, O12.
