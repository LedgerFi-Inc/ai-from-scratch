import assert from 'node:assert/strict';
import test from 'node:test';
import { diffPayments } from '../src/reconcile.ts';

const remote = (id: string, status: string, dateLastUpdated: string) => ({ id, status, dateLastUpdated });
const local = (providerId: string, status: string, updatedAt: string) => ({ providerId, status, updatedAt });

test('flags a remote payment absent locally', () => {
  assert.deepEqual(diffPayments([remote('9', 'approved', '2026-09-07T00:00:00Z')], []), ['9']);
});

test('flags a status mismatch', () => {
  assert.deepEqual(
    diffPayments([remote('9', 'approved', '2026-09-07T00:00:00Z')], [local('9', 'pending', '2026-09-07T00:00:00Z')]),
    ['9']);
});

test('flags a newer dateLastUpdated', () => {
  assert.deepEqual(
    diffPayments([remote('9', 'approved', '2026-09-07T02:00:00Z')], [local('9', 'approved', '2026-09-07T01:00:00Z')]),
    ['9']);
});

test('does not flag an identical row', () => {
  assert.deepEqual(
    diffPayments([remote('9', 'approved', '2026-09-07T00:00:00Z')], [local('9', 'approved', '2026-09-07T00:00:00Z')]),
    []);
});

test('does not flag a local-only row (coupon grant, no Mercado Pago id)', () => {
  assert.deepEqual(
    diffPayments([], [local('coupon:ALXN100:4001', 'approved', '2026-09-07T00:00:00Z')]),
    []);
});
