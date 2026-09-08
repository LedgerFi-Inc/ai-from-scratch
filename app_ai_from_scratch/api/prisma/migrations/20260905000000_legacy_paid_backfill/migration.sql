-- Legacy buyers get an explicit, perpetual entitlement event.
--
-- Until 2026-08-24 the api set users.paid = 1 directly when Mercado Pago
-- approved a payment; entitlement_events was created empty and never
-- backfilled. Those accounts have paid = 1 and no event, which two things read
-- as "no grant": the lapse sweep (now guarded to skip accounts with no events)
-- and any future derivation that trusts the table over the cache.
--
-- One row per such account, period_end NULL = never expires: they bought the
-- course as «pago único» and keep what they paid for. Data only, no schema
-- change, so `db:drift` stays clean. Idempotent through the event_key UNIQUE.
--
-- Accounts seeded AFTER migrations (api/src/seed.ts, dev demo users) are not
-- covered here and do not need to be: the sweep leaves any account without
-- events alone.
INSERT INTO "entitlement_events" ("event_key", "user_id", "active", "source", "external_id", "occurred_at", "period_end")
SELECT 'legacy:' || u."id", u."id", true, 'legacy', 'paid-before-entitlement-events', now(), NULL
  FROM "users" u
 WHERE u."paid" = 1
   AND NOT EXISTS (SELECT 1 FROM "entitlement_events" e WHERE e."user_id" = u."id")
ON CONFLICT ("event_key") DO NOTHING;
