import assert from 'node:assert/strict';
import test from 'node:test';
import { Store } from '../../src/db.ts';

const dsn = process.env.PAYMENTS_TEST_DATABASE_URL;

if (!dsn) {
  console.error('payments/test/db/store.test.ts: SKIPPED (PAYMENTS_TEST_DATABASE_URL unset). Unproved: migrate() twice is a no-op; concurrent consumeOrder admits one winner; orphan approved payment lands dead with last_error starting orphan_payment:.');
} else {
  const store = new Store(dsn);

  test('migrate() called twice is a no-op', async () => {
    await store.migrate();
    await store.migrate();
  });

  test('two concurrent consumeOrder calls on the same order admit exactly one winner', async () => {
    await store.migrate();
    const orderKey = `race-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    await store.createOrder({
      orderKey, userId: 1, mode: 'one_time', expectedMinor: 39_900, currency: 'COP',
      expiresAt: new Date(Date.now() + 86_400_000),
    });
    const [a, b] = await Promise.all([
      store.consumeOrder(orderKey, 'pay-a'),
      store.consumeOrder(orderKey, 'pay-b'),
    ]);
    assert.equal([a, b].filter(Boolean).length, 1, 'exactly one consumeOrder must win');
    const row = await store.order(orderKey);
    assert.ok(row?.consumedBy === 'pay-a' || row?.consumedBy === 'pay-b');
    assert.equal(await store.consumeOrder(orderKey, row!.consumedBy!), true, 'same payment id re-delivered still wins');
  });

  test('an orphan approved payment lands dead exactly once with last_error starting orphan_payment:', async () => {
    await store.migrate();
    const providerId = `orphan-${Date.now()}`;
    await store.upsertPayment({
      providerId, userId: null, status: 'approved', amount: 39_900, currency: 'COP',
      raw: { id: providerId, status: 'approved' }, eligible: false, ineligibleReason: 'no_user', liveMode: true,
    });
    const key = `evt-${providerId}`;
    assert.equal(await store.recordEvent(key, providerId, 'payment'), true);
    const taken = await store.takeEvent();
    assert.ok(taken);
    assert.equal(taken.providerId, providerId);
    await store.failEvent(taken.id, 8, 'orphan_payment:' + providerId);
    const counts = await store.queueCounts();
    assert.ok(counts.dead >= 1);
    assert.ok(counts.orphanedApproved >= 1);
    const again = await store.pool.query(
      `SELECT state, last_error FROM payment_webhook_events WHERE id=$1`, [taken.id]);
    assert.equal(again.rows[0].state, 'dead');
    assert.match(String(again.rows[0].last_error), /^orphan_payment:/);
    await store.failEvent(taken.id, 8, 'orphan_payment:' + providerId);
    const still = await store.pool.query(
      `SELECT COUNT(*)::int AS n FROM payment_webhook_events WHERE provider_id=$1 AND state='dead'`, [providerId]);
    assert.equal(Number(still.rows[0].n), 1);
  });

  test.after(async () => { await store.close(); });
}
