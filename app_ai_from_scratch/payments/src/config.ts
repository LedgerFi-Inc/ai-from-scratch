const placeholders = /changeme|cambia|example|placeholder|secret/i;

function secret(name: string, value = process.env[name]): string {
  if (!value || value.length < 32 || placeholders.test(value)) {
    throw new Error(`${name} must contain at least 32 non-placeholder characters`);
  }
  return value;
}

function required(name: string, value = process.env[name]): string {
  if (!value) throw new Error(`${name} is required`);
  return value;
}

export interface Config {
  host: string;
  port: number;
  databaseUrl: string;
  serviceSecret: string;
  /** Bearer sent to the course API entitlements callback. Falls back to PAYMENTS_SECRET. */
  entitlementsSecret: string;
  mpAccessToken: string | null;
  mpWebhookSecret: string | null;
  mpPublicKey: string | null;
  publicOrigin: string;
  /**
   * Origin used only for Mercado Pago `notification_url`. Distinct from
   * `publicOrigin` (buyer `back_url`s) so a sandbox tunnel can receive
   * webhooks without changing the URL the buyer sees.
   */
  webhookPublicOrigin: string;
  entitlementsUrl: string;
  webhookWindowSeconds: number;
  /** NODE_ENV === 'production'. Live tokens and http origins are refused when true. */
  production: boolean;
  /** Meta Conversions API. Both set or both unset: half a configuration is a misconfiguration. */
  metaPixelId: string | null;
  metaCapiToken: string | null;
  metaTestEventCode: string | null;
}

function meta(): Pick<Config, 'metaPixelId' | 'metaCapiToken' | 'metaTestEventCode'> {
  const pixelId = process.env.META_PIXEL_ID || null;
  const token = process.env.META_CAPI_TOKEN || null;
  if (!pixelId && !token) return { metaPixelId: null, metaCapiToken: null, metaTestEventCode: null };
  if (!pixelId || !token) throw new Error('META_PIXEL_ID and META_CAPI_TOKEN must be set together (or both unset)');
  if (!/^\d{6,20}$/.test(pixelId)) throw new Error('META_PIXEL_ID must be the numeric Meta dataset id');
  return { metaPixelId: pixelId, metaCapiToken: secret('META_CAPI_TOKEN', token),
    metaTestEventCode: process.env.META_TEST_EVENT_CODE || null };
}

/**
 * Mercado Pago tokens are either live (`APP_USR-`) or test (`TEST-`). Anything
 * else is a paste of the public key, a placeholder, or a truncated secret, and
 * would charge (or fail to charge) without anyone noticing the mix-up.
 */
function mpAccessToken(): string | null {
  const token = process.env.MP_ACCESS_TOKEN || null;
  if (!token) return null;
  if (!token.startsWith('APP_USR-') && !token.startsWith('TEST-')) {
    throw new Error('MP_ACCESS_TOKEN must start with APP_USR- or TEST-');
  }
  return token;
}

export function loadConfig(): Config {
  const production = process.env.NODE_ENV === 'production';
  const token = mpAccessToken();
  const publicOrigin = (process.env.PUBLIC_ORIGIN ?? 'http://localhost:4321').replace(/\/+$/, '');
  const webhookPublicOrigin = (process.env.WEBHOOK_PUBLIC_ORIGIN ?? publicOrigin).replace(/\/+$/, '');

  if (production) {
    if (!token || !token.startsWith('APP_USR-')) {
      throw new Error('production requires MP_ACCESS_TOKEN to start with APP_USR-');
    }
    if (!publicOrigin.startsWith('https://')) {
      throw new Error('production requires PUBLIC_ORIGIN to start with https://');
    }
  } else if (token?.startsWith('APP_USR-') && process.env.MP_ALLOW_LIVE_OUTSIDE_PRODUCTION !== '1') {
    throw new Error('APP_USR- tokens outside production require MP_ALLOW_LIVE_OUTSIDE_PRODUCTION=1');
  }

  return {
    host: process.env.HOST ?? '127.0.0.1',
    port: Number(process.env.PORT ?? 8785),
    databaseUrl: required('DATABASE_URL'),
    serviceSecret: secret('PAYMENTS_SECRET'),
    entitlementsSecret: process.env.ENTITLEMENTS_SECRET
      ? secret('ENTITLEMENTS_SECRET') : secret('PAYMENTS_SECRET'),
    mpAccessToken: token,
    mpWebhookSecret: process.env.MP_WEBHOOK_SECRET || null,
    mpPublicKey: process.env.MP_PUBLIC_KEY || null,
    publicOrigin,
    webhookPublicOrigin,
    entitlementsUrl: required('ENTITLEMENTS_URL'),
    // 900 s is the cap: a window of hours lets an attacker replay a captured
    // webhook long after the buyer left. Floor 30 so a typo of 0 does not
    // reject every in-flight delivery.
    webhookWindowSeconds: Math.min(900, Math.max(30, Number(process.env.WEBHOOK_WINDOW_SECONDS ?? 300))),
    production,
    ...meta(),
  };
}
