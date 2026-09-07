import { test } from 'node:test';
import assert from 'node:assert/strict';
import { deriveEntitlement, deriveEntitlementFor, oneTimePeriodEnd } from '../src/entitlement.ts';
import { ONE_TIME_DAYS, ONE_TIME_EXPIRES_FROM } from '../src/price.ts';

const DAY = 86_400_000;
// Far enough after ONE_TIME_EXPIRES_FROM that "N days ago" never lands in the legacy era by accident.
const NOW = new Date('2026-12-01T12:00:00Z');
const CUTOFF = Date.parse(ONE_TIME_EXPIRES_FROM);
const daysAgo = (n: number): Date => new Date(NOW.getTime() - n * DAY);
const payment = (status: string, at: Date | null, id = 'pay-1') => ({ kind: 'payment' as const, id, status, at, seen: at ?? NOW });
const subscription = (status: string, at: Date | null, seen = NOW, id = 'sub-1') => ({ kind: 'subscription' as const, id, status, at, seen });

test('a payment approved before the cutoff never expires: it was sold as pago único', () => {
  const legacy = new Date(CUTOFF - DAY);
  assert.equal(oneTimePeriodEnd(legacy), null);
  assert.deepEqual(deriveEntitlement([payment('approved', legacy)], NOW), { active: true, periodEnd: null });
});

test('a payment approved after the cutoff buys exactly ONE_TIME_DAYS days', () => {
  const approved = daysAgo(3);
  const end = oneTimePeriodEnd(approved);
  assert.equal(end?.getTime(), approved.getTime() + ONE_TIME_DAYS * DAY);
  assert.deepEqual(deriveEntitlement([payment('approved', approved)], NOW),
    { active: true, periodEnd: new Date(approved.getTime() + ONE_TIME_DAYS * DAY).toISOString() });
});

test('a payment older than ONE_TIME_DAYS grants nothing', () => {
  assert.deepEqual(deriveEntitlement([payment('approved', daysAgo(ONE_TIME_DAYS + 1))], NOW), { active: false, periodEnd: null });
});

test('pending, rejected and refunded payments grant nothing', () => {
  for (const status of ['pending', 'rejected', 'refunded', 'in_process', 'unknown']) {
    assert.deepEqual(deriveEntitlement([payment(status, daysAgo(1))], NOW), { active: false, periodEnd: null }, status);
  }
});

test('an authorized subscription grants until its next payment date', () => {
  const next = new Date(NOW.getTime() + 20 * DAY);
  assert.deepEqual(deriveEntitlement([subscription('authorized', next)], NOW), { active: true, periodEnd: next.toISOString() });
});

test('an authorized subscription whose period already ended grants nothing', () => {
  assert.deepEqual(deriveEntitlement([subscription('authorized', daysAgo(1))], NOW), { active: false, periodEnd: null });
});

test('an authorized subscription without a date is bounded, not perpetual', () => {
  const seen = daysAgo(2);
  assert.deepEqual(deriveEntitlement([subscription('authorized', null, seen)], NOW),
    { active: true, periodEnd: new Date(seen.getTime() + ONE_TIME_DAYS * DAY).toISOString() });
  assert.deepEqual(deriveEntitlement([subscription('authorized', null, daysAgo(ONE_TIME_DAYS + 1))], NOW),
    { active: false, periodEnd: null });
});

test('cancelled and paused subscriptions grant nothing on their own', () => {
  for (const status of ['cancelled', 'paused', 'pending']) {
    assert.deepEqual(deriveEntitlement([subscription(status, new Date(NOW.getTime() + 10 * DAY))], NOW),
      { active: false, periodEnd: null }, status);
  }
});

test('the latest live end wins; a cancelled subscription keeps the month its last charge paid for', () => {
  // The recurring charge is also a payment row: cancelling the subscription leaves that
  // payment, so access runs to the end of the paid month, as the terms promise.
  const charge = daysAgo(10);
  const state = deriveEntitlement([subscription('cancelled', null), payment('approved', charge)], NOW);
  assert.deepEqual(state, { active: true, periodEnd: new Date(charge.getTime() + ONE_TIME_DAYS * DAY).toISOString() });
  const later = new Date(NOW.getTime() + 25 * DAY);
  assert.equal(deriveEntitlement([payment('approved', charge), subscription('authorized', later)], NOW).periodEnd, later.toISOString());
});

test('one legacy grant makes the whole access perpetual, whatever else expired', () => {
  assert.deepEqual(deriveEntitlement([payment('approved', daysAgo(90)), payment('approved', new Date(CUTOFF - 1))], NOW),
    { active: true, periodEnd: null });
});

test('an approved payment without a readable date is refused, never turned into a grant', () => {
  assert.throws(() => deriveEntitlement([payment('approved', null)], NOW), /approval date/);
  assert.throws(() => oneTimePeriodEnd(new Date('not a date')), /approval date/);
});

test('an unknown source kind is refused', () => {
  assert.throws(() => deriveEntitlement([{ kind: 'gift' as never, id: 'g-1', status: 'approved', at: NOW, seen: NOW }], NOW), /unknown entitlement source/);
});

test('each delivery reports its own grant: a cancelled subscription never carries the charge\'s end date', () => {
  // The api ORs the latest state per (source, external_id). Had the cancel delivery
  // sent the user aggregate, the subscription key would read "active until the
  // charge's end" and a refund of that charge could not close the access.
  const charge = daysAgo(10);
  const rows = [subscription('cancelled', null, NOW, 'sub-1'), payment('approved', charge, 'pay-1')];
  assert.deepEqual(deriveEntitlementFor(rows, 'subscription', 'sub-1', NOW), { active: false, periodEnd: null });
  assert.deepEqual(deriveEntitlementFor(rows, 'payment', 'pay-1', NOW),
    { active: true, periodEnd: new Date(charge.getTime() + ONE_TIME_DAYS * DAY).toISOString() });
  // The refund closes the payment key too; nothing is left for the api to OR.
  assert.deepEqual(deriveEntitlementFor([rows[0], payment('refunded', charge, 'pay-1')], 'payment', 'pay-1', NOW),
    { active: false, periodEnd: null });
  // A grant the delivery is not about is invisible to it.
  assert.deepEqual(deriveEntitlementFor(rows, 'payment', 'pay-2', NOW), { active: false, periodEnd: null });
  // The aggregate (what /perfil shows) still sees the whole access.
  assert.equal(deriveEntitlement(rows, NOW).active, true);
});
