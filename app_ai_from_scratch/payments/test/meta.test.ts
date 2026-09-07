import assert from 'node:assert/strict';
import test from 'node:test';
import { loadConfig } from '../src/config.ts';
import { MetaConversions, MetaError, hashPii, purchaseEvent, purchaseEventId, sanitizeContext } from '../src/meta.ts';

const NOW = 1_800_000_000;

test('sanitizeContext keeps Meta-shaped cookies and drops everything spoofed', () => {
  const clean = sanitizeContext({
    fbp: 'fb.1.1700000000000.1234567890', fbc: 'fb.1.1700000000000.IwAR2abc_DEF-ghi',
    clientIp: '181.55.10.9', userAgent: 'Mozilla/5.0', sourceUrl: 'https://aidesdecero.shop/pago',
    utm: { source: 'meta', medium: 'paid', campaign: 'cartagena-v8', content: 'gancho-a', term: 'x', bogus: 'no', landing: '/' },
  });
  assert.equal(clean.fbp, 'fb.1.1700000000000.1234567890');
  assert.equal(clean.fbc, 'fb.1.1700000000000.IwAR2abc_DEF-ghi');
  assert.equal(clean.clientIp, '181.55.10.9');
  assert.deepEqual(clean.utm, { source: 'meta', medium: 'paid', campaign: 'cartagena-v8', content: 'gancho-a', term: 'x' });

  const dirty = sanitizeContext({
    fbp: '<script>', fbc: 'fb.1.x.y z', clientIp: '999.1.1.1', userAgent: 'x'.repeat(600),
    sourceUrl: 'javascript:alert(1)', utm: { source: 'y'.repeat(201) },
  });
  assert.deepEqual(dirty, { fbp: null, fbc: null, clientIp: null, userAgent: null, sourceUrl: null, utm: {} });
  assert.deepEqual(sanitizeContext(undefined).utm, {});
  assert.deepEqual(sanitizeContext('garbage').utm, {});
});

test('hashPii normalises case and whitespace the way Meta matches', () => {
  assert.equal(hashPii('  Ana@Correo.CO '), hashPii('ana@correo.co'));
  assert.match(hashPii('ana@correo.co'), /^[0-9a-f]{64}$/);
});

test('purchaseEvent never carries raw PII and shares the browser event id', () => {
  const event = purchaseEvent({
    providerId: '123456789', eventTime: NOW - 60, nowSeconds: NOW, userId: 4001, email: 'Ana@Correo.co',
    amount: 39_900, currency: 'COP', fallbackUrl: 'https://aidesdecero.shop/pago',
    context: { fbp: 'fb.1.1.2', fbc: null, clientIp: '181.55.10.9', userAgent: 'UA', sourceUrl: 'https://aidesdecero.shop/pago?x=1',
      utm: { source: 'meta', campaign: 'cartagena-v8' } },
  });
  const json = JSON.stringify(event);
  assert.equal(event.event_id, purchaseEventId('123456789'));
  assert.equal(event.event_id, 'mp:123456789');
  assert.equal(event.event_time, NOW - 60);
  assert.equal(event.action_source, 'website');
  assert.equal(event.event_source_url, 'https://aidesdecero.shop/pago?x=1');
  assert.ok(!json.includes('Ana@'), 'raw email leaked');
  assert.ok(!json.includes('ana@correo.co'), 'raw email leaked');
  assert.ok(!json.includes('"4001"'), 'raw user id leaked');
  assert.deepEqual(event.user_data.em, [hashPii('ana@correo.co')]);
  assert.deepEqual(event.user_data.external_id, [hashPii('4001')]);
  assert.equal(event.user_data.client_ip_address, '181.55.10.9');
  assert.equal(event.user_data.fbp, 'fb.1.1.2');
  assert.equal('fbc' in event.user_data, false);
  assert.equal(event.custom_data.value, 39_900);
  assert.equal(event.custom_data.currency, 'COP');
  assert.deepEqual(event.custom_data.utm, { source: 'meta', campaign: 'cartagena-v8' });
});

test('purchaseEvent clamps event_time into the window Meta accepts', () => {
  const base = { providerId: '1', userId: 1, email: null, amount: 1, currency: 'COP', context: null, fallbackUrl: 'https://x.test/pago', nowSeconds: NOW };
  assert.equal(purchaseEvent({ ...base, eventTime: NOW + 3600 }).event_time, NOW, 'future is clamped to now');
  assert.equal(purchaseEvent({ ...base, eventTime: NOW - 30 * 86_400 }).event_time, NOW - 7 * 86_400, 'older than 7 days is clamped');
  assert.equal(purchaseEvent({ ...base, eventTime: Number.NaN }).event_time, NOW, 'unparseable date falls back to now');
  const noContext = purchaseEvent({ ...base, eventTime: NOW });
  assert.equal(noContext.event_source_url, 'https://x.test/pago');
  assert.equal('em' in noContext.user_data, false);
});

