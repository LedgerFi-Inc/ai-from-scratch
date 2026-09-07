// Who this payment may grant access to, if anyone. Pure: no Postgres, so
// test/assess.test.ts can prove the rules without Mercado Pago or a database.
//
// POR QUÉ ESTE FICHERO EXISTE. processOne concedía 30 días con solo
// `item.status === 'approved'`. No miraba el importe, la moneda ni `live_mode`.
// Un enlace de checkout con descuento que Mercado Pago no caduca se puede
// reabrir el mes siguiente y pagar el mismo descuento; un pago de prueba en
// producción, o uno en USD, o uno de 1.000 COP contra un pedido de 39.900,
// pasaban igual. La cuenta real ya tiene un aprobado sin `user_id` resoluble:
// ese huérfano no es hipotético. Este módulo es el único sitio que decide
// elegibilidad; el servidor solo lo aplica.

export interface PaymentFacts {
  id: string;
  status: string;
  amountMinor: number;
  refundedMinor: number;
  currency: string;
  liveMode: boolean;
  dateCreated: Date;
  dateApproved: Date | null;
  userIdHint: number | null;
  orderKey: string | null;
}

export interface OrderFacts {
  orderKey: string;
  userId: number;
  expectedMinor: number;
  currency: string;
  consumedBy: string | null;
  expiresAt: Date;
  /** false for subscription orders: many authorized charges share one order. */
  singleUse: boolean;
}

export interface AssessEnv {
  production: boolean;
  priceMinor: number;
  currency: string;
}

export interface Verdict {
  eligible: boolean;
  reason: string | null;
  userId: number | null;
}

const HOUR = 3_600_000;

/**
 * First matching rule wins. A pending/rejected payment grants nothing regardless
 * of eligibility, so those statuses return eligible and must not be blocked:
 * blocking them would hide the real status behind an ineligibility flag.
 */
export function assessPayment(p: PaymentFacts, order: OrderFacts | null, env: AssessEnv): Verdict {
  if (p.status !== 'approved') {
    return { eligible: true, reason: null, userId: p.userIdHint };
  }

  const userId = order?.userId ?? p.userIdHint;
  if (userId == null) return { eligible: false, reason: 'no_user', userId: null };

  if (p.liveMode !== env.production) {
    return { eligible: false, reason: 'test_mode', userId };
  }

  const currency = order?.currency ?? env.currency;
  if (p.currency !== currency) {
    return { eligible: false, reason: 'currency_mismatch', userId };
  }

  if (order && p.userIdHint != null && order.userId !== p.userIdHint) {
    return { eligible: false, reason: 'order_user_mismatch', userId };
  }

  if (order?.singleUse && order.consumedBy && order.consumedBy !== p.id) {
    return { eligible: false, reason: 'order_consumed', userId };
  }

  if (order && p.dateCreated.getTime() > order.expiresAt.getTime() + HOUR) {
    return { eligible: false, reason: 'created_after_expiry', userId };
  }

  const expected = order?.expectedMinor ?? env.priceMinor;
  if ((p.amountMinor - p.refundedMinor) < expected) {
    return { eligible: false, reason: order ? 'amount_below_expected' : 'no_order', userId };
  }

  return { eligible: true, reason: null, userId };
}
