import Fastify from 'fastify';
import { loadConfig } from './config.ts';
import { Store } from './db.ts';
import { MercadoPago, MercadoPagoError } from './mercadopago.ts';
import { MetaConversions, MetaError, purchaseEvent, sanitizeContext } from './meta.ts';
import { CURRENCY } from './price.ts';
import { serviceAuthorized, verifyMercadoPagoSignature } from './security.ts';

const config = loadConfig();
const store = new Store(config.databaseUrl);
const provider = new MercadoPago(config);
// null = not configured. Purchases still grant access; they just never reach Meta.
const meta = config.metaPixelId && config.metaCapiToken
  ? new MetaConversions(config.metaPixelId, config.metaCapiToken, config.metaTestEventCode)
  : null;
const app = Fastify({ logger: { level: process.env.LOG_LEVEL ?? 'info' } });

const authorized = (request: { headers: Record<string, unknown> }): boolean =>
  serviceAuthorized(request.headers.authorization, config.serviceSecret);

/**
 * La concesion rechazada, con su codigo separado del mensaje.
 *
 * Antes sendEntitlement lanzaba un `Error` con el cuerpo del api concatenado, la
 * ruta lo relanzaba y Fastify lo servia como 500 con el detalle dentro: el
 * navegador recibia literalmente `entitlement callback 400: {"code":"refused",
 * "message":"data refused auth.entitlement_..."}`. Ni el codigo era nuestro ni
 * ese detalle es del publico.
 */
export class EntitlementError extends Error {
  readonly status: number;
  readonly body: string;
  constructor(status: number, body: string) {
    super(`entitlement callback ${status}`);
    this.name = 'EntitlementError';
    this.status = status;
    this.body = body;
  }
}

async function sendEntitlement(userId: number, source: string, externalId: string, deliveryId: number): Promise<void> {
  const active = await store.entitlement(userId);
  // Stable across retries of this delivery, distinct across real state changes.
  const eventKey = `${source}:${externalId}:${deliveryId}:${active}`;
  const response = await fetch(config.entitlementsUrl, {
    method: 'POST', headers: { authorization: `Bearer ${config.serviceSecret}`, 'content-type': 'application/json' },
    body: JSON.stringify({ eventKey, userId, active, source, externalId, occurredAt: new Date().toISOString() }),
  });
  if (!response.ok) throw new EntitlementError(response.status, (await response.text()).slice(0, 300));
  await store.markDelivered(eventKey, userId, active);
}

const userIdFrom = (resource: Record<string, unknown>): number | null => {
  const metadata = resource.metadata as Record<string, unknown> | undefined;
  const candidate = metadata?.user_id ?? resource.external_reference;
  const value = Number(candidate);
  return Number.isSafeInteger(value) && value > 0 ? value : null;
};

async function processOne(): Promise<boolean> {
  const event = await store.takeEvent();
  if (!event) return false;
  try {
    if (event.resourceType.includes('subscription') || event.resourceType.includes('preapproval')) {
      const item = await provider.subscription(event.providerId);
      const userId = userIdFrom(item);
      await store.upsertSubscription({ providerId: event.providerId, userId,
        status: String(item.status ?? 'unknown'),
        periodEnd: typeof item.next_payment_date === 'string' ? item.next_payment_date : null, raw: item });
      if (userId) await sendEntitlement(userId, 'mercadopago.subscription', event.providerId, event.id);
    } else {
      const item = await provider.payment(event.providerId);
      const userId = userIdFrom(item);
      await store.upsertPayment({ providerId: event.providerId, userId,
        status: String(item.status ?? 'unknown'), amount: Number(item.transaction_amount ?? 0),
        currency: String(item.currency_id ?? CURRENCY), raw: item });
      const metadata = item.metadata as Record<string, unknown> | undefined;
      const redemptionId = Number(metadata?.coupon_redemption_id);
      if (String(item.status) === 'approved' && Number.isSafeInteger(redemptionId) && redemptionId > 0) {
        await store.redeemCouponReservation(redemptionId, event.providerId);
      }
      if (userId) await sendEntitlement(userId, 'mercadopago.payment', event.providerId, event.id);
      // After the grant, never before: a Meta hiccup must not delay access.
      if (userId && String(item.status) === 'approved' && Number(item.transaction_amount) > 0) {
        await queuePurchase(event.providerId, userId, item);
      }
    }
    await store.finishEvent(event.id);
  } catch (error) {
    app.log.error({ error, event }, 'payment event failed');
    await store.failEvent(event.id, event.attempts, error);
  }
  return true;
}

/**
 * Queues the Purchase for Meta. Queues, does not send: the payment event has to
 * finish whether or not Meta answers, and a Meta outage must never re-run the
 * entitlement path through failEvent. Delivery has its own outbox loop below.
 * Same event_id as the thank-you page (`mp:<payment id>`), so Meta counts one
 * sale even when both arrive.
 */
