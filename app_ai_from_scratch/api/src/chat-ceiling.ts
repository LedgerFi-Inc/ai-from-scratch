// The token half of the chat spend ceiling, as a pure decision.
//
// WHY THIS FILE EXISTS. `CHAT_TOKENS_DAY` and `CHAT_TOKENS_DAY_GLOBAL` were
// declared in server.ts, incremented after every call, compared once, and the
// only consequence of exceeding them was an `app.log.warn`. Nothing read those
// counters before the billed call, so the only ceiling that ever bound was the
// question COUNT: 120 a day. At `esfuerzo: 'alto'` on the priciest provider
// that is roughly 3.6 million tokens for one account in one day, eighteen times
// the 200 000 the code claimed to enforce.
//
// It lived inline in server.ts, which calls `app.listen` at import, so testing
// it meant booting Fastify, a session, the ai service and Postgres. That is why
// the ledger could cite `api/test/chat-brake.mts` for months while the file did
// not exist: the shape of the code made the test expensive enough to skip. The
// decision is pure, so it belongs where a test can reach it in one import.

/** The 429 payload. Keys are read by web/src/lib/chat-client.ts. */
export interface Ceiling { limite: string; esperaS: number; tope: number; msg: string }

export interface TokenCaps { own: number; global: number }

/**
 * Returns the 429 payload when a token counter is ALREADY past its ceiling, or
 * null when the message may proceed.
 *
 * Read, never incremented. A request's cost is unknowable before it runs, so
 * the gate is "already over the line" rather than "would go over", and the
 * overshoot is bounded by a single turn. Strictly greater, matching the
 * question caps: a counter exactly at the ceiling has spent its allowance and
 * not exceeded it.
 *
 * Own before global, so a person who blew their own budget is told that, rather
 * than being told the platform is full.
 */
export function tokenCeiling(
  tokOwn: number,
  tokGlobal: number,
  caps: TokenCaps,
  esperaS: number,
): Ceiling | null {
  if (tokOwn > caps.own) {
    return { limite: 'tokens_dia', esperaS, tope: caps.own,
             msg: 'Llegaste al tope de uso de hoy. Mañana se reinicia.' };
  }
  if (tokGlobal > caps.global) {
    return { limite: 'tokens_dia_global', esperaS, tope: caps.global,
             msg: 'El chat alcanzó su tope de hoy para toda la plataforma. Vuelve mañana.' };
  }
  return null;
}
