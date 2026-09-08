import assert from 'node:assert/strict';
import { clientIp, countWindow, secondsToNextWindow, slidingWindowKey } from '../src/brake.ts';

const now = 1_700_000_000_000;
assert.equal(slidingWindowKey('auth', '1.1.1.1', 60_000, now), `auth:1.1.1.1:${Math.floor(now / 60_000)}`);
assert.ok(secondsToNextWindow(60_000, now) >= 1);

const map = new Map<string, number>();
const key = slidingWindowKey('t', 'ip', 60_000, now);
for (let i = 0; i < 5; i++) {
  const r = countWindow(key, 5, 60_000, map, now);
  assert.equal(r.ok, true);
}
const sixth = countWindow(key, 5, 60_000, map, now);
assert.equal(sixth.ok, false);
assert.ok(sixth.retryAfterS >= 1);

assert.equal(clientIp({ 'cf-connecting-ip': ' 8.8.8.8 ' }, '1.1.1.1'), '8.8.8.8');
assert.equal(clientIp({ 'x-forwarded-for': '9.9.9.9, 10.0.0.1' }, '1.1.1.1'), '9.9.9.9');
assert.equal(clientIp({}, '1.1.1.1'), '1.1.1.1');
console.log('brake: sliding window and ip extraction ok');
