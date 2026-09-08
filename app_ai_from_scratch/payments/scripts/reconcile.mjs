#!/usr/bin/env node
/**
 * One-shot reconcile against the running payments service.
 *
 * WHY A SCRIPT AND NOT `curl` IN THE RUNBOOK. A non-2xx from the admin
 * route used to be easy to miss: `curl` exits 0 on HTTP 500 unless -f is
 * passed, and a forgotten -f is how a missed webhook stayed missed. This
 * exits 1 on any fetch error or non-2xx. It does not read payments/.env —
 * pass PAYMENTS_SECRET and PAYMENTS_URL in the environment you already have.
 */
const base = (process.env.PAYMENTS_URL || 'http://127.0.0.1:8785').replace(/\/+$/, '');
const secret = process.env.PAYMENTS_SECRET;
if (!secret) {
  console.error('reconcile: PAYMENTS_SECRET is required');
  process.exit(1);
}

let response;
try {
  response = await fetch(`${base}/v1/admin/reconcile`, {
    method: 'POST',
    headers: { authorization: `Bearer ${secret}`, 'content-type': 'application/json' },
  });
} catch (error) {
  console.error(`reconcile: fetch failed: ${error}`);
  process.exit(1);
}

const text = await response.text();
if (response.status < 200 || response.status >= 300) {
  console.error(`reconcile: HTTP ${response.status}: ${text.slice(0, 400)}`);
  process.exit(1);
}
console.log(text);