async function queuePurchase(providerId: string, userId: number, item: Record<string, unknown>): Promise<void> {
  if (!meta) return;
  const saved = await store.checkoutContext(userId);
  const payer = item.payer as { email?: unknown } | undefined;
  const email = saved?.email ?? (typeof payer?.email === 'string' ? payer.email : null);
  const event = purchaseEvent({ providerId, userId, email,
    eventTime: Date.parse(String(item.date_approved ?? '')) / 1000,
    amount: Number(item.transaction_amount), currency: String(item.currency_id ?? CURRENCY),
    context: saved?.context ?? null, fallbackUrl: `${config.publicOrigin}/pago` });
  const queued = await store.queueMetaEvent({ eventId: event.event_id, eventName: event.event_name, userId, providerId, payload: event });
  if (queued) app.log.info({ eventId: event.event_id, userId, matched: Boolean(saved) }, 'meta purchase queued');
}

async function deliverMetaOne(): Promise<boolean> {
  if (!meta) return false;
  const pending = await store.takeMetaEvent();
  if (!pending) return false;
  try {
    const receipt = await meta.send([pending.payload]);
    await store.metaSent(pending.eventId, receipt.fbtraceId);
    app.log.info({ eventId: pending.eventId, fbtraceId: receipt.fbtraceId }, 'meta purchase delivered');
  } catch (error) {
    const detail = error instanceof MetaError ? { status: error.status, body: error.body } : { error: String(error) };
    app.log.error({ eventId: pending.eventId, attempts: pending.attempts, ...detail }, 'meta conversions api rejected event');
    await store.metaFailed(pending.eventId, pending.attempts, error instanceof MetaError ? `${error.status} ${error.body}` : error);
  }
  return true;
}

app.get('/health', async () => ({ ok: true, compiler: 'tsgo', service: 'payments', meta: meta ? 'enabled' : 'disabled' }));

app.post<{ Body: { userId?: unknown; email?: unknown; mode?: unknown; couponCode?: unknown; context?: unknown } }>('/v1/checkout', async (request, reply) => {
  if (!authorized(request)) return reply.code(401).send({ error: 'unauthorized' });
  const userId = Number(request.body?.userId);
  const email = String(request.body?.email ?? '').trim().toLowerCase();
  const mode = request.body?.mode === 'subscription' ? 'subscription' : 'one_time';
  const couponCode = typeof request.body?.couponCode === 'string' ? request.body.couponCode : '';
  if (!Number.isSafeInteger(userId) || userId < 1 || !email.includes('@')) {
    return reply.code(400).send({ error: 'invalid_actor' });
  }
  if (couponCode && mode === 'subscription') return reply.code(400).send({ error: 'coupon_not_applicable' });
  // Browser facts the api forwarded (cookies, IP, UA, utm). Validated here, kept
  // for the Purchase event the webhook will send later. Not a reason to refuse
  // a checkout: an empty context only lowers Meta's match quality.
  await store.saveCheckoutContext(userId, email, sanitizeContext(request.body?.context));
  const reservation = couponCode ? await store.reserveCoupon(couponCode, userId) : null;
  if (couponCode && !reservation) return reply.code(422).send({ error: 'invalid_coupon' });
  try {
    if (reservation?.offer.totalMinor === 0) {
      // EL ORDEN ES EL ARREGLO, no un detalle de estilo.
      //
      // Antes esto marcaba la redencion como `redeemed` ANTES de llamar a
      // sendEntitlement. Si la concesion fallaba -- el servicio de datos caido, un
      // 400 del api -- la ruta respondia 500 y la fila se quedaba en `redeemed`
      // para siempre: releaseCoupon solo toca `state='reserved'` (db.ts), y el
      // indice unico coupon_user_redeemed impide que ese usuario lo reintente. El
      // cupon quedaba quemado, un cupo de los 25 consumido, el usuario sin acceso,
      // y la unica salida era editar Postgres a mano. Medido: user 4001 / ALXN100
      // / state=redeemed / respuesta 500 / sin derecho concedido.
      //
      // Ahora lo irreversible va ultimo. Si la concesion falla, la fila sigue
      // `reserved`, el catch la libera y el reintento funciona.
      //
      // providerId DETERMINISTA, no `coupon:${reservation.id}`: la reserva cambia
      // de id en cada reintento, asi que aquel formato dejaba un pago aprobado
      // nuevo por intento fallido. upsertPayment tiene la clave en providerId, asi
      // que con este el reintento reescribe la misma fila.
      const providerId = `coupon:${reservation.offer.code}:${userId}`;
      await store.upsertPayment({ providerId, userId, status: 'approved', amount: 0,
        currency: CURRENCY, raw: { source: 'coupon', coupon: reservation.offer.code } });
      await sendEntitlement(userId, 'coupon', providerId, reservation.id);
      await store.redeemCouponReservation(reservation.id, providerId);
      return { mode, coupon: reservation.offer.code, discountPercent: reservation.offer.percent,
        discountMinor: reservation.offer.discountMinor, totalMinor: 0, granted: true };
    }
    if (!config.mpAccessToken) {
      if (reservation) await store.releaseCoupon(reservation.id);
      return reply.code(501).send({ error: 'provider_not_configured' });
    }
    const result = await provider.checkout({ userId, email }, mode, reservation ? {
      totalMinor: reservation.offer.totalMinor, couponRedemptionId: reservation.id,
    } : undefined);
    const providerId = String(result.preferenceId ?? result.subscriptionId ?? '');
    if (reservation && providerId) await store.attachCoupon(reservation.id, providerId);
    return { ...result, ...(reservation ? { discountPercent: reservation.offer.percent,
      discountMinor: reservation.offer.discountMinor, totalMinor: reservation.offer.totalMinor } : {}) };
  } catch (error) {
    if (reservation) await store.releaseCoupon(reservation.id);
    // Un 4xx de Mercado Pago no es un fallo nuestro de 500: es el proveedor
    // rechazando el cobro (cuenta en otra moneda, monto por debajo del minimo,
    // token sin permiso). El detalle va al log, al cliente va un codigo.
    if (error instanceof MercadoPagoError) {
      app.log.error({ status: error.status, body: error.body, sent: error.sent, userId, mode },
        'mercadopago rejected checkout');
      return reply.code(502).send({ error: 'provider_rejected' });
    }
    // La concesion la rechazo el api, no nosotros. La reserva ya quedo liberada
    // arriba, asi que el cupon vuelve a estar disponible y el reintento sirve:
    // por eso el codigo dice que se puede repetir y no «error interno».
    if (error instanceof EntitlementError) {
      app.log.error({ status: error.status, body: error.body, userId, mode },
        'entitlement callback refused the grant');
      return reply.code(502).send({ error: 'grant_failed' });
    }
    throw error;
  }
});

