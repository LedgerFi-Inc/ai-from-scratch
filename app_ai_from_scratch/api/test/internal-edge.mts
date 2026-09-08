import assert from 'node:assert/strict';
import { createServer } from 'node:http';

const port = await new Promise<number>((resolve, reject) => {
  const s = createServer(); s.once('error', reject);
  s.listen(0, '127.0.0.1', () => {
    const a = s.address();
    if (!a || typeof a === 'string') return reject(new Error('no port'));
    const p = a.port; s.close(() => resolve(p));
  });
});
process.env.PORT = String(port);
process.env.HOST = '127.0.0.1';
process.env.PAYMENTS_SECRET = process.env.PAYMENTS_SECRET || 'test-payments-secret-32-chars-min!!';
const API = `http://127.0.0.1:${port}`;
await import('../src/server.ts');
for (let i = 0; i < 60; i++) {
  try { if ((await fetch(`${API}/api/version`)).ok) break; } catch {}
  await new Promise((r) => setTimeout(r, 250));
}

const blocked = await fetch(`${API}/api/internal/entitlements`, {
  method: 'POST',
  headers: { 'content-type': 'application/json', 'cf-ray': 'test-ray', authorization: `Bearer ${process.env.PAYMENTS_SECRET}` },
  body: JSON.stringify({}),
});
assert.equal(blocked.status, 404);

const unauthorized = await fetch(`${API}/api/internal/entitlements`, {
  method: 'POST',
  headers: { 'content-type': 'application/json', authorization: 'Bearer wrong' },
  body: JSON.stringify({}),
});
assert.equal(unauthorized.status, 401);
console.log('internal-edge: cf-ray 404; bad bearer 401');
process.exit(0);
