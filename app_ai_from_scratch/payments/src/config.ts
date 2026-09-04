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
  mpAccessToken: string | null;
  mpWebhookSecret: string | null;
  mpPublicKey: string | null;
  publicOrigin: string;
  entitlementsUrl: string;
  webhookWindowSeconds: number;
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

export function loadConfig(): Config {
  return {
    host: process.env.HOST ?? '127.0.0.1',
    port: Number(process.env.PORT ?? 8785),
    databaseUrl: required('DATABASE_URL'),
    serviceSecret: secret('PAYMENTS_SECRET'),
    mpAccessToken: process.env.MP_ACCESS_TOKEN || null,
    mpWebhookSecret: process.env.MP_WEBHOOK_SECRET || null,
    mpPublicKey: process.env.MP_PUBLIC_KEY || null,
    publicOrigin: (process.env.PUBLIC_ORIGIN ?? 'http://localhost:4321').replace(/\/+$/, ''),
    entitlementsUrl: required('ENTITLEMENTS_URL'),
    webhookWindowSeconds: Math.max(30, Number(process.env.WEBHOOK_WINDOW_SECONDS ?? 300)),
    ...meta(),
  };
}
