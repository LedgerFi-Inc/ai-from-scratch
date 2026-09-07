// Who has access right now, and until when. Pure: no Postgres, so test/entitlement.test.ts
// can prove the rules without a database.
//
// WHY THIS EXISTS. `Store.entitlement()` used to be one SQL EXISTS: any approved payment,
// ever, meant access forever. That matched the product when it was «pago único». Since
// 2026-09-05 one payment buys ONE_TIME_DAYS days and the optional subscription renews by
// itself, so a payment now has an end date -- and that date has to travel to the api
// (`periodEnd` in the entitlement event) or the lapse sweep there has nothing to expire
// and the access is free and permanent again. This module derives both facts from the
// rows the store already keeps.
import { ONE_TIME_DAYS, ONE_TIME_EXPIRES_FROM } from './price.ts';

export interface EntitlementSource {
  kind: 'payment' | 'subscription';
  /** The provider's id of the row (payments.provider_id / subscriptions.provider_id). */
  id: string;
  status: string;
  /** payment: when it was approved; subscription: Mercado Pago's next_payment_date (may be null). */
  at: Date | null;
  /** When the row was last written. The fallback horizon for a subscription without a date. */
  seen: Date;
}

export interface EntitlementState {
  active: boolean;
  /** ISO instant the access ends, or null when it does not end (a purchase from the pago-único era). */
  periodEnd: string | null;
}

const DAY = 86_400_000;

/**
 * When one approved payment stops granting access. `null` = never: a payment approved
 * before ONE_TIME_EXPIRES_FROM was sold as «pago único, actualizaciones sin pagar otra
 * vez» and keeps that promise. Throws on a date that is not one: a payment whose
 * approval time cannot be read must not silently become a perpetual grant.
 */
export function oneTimePeriodEnd(approvedAt: Date): Date | null {
  if (!(approvedAt instanceof Date) || Number.isNaN(approvedAt.getTime())) {
    throw new Error('approved payment without a readable approval date');
  }
  if (approvedAt.getTime() < Date.parse(ONE_TIME_EXPIRES_FROM)) return null;
  return new Date(approvedAt.getTime() + ONE_TIME_DAYS * DAY);
}

/**
 * The access a user has from every payment and subscription row they own.
 *
 * - approved payment: grants until oneTimePeriodEnd (or forever, legacy).
 * - authorized subscription: grants until Mercado Pago's next_payment_date. If Mercado
 *   Pago sent no date, the grant is bounded to ONE_TIME_DAYS after the row was last
 *   updated rather than open-ended: an "authorized" row that never gets a date again
 *   must lapse, not live forever.
 * - anything else (pending, rejected, cancelled, paused…) grants nothing.
 *
 * periodEnd is the LATEST end among the live grants, or null when a legacy grant makes
 * the access perpetual.
 */
export function deriveEntitlement(rows: readonly EntitlementSource[], now: Date = new Date()): EntitlementState {
  let perpetual = false;
  let latest: Date | null = null;
  const consider = (end: Date): void => {
    if (end.getTime() > now.getTime() && (!latest || end.getTime() > latest.getTime())) latest = end;
  };
  for (const row of rows) {
    if (row.kind === 'payment') {
      if (row.status !== 'approved') continue;
      if (!row.at) throw new Error('approved payment without a readable approval date');
      const end = oneTimePeriodEnd(row.at);
      if (end === null) perpetual = true; else consider(end);
    } else if (row.kind === 'subscription') {
      if (row.status !== 'authorized') continue;
      consider(row.at ?? new Date(row.seen.getTime() + ONE_TIME_DAYS * DAY));
    } else {
      throw new Error(`unknown entitlement source kind: ${String((row as { kind: unknown }).kind)}`);
    }
  }
  if (perpetual) return { active: true, periodEnd: null };
  return latest ? { active: true, periodEnd: (latest as Date).toISOString() } : { active: false, periodEnd: null };
}

/**
 * The state of ONE grant: only the rows that belong to the (kind, id) a delivery is about.
 *
 * This is what travels to the api. The api keeps the latest state per (source,
 * external_id) and ORs them, so each delivery has to describe its own grant. Sending
 * the user aggregate under the delivery's key (what sendEntitlement did before) made a
 * CANCELLED subscription's key carry the live payment's end date; refund that payment
 * and the subscription key still said "active until then", so paid stayed 1 for the
 * rest of the month after a full refund.
 */
export function deriveEntitlementFor(rows: readonly EntitlementSource[], kind: EntitlementSource['kind'],
  id: string, now: Date = new Date()): EntitlementState {
  return deriveEntitlement(rows.filter((row) => row.kind === kind && row.id === id), now);
}
