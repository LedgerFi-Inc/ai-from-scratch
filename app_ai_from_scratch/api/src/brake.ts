/**
 * Sliding-window rate-limit key and in-memory counter.
 * Same trade as the chat per-minute brake: in-memory, per replica.
 */

export function slidingWindowKey(prefix: string, id: string, windowMs: number, now = Date.now()): string {
  return `${prefix}:${id}:${Math.floor(now / windowMs)}`;
}

export function secondsToNextWindow(windowMs: number, now = Date.now()): number {
  const nextWindow = (Math.floor(now / windowMs) + 1) * windowMs;
  return Math.max(1, Math.ceil((nextWindow - now) / 1000));
}

export const memoryBrakeCounters = new Map<string, number>();

export interface BrakeResult {
  ok: boolean;
  retryAfterS: number;
  total: number;
}

export function countWindow(
  key: string,
  limit: number,
  windowMs: number,
  map = memoryBrakeCounters,
  now = Date.now(),
): BrakeResult {
  const current = (map.get(key) ?? 0) + 1;
  map.set(key, current);
  if (map.size > 10_000) {
    const currentBucket = Math.floor(now / windowMs);
    for (const [k] of map) {
      const bucket = Number(k.slice(k.lastIndexOf(':') + 1));
      if (!Number.isNaN(bucket) && bucket < currentBucket) map.delete(k);
    }
  }
  const retryAfterS = secondsToNextWindow(windowMs, now);
  if (current > limit) return { ok: false, retryAfterS, total: current };
  return { ok: true, retryAfterS, total: current };
}

export function clientIp(headers: Record<string, unknown>, fallback: string): string {
  const rawCf = headers['cf-connecting-ip'];
  const cf = Array.isArray(rawCf) ? rawCf[0] : rawCf;
  if (typeof cf === 'string' && cf.trim()) return cf.trim();
  const rawXff = headers['x-forwarded-for'];
  const xff = Array.isArray(rawXff) ? rawXff[0] : rawXff;
  const first = typeof xff === 'string' ? xff.split(',')[0]?.trim() : '';
  return first || fallback || '127.0.0.1';
}
