import assert from 'node:assert/strict';
import test from 'node:test';
import { assessPayment } from '../src/assess.ts';
import type { AssessEnv, OrderFacts, PaymentFacts } from '../src/assess.ts';

const ENV: AssessEnv = { production: true, priceMinor: 39_900, currency: 'COP' };
const NOW = new Date('2026-09-07T12:00:00Z');
const EXPIRES = new Date('2026-09-08T12:00:00Z');

const payment = (over: Partial<PaymentFacts> = {}): PaymentFacts => ({
  id: 'pay-1', status: 'approved', amountMinor: 39_900, refundedMinor: 0, currency: 'COP',
  liveMode: true, dateCreated: NOW, dateApproved: NOW, userIdHint: 4001, orderKey: 'ord-1', ...over,
});

const order = (over: Partial<OrderFacts> = {}): OrderFacts => ({
  orderKey: 'ord-1', userId: 4001, expectedMinor: 39_900, currency: 'COP',
  consumedBy: null, expiresAt: EXPIRES, singleUse: true, ...over,
});

test('pending payments are eligible (eligibility is moot; they grant nothing)', () => {
  assert.deepEqual(assessPayment(payment({ status: 'pending', userIdHint: null, liveMode: false }), null, ENV),
    { eligible: true, reason: null, userId: null });
});

test('userIdHint null and no order is no_user', () => {
  assert.deepEqual(assessPayment(payment({ userIdHint: null, orderKey: null }), null, ENV),
    { eligible: false, reason: 'no_user', userId: null });
});

test('TEST-mode payment in production is test_mode, and vice versa', () => {
  assert.equal(assessPayment(payment({ liveMode: false }), order(), ENV).reason, 'test_mode');
  assert.equal(assessPayment(payment({ liveMode: true }), order(), { ...ENV, production: false }).reason, 'test_mode');
});

test('USD is refused whatever the amount', () => {
  assert.equal(assessPayment(payment({ currency: 'USD', amountMinor: 99_999 }), order(), ENV).reason, 'currency_mismatch');
  assert.equal(assessPayment(payment({ currency: 'USD', amountMinor: 39_900 }), null, ENV).reason, 'currency_mismatch');
});

test('an order belonging to a different userIdHint is order_user_mismatch', () => {
  assert.equal(assessPayment(payment({ userIdHint: 7 }), order({ userId: 4001 }), ENV).reason, 'order_user_mismatch');
});

test('a second approved payment against a consumed single-use order is refused; the same id is not', () => {
  const consumed = order({ consumedBy: 'pay-1' });
  assert.deepEqual(assessPayment(payment({ id: 'pay-1' }), consumed, ENV),
    { eligible: true, reason: null, userId: 4001 });
  assert.equal(assessPayment(payment({ id: 'pay-2' }), consumed, ENV).reason, 'order_consumed');
});

test('created after expiry (plus the 1 h grace) is created_after_expiry', () => {
  const late = new Date(EXPIRES.getTime() + 3_600_000 + 1);
  assert.equal(assessPayment(payment({ dateCreated: late }), order(), ENV).reason, 'created_after_expiry');
  const withinGrace = new Date(EXPIRES.getTime() + 3_600_000);
  assert.equal(assessPayment(payment({ dateCreated: withinGrace }), order(), ENV).eligible, true);
});

test('1.000 COP against a 39.900 order is amount_below_expected', () => {
  assert.equal(assessPayment(payment({ amountMinor: 1_000 }), order(), ENV).reason, 'amount_below_expected');
});

test('a coupon order passes at the discounted amount and fails below it', () => {
  const coupon = order({ expectedMinor: 27_930 });
  assert.equal(assessPayment(payment({ amountMinor: 27_930 }), coupon, ENV).eligible, true);
  assert.equal(assessPayment(payment({ amountMinor: 27_929 }), coupon, ENV).reason, 'amount_below_expected');
});

test('no order at all passes only at or above the current list price', () => {
  assert.equal(assessPayment(payment({ amountMinor: 39_900, orderKey: null }), null, ENV).eligible, true);
  assert.equal(assessPayment(payment({ amountMinor: 39_899, orderKey: null }), null, ENV).reason, 'no_order');
});

test('a singleUse:false subscription order accepts a second approved payment', () => {
  const sub = order({ singleUse: false, consumedBy: 'pay-1' });
  assert.deepEqual(assessPayment(payment({ id: 'pay-2' }), sub, ENV),
    { eligible: true, reason: null, userId: 4001 });
});

test('order.userId fills in when the payment has no userIdHint', () => {
  assert.deepEqual(assessPayment(payment({ userIdHint: null }), order(), ENV),
    { eligible: true, reason: null, userId: 4001 });
});