test('MetaConversions posts to the dataset endpoint with the token in the body, never in the URL', async () => {
  const calls: { url: string; body: Record<string, unknown> }[] = [];
  const fetchImpl = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), body: JSON.parse(String(init?.body)) });
    return new Response(JSON.stringify({ events_received: 1, fbtrace_id: 'AbC' }), { status: 200 });
  }) as typeof fetch;
  const token = 'EAAB' + 'k'.repeat(60);
  const meta = new MetaConversions('123456789012345', token, 'TEST42', fetchImpl);
  const receipt = await meta.send([purchaseEvent({ providerId: '9', eventTime: NOW, nowSeconds: NOW, userId: 1, email: null,
    amount: 1, currency: 'COP', context: null, fallbackUrl: 'https://x.test/pago' })]);
  assert.deepEqual(receipt, { eventsReceived: 1, fbtraceId: 'AbC' });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, 'https://graph.facebook.com/v21.0/123456789012345/events');
  assert.equal(calls[0].body.access_token, token);
  assert.equal(calls[0].body.test_event_code, 'TEST42');
  assert.equal((calls[0].body.data as unknown[]).length, 1);
});

test('MetaConversions surfaces a rejection with the status and a redacted body', async () => {
  const token = 'EAAB' + 'k'.repeat(60);
  const rejecting = (async () => new Response(`{"error":{"message":"Invalid OAuth ${token}","code":190}}`, { status: 400 })) as typeof fetch;
  const meta = new MetaConversions('123456789012345', token, null, rejecting);
  const event = purchaseEvent({ providerId: '9', eventTime: NOW, nowSeconds: NOW, userId: 1, email: null, amount: 1, currency: 'COP', context: null, fallbackUrl: 'https://x.test/pago' });
  await assert.rejects(meta.send([event]), (error: unknown) => {
    assert.ok(error instanceof MetaError);
    assert.equal(error.status, 400);
    assert.ok(error.body.includes('[redacted]'), 'token must be redacted');
    assert.ok(!error.body.includes(token), 'token leaked into the error body');
    return true;
  });

  const shortCount = (async () => new Response(JSON.stringify({ events_received: 0 }), { status: 200 })) as typeof fetch;
  await assert.rejects(new MetaConversions('123456789012345', token, null, shortCount).send([event]), (error: unknown) =>
    error instanceof MetaError && /events_received=0 expected 1/.test(error.body));
});

test('loadConfig refuses half a Meta configuration and a non-numeric dataset id', () => {
  const base = {
    DATABASE_URL: 'postgres://x', PAYMENTS_SECRET: 'p'.repeat(40), ENTITLEMENTS_URL: 'http://api/entitlements',
  };
  const withEnv = <T>(env: Record<string, string | undefined>, run: () => T): T => {
    const saved = { ...process.env };
    for (const key of ['META_PIXEL_ID', 'META_CAPI_TOKEN', 'META_TEST_EVENT_CODE']) delete process.env[key];
    Object.assign(process.env, base, env);
    try { return run(); } finally { process.env = saved; }
  };
  const off = withEnv({}, loadConfig);
  assert.equal(off.metaPixelId, null);
  assert.equal(off.metaCapiToken, null);
  assert.throws(() => withEnv({ META_PIXEL_ID: '123456789012345' }, loadConfig), /set together/);
  assert.throws(() => withEnv({ META_CAPI_TOKEN: 'EAAB' + 'k'.repeat(60) }, loadConfig), /set together/);
  assert.throws(() => withEnv({ META_PIXEL_ID: 'pixel-abc', META_CAPI_TOKEN: 'EAAB' + 'k'.repeat(60) }, loadConfig), /numeric/);
  assert.throws(() => withEnv({ META_PIXEL_ID: '123456789012345', META_CAPI_TOKEN: 'short' }, loadConfig), /32 non-placeholder/);
  const on = withEnv({ META_PIXEL_ID: '123456789012345', META_CAPI_TOKEN: 'EAAB' + 'k'.repeat(60), META_TEST_EVENT_CODE: 'TEST1' }, loadConfig);
  assert.equal(on.metaPixelId, '123456789012345');
  assert.equal(on.metaTestEventCode, 'TEST1');
});
