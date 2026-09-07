import assert from 'node:assert/strict';
import test from 'node:test';
import { classifyWebhook } from '../src/webhook.ts';

test('classifyWebhook maps the four real Mercado Pago types', () => {
  assert.equal(classifyWebhook('payment', '123'), 'payment');
  assert.equal(classifyWebhook('subscription_preapproval', 'uuid-like'), 'subscription');
  assert.equal(classifyWebhook('subscription_authorized_payment', '456'), 'authorized_payment');
});

test('merchant_order and other unknown types are ignored', () => {
  assert.equal(classifyWebhook('merchant_order', '123'), 'ignore');
  assert.equal(classifyWebhook('subscription_preapproval_plan', 'abc'), 'ignore');
  assert.equal(classifyWebhook('topic.unknown', '1'), 'ignore');
});

test('empty type keeps the numeric-id heuristic', () => {
  assert.equal(classifyWebhook('', '987654321'), 'payment');
  assert.equal(classifyWebhook('', 'a1b2-c3d4'), 'subscription');
});