app.post<{ Body: { data?: { id?: unknown }; type?: unknown; action?: unknown };
  Querystring: Record<string, string> }>('/v1/webhooks/mercadopago', async (request, reply) => {
  const dataId = String(request.query?.['data.id'] ?? request.body?.data?.id ?? '');
  // Mercado Pago signs the resource id, request id and timestamp, but not the
  // body `type`. Never let an unsigned field choose which provider endpoint we
  // call: numeric ids are payments; preapproval ids are UUID-like strings.
  const resourceType = /^\d+$/.test(dataId) ? 'payment' : 'subscription_preapproval';
  if (!config.mpWebhookSecret) return reply.code(501).send({ error: 'provider_not_configured' });
  if (!dataId) return reply.code(400).send({ error: 'missing_data_id' });
  const checked = verifyMercadoPagoSignature({ dataId,
    requestId: String(request.headers['x-request-id'] ?? ''),
    signature: String(request.headers['x-signature'] ?? ''), secret: config.mpWebhookSecret,
    windowSeconds: config.webhookWindowSeconds });
  if (!checked.ok) return reply.code(401).send({ error: checked.reason === 'expired' ? 'expired_signature' : 'invalid_signature' });
  const inserted = await store.recordEvent(checked.eventKey, dataId, resourceType);
  setImmediate(() => { void processOne(); });
  return reply.code(202).send({ ok: true, accepted: inserted });
});

app.get<{ Params: { userId: string } }>('/v1/subscriptions/:userId', async (request, reply) => {
  if (!authorized(request)) return reply.code(401).send({ error: 'unauthorized' });
  const userId = Number(request.params.userId);
  if (!Number.isSafeInteger(userId) || userId < 1) return reply.code(400).send({ error: 'invalid_user' });
  return { subscription: await store.subscription(userId), active: await store.entitlement(userId) };
});

app.post<{ Params: { userId: string } }>('/v1/subscriptions/:userId/cancel', async (request, reply) => {
  if (!authorized(request)) return reply.code(401).send({ error: 'unauthorized' });
  const userId = Number(request.params.userId);
  if (!Number.isSafeInteger(userId) || userId < 1) return reply.code(400).send({ error: 'invalid_user' });
  const current = await store.subscription(userId) as { provider_id?: string } | null;
  if (!current?.provider_id) return reply.code(404).send({ error: 'subscription_not_found' });
  const changed = await provider.cancelSubscription(current.provider_id);
  await store.upsertSubscription({ providerId: current.provider_id, userId,
    status: String(changed.status ?? 'cancelled'), periodEnd: null, raw: changed });
  await sendEntitlement(userId, 'mercadopago.subscription', current.provider_id, Date.now());
  return { subscription: await store.subscription(userId), active: await store.entitlement(userId) };
});

app.get('/v1/admin/payments', async (request, reply) => {
  if (!authorized(request)) return reply.code(401).send({ error: 'unauthorized' });
  return { payments: await store.listPayments(), metaEvents: await store.listMetaEvents() };
});

await store.migrate();
if (!meta) app.log.warn('meta conversions api disabled: META_PIXEL_ID and META_CAPI_TOKEN unset, purchases will not be reported to Meta');
const timer = setInterval(() => { void processOne(); void deliverMetaOne(); }, 1_000);
timer.unref();
for (const signal of ['SIGTERM', 'SIGINT'] as const) process.once(signal, async () => {
  clearInterval(timer); await app.close(); await store.close(); process.exit(0);
});

await app.listen({ host: config.host, port: config.port });
