import { createHash, createHmac, timingSafeEqual } from 'node:crypto';

export interface MercadoPagoSignatureInput {
  dataId: string;
  requestId: string;
  signature: string;
  secret: string;
  nowSeconds?: number;
  windowSeconds?: number;
}

const safeHexEqual = (left: string, right: string): boolean => {
  if (!/^[a-f\d]+$/i.test(left) || !/^[a-f\d]+$/i.test(right)) return false;
  const a = Buffer.from(left, 'hex');
  const b = Buffer.from(right, 'hex');
  return a.length === b.length && timingSafeEqual(a, b);
};

/**
 * Manifest Mercado Pago actually signed. Alphanumeric ids are lowercased
 * because the dashboard copies them mixed-case and the HMAC is case-sensitive;
 * numeric payment ids stay as-is (lowercasing digits is a no-op, but the
 * letter test keeps us from touching a value that never had case). An empty
 * request-id is omitted entirely: `id:…;request-id:;ts:…;` never matches the
 * bytes Mercado Pago hashed, and every such delivery 401'd as invalid.
 */
export function mercadoPagoManifest(dataId: string, requestId: string, ts: string): string {
  const id = /[a-z]/i.test(dataId) ? dataId.toLowerCase() : dataId;
  const parts = [`id:${id};`];
  if (requestId !== '') parts.push(`request-id:${requestId};`);
  parts.push(`ts:${ts};`);
  return parts.join('');
}

export function verifyMercadoPagoSignature(input: MercadoPagoSignatureInput):
  { ok: true; timestamp: number; eventKey: string } | { ok: false; reason: 'invalid' | 'expired' } {
  const parsed = Object.fromEntries(input.signature.split(',').map((part) => {
    const [key, ...rest] = part.trim().split('=');
    return [key, rest.join('=')];
  }));
  const manifest = mercadoPagoManifest(input.dataId, input.requestId, String(parsed.ts ?? ''));
  const expected = createHmac('sha256', input.secret).update(manifest).digest('hex');
  if (!parsed.v1 || !safeHexEqual(parsed.v1, expected)) return { ok: false, reason: 'invalid' };

  const raw = Number(parsed.ts);
  const timestamp = raw > 1e12 ? raw / 1000 : raw;
  const now = input.nowSeconds ?? Date.now() / 1000;
  // A `ts` more than 60 s in the future is a clock we refuse, not a generous
  // window: without this, Math.abs(age) treated "an hour from now" as "an hour
  // ago" and accepted a captured signature replayed after we rotated nothing.
  if (!Number.isFinite(timestamp) || timestamp - now > 60) {
    return { ok: false, reason: 'expired' };
  }
  const age = Math.abs(now - timestamp);
  if (age > (input.windowSeconds ?? 300)) {
    return { ok: false, reason: 'expired' };
  }
  // A provider resource may change status several times. The event identity is
  // the signed delivery, not the payment id; deduping forever by payment id
  // drops approved -> refunded and pending -> approved transitions.
  const eventKey = createHash('sha256')
    .update(`${input.dataId}\0${input.requestId}\0${parsed.ts}\0${parsed.v1}`)
    .digest('hex');
  return { ok: true, timestamp, eventKey };
}

export function serviceAuthorized(header: unknown, secret: string): boolean {
  const got = String(header ?? '').replace(/^Bearer\s+/i, '');
  const a = Buffer.from(got);
  const b = Buffer.from(secret);
  return a.length === b.length && timingSafeEqual(a, b);
}
