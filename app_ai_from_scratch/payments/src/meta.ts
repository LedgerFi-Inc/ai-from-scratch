import { createHash } from 'node:crypto';
import { isIP } from 'node:net';

/**
 * Meta Conversions API (server-side Purchase events).
 *
 * The browser pixel alone loses every iOS buyer and every ad blocker. The only
 * point that KNOWS a sale happened is the Mercado Pago webhook, so the Purchase
 * event is sent from there, with the same event_id the thank-you page uses
 * (`mp:<payment id>`) so Meta deduplicates the two.
 *
 * Nothing in this module talks to the database or logs: it validates input,
 * shapes the event and posts it. That is what makes it testable without Meta.
 */

export interface CheckoutContext {
  fbp: string | null;
  fbc: string | null;
  clientIp: string | null;
  userAgent: string | null;
  sourceUrl: string | null;
  utm: Record<string, string>;
}

// Meta's own cookie formats. Anything else is a spoofed cookie and is dropped
// rather than forwarded: a malformed fbp lowers the whole event's match quality.
const FBP = /^fb\.[12]\.\d{1,16}\.\d{1,20}$/;
const FBC = /^fb\.[12]\.\d{1,16}\.[A-Za-z0-9_-]{1,400}$/;
const UTM_KEYS = ['source', 'medium', 'campaign', 'content', 'term'] as const;

const str = (value: unknown, max: number): string | null =>
  typeof value === 'string' && value.length > 0 && value.length <= max ? value : null;

/** Never trusts its input: the api forwards cookies and headers a browser chose. */
export function sanitizeContext(input: unknown): CheckoutContext {
  const raw = (input && typeof input === 'object' ? input : {}) as Record<string, unknown>;
  const fbp = str(raw.fbp, 64);
  const fbc = str(raw.fbc, 512);
  const ip = str(raw.clientIp, 64);
  const url = str(raw.sourceUrl, 512);
  const utmRaw = (raw.utm && typeof raw.utm === 'object' ? raw.utm : {}) as Record<string, unknown>;
  const utm: Record<string, string> = {};
  for (const key of UTM_KEYS) {
    const value = str(utmRaw[key], 200);
    if (value) utm[key] = value;
  }
  return {
    fbp: fbp && FBP.test(fbp) ? fbp : null,
    fbc: fbc && FBC.test(fbc) ? fbc : null,
    clientIp: ip && isIP(ip) ? ip : null,
    userAgent: str(raw.userAgent, 512),
    sourceUrl: url && /^https?:\/\//.test(url) ? url : null,
    utm,
  };
}

/** Meta wants SHA-256 over the trimmed, lower-cased value. */
export const hashPii = (value: string): string =>
  createHash('sha256').update(value.trim().toLowerCase()).digest('hex');

/** Shared with web/src/pages/pago/gracias.astro: same id, one counted purchase. */
export const purchaseEventId = (providerId: string): string => `mp:${providerId}`;

export interface MetaEvent {
  event_name: string;
  event_time: number;
  event_id: string;
  action_source: 'website';
  event_source_url: string;
  user_data: Record<string, unknown>;
  custom_data: Record<string, unknown>;
}

export interface PurchaseInput {
  providerId: string;
  /** Unix seconds. Clamped to [now - 7 days, now]: Meta refuses anything else. */
  eventTime: number;
  nowSeconds?: number;
  userId: number;
  email: string | null;
  amount: number;
  currency: string;
  context: CheckoutContext | null;
  fallbackUrl: string;
}

export function purchaseEvent(input: PurchaseInput): MetaEvent {
  const now = input.nowSeconds ?? Math.floor(Date.now() / 1000);
  const weekAgo = now - 7 * 24 * 3600;
  const time = Number.isFinite(input.eventTime) ? Math.min(now, Math.max(weekAgo, Math.floor(input.eventTime))) : now;
  const ctx = input.context;
  const userData: Record<string, unknown> = { external_id: [hashPii(String(input.userId))] };
  if (input.email && input.email.includes('@')) userData.em = [hashPii(input.email)];
  if (ctx?.clientIp) userData.client_ip_address = ctx.clientIp;
  if (ctx?.userAgent) userData.client_user_agent = ctx.userAgent;
  if (ctx?.fbp) userData.fbp = ctx.fbp;
  if (ctx?.fbc) userData.fbc = ctx.fbc;
  const customData: Record<string, unknown> = {
    currency: input.currency, value: input.amount,
    content_name: 'IA desde cero', content_type: 'product', content_ids: ['curso-v1'], num_items: 1,
  };
  if (ctx && Object.keys(ctx.utm).length) customData.utm = ctx.utm;
  return {
    event_name: 'Purchase', event_time: time, event_id: purchaseEventId(input.providerId),
    action_source: 'website', event_source_url: ctx?.sourceUrl ?? input.fallbackUrl,
    user_data: userData, custom_data: customData,
  };
}

export class MetaError extends Error {
  readonly status: number;
  readonly body: string;
  constructor(status: number, body: string) {
    super(`meta conversions api ${status}`);
    this.name = 'MetaError';
    this.status = status;
    this.body = body;
  }
}

export interface MetaReceipt { eventsReceived: number; fbtraceId: string | null }

// No parameter properties here: the service runs on `node --experimental-strip-types`,
// which refuses `constructor(private x)` (ERR_INVALID_TYPESCRIPT_SYNTAX). Plain fields.
export class MetaConversions {
  readonly pixelId: string;
  readonly url: string;
  private readonly token: string;
  private readonly testEventCode: string | null;
  private readonly fetchImpl: typeof fetch;

  constructor(pixelId: string, token: string, testEventCode: string | null, fetchImpl: typeof fetch = fetch, version = 'v21.0') {
    this.pixelId = pixelId;
    this.token = token;
    this.testEventCode = testEventCode;
    this.fetchImpl = fetchImpl;
    this.url = `https://graph.facebook.com/${version}/${pixelId}/events`;
  }

  async send(events: MetaEvent[]): Promise<MetaReceipt> {
    const body: Record<string, unknown> = { data: events, access_token: this.token };
    if (this.testEventCode) body.test_event_code = this.testEventCode;
    const response = await this.fetchImpl(this.url, {
      method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body),
    });
    // The token never reaches a log, whatever Meta echoes back.
    const text = (await response.text()).replaceAll(this.token, '[redacted]').slice(0, 500);
    if (!response.ok) throw new MetaError(response.status, text);
    let parsed: { events_received?: unknown; fbtrace_id?: unknown };
    try { parsed = JSON.parse(text); } catch { throw new MetaError(response.status, `unparseable body: ${text}`); }
    if (parsed.events_received !== events.length) {
      throw new MetaError(response.status, `events_received=${String(parsed.events_received)} expected ${events.length}`);
    }
    return { eventsReceived: events.length, fbtraceId: typeof parsed.fbtrace_id === 'string' ? parsed.fbtrace_id : null };
  }
}
