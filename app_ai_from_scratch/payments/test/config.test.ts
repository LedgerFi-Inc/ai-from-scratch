import assert from 'node:assert/strict';
import test from 'node:test';
import { loadConfig } from '../src/config.ts';

const BASE = {
  DATABASE_URL: 'postgres://x', PAYMENTS_SECRET: 'p'.repeat(40), ENTITLEMENTS_URL: 'http://api/entitlements',
};

const KEYS = [
  'META_PIXEL_ID', 'META_CAPI_TOKEN', 'META_TEST_EVENT_CODE',
  'MP_ACCESS_TOKEN', 'MP_ALLOW_LIVE_OUTSIDE_PRODUCTION', 'MP_WEBHOOK_SECRET', 'MP_PUBLIC_KEY',
  'NODE_ENV', 'WEBHOOK_PUBLIC_ORIGIN', 'WEBHOOK_WINDOW_SECONDS', 'PUBLIC_ORIGIN',
];

const withEnv = <T>(env: Record<string, string | undefined>, run: () => T): T => {
  const saved = { ...process.env };
  for (const key of KEYS) delete process.env[key];
  Object.assign(process.env, BASE, env);
  try { return run(); } finally { process.env = saved; }
};

test('production with a TEST- token throws', () => {
  assert.throws(() => withEnv({ NODE_ENV: 'production', MP_ACCESS_TOKEN: 'TEST-' + 'k'.repeat(40),
    PUBLIC_ORIGIN: 'https://aidesdecero.shop' }, loadConfig), /APP_USR-/);
});

test('production with an http:// publicOrigin throws', () => {
  assert.throws(() => withEnv({ NODE_ENV: 'production', MP_ACCESS_TOKEN: 'APP_USR-' + 'k'.repeat(40),
    PUBLIC_ORIGIN: 'http://aidesdecero.shop' }, loadConfig), /https:\/\//);
});

test('non-production APP_USR- token throws unless MP_ALLOW_LIVE_OUTSIDE_PRODUCTION=1', () => {
  assert.throws(() => withEnv({ NODE_ENV: 'development', MP_ACCESS_TOKEN: 'APP_USR-' + 'k'.repeat(40) }, loadConfig),
    /MP_ALLOW_LIVE_OUTSIDE_PRODUCTION/);
  const allowed = withEnv({
    NODE_ENV: 'development', MP_ACCESS_TOKEN: 'APP_USR-' + 'k'.repeat(40),
    MP_ALLOW_LIVE_OUTSIDE_PRODUCTION: '1',
  }, loadConfig);
  assert.equal(allowed.production, false);
  assert.ok(allowed.mpAccessToken?.startsWith('APP_USR-'));
});

test('a token starting with neither APP_USR- nor TEST- throws', () => {
  assert.throws(() => withEnv({ MP_ACCESS_TOKEN: 'APP_USR_WRONG-' + 'k'.repeat(40) }, loadConfig),
    /APP_USR- or TEST-/);
});

test('WEBHOOK_WINDOW_SECONDS=999999 is capped to 900', () => {
  const cfg = withEnv({ WEBHOOK_WINDOW_SECONDS: '999999' }, loadConfig);
  assert.equal(cfg.webhookWindowSeconds, 900);
});

test('WEBHOOK_PUBLIC_ORIGIN defaults to publicOrigin and can differ', () => {
  const def = withEnv({ PUBLIC_ORIGIN: 'https://shop.test' }, loadConfig);
  assert.equal(def.webhookPublicOrigin, 'https://shop.test');
  const split = withEnv({ PUBLIC_ORIGIN: 'https://shop.test', WEBHOOK_PUBLIC_ORIGIN: 'https://tunnel.test' }, loadConfig);
  assert.equal(split.publicOrigin, 'https://shop.test');
  assert.equal(split.webhookPublicOrigin, 'https://tunnel.test');
});
