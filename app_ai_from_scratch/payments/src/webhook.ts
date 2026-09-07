// Which Mercado Pago resource a webhook delivery is about. Pure: the route
// must not let an unsigned `type` pick an endpoint, but it also must not treat
// every non-numeric id as a preapproval — `merchant_order` and plan events
// would then be fetched as subscriptions and fail-retried into `dead`.
//
// POR QUÉ ESTE FICHERO EXISTE. El webhook usaba `/^\d+$/` sobre `data.id` y
// nada más: numérico = pago, cualquier otra cosa = suscripción. Mercado Pago
// manda `subscription_authorized_payment` (el cobro recurrente de verdad) y
// `merchant_order` (ruido). El primero nunca se procesaba; el segundo se
// encolaba como preapproval y moría a los 8 intentos. classifyWebhook nombra
// las cuatro clases reales y tira el resto con 202, sin tocar la cola.

export type WebhookKind = 'payment' | 'subscription' | 'authorized_payment' | 'ignore';

/**
 * Empty `type` keeps today's heuristic because Mercado Pago has signed
 * deliveries with no body type (query `topic` only). Anything we do not
 * recognise is ignored rather than guessed: a guess that hits the wrong
 * provider endpoint burns the retry budget on a resource we cannot process.
 */
export function classifyWebhook(type: string, dataId: string): WebhookKind {
  if (type === 'payment') return 'payment';
  if (type === 'subscription_preapproval') return 'subscription';
  if (type === 'subscription_authorized_payment') return 'authorized_payment';
  if (type === '') return /^\d+$/.test(dataId) ? 'payment' : 'subscription';
  return 'ignore';
}
