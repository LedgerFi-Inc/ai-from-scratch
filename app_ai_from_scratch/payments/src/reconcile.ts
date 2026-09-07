// What the webhook queue has not heard about yet. Pure: the search against
// Mercado Pago and the local table live in mercadopago.ts / db.ts; this only
// names the ids that must be re-enqueued.
//
// POR QUÉ ESTE FICHERO EXISTE. Un webhook perdido, o uno que rechazamos por
// firma y nunca reintentamos, deja el pago aprobado en Mercado Pago y ausente
// (o con un status viejo) en `payments`. La cuenta real ya tuvo un aprobado
// huérfano. diffPayments no cobra ni concede: solo señala ids para que
// processOne los vuelva a leer. Una fila local sin espejo remoto (un cupón)
// no se toca: no hay nada que reconcilie en el proveedor.

export interface RemotePayment {
  id: string;
  status: string;
  dateLastUpdated: string;
}

export interface LocalPayment {
  providerId: string;
  status: string;
  updatedAt: string;
}

/**
 * Remote ids whose local row is missing, has a different status, or is older
 * than Mercado Pago's `date_last_updated`. Local-only rows (coupon grants) are
 * not returned: they have no Mercado Pago id to fetch.
 */
export function diffPayments(remote: RemotePayment[], local: LocalPayment[]): string[] {
  const byId = new Map(local.map((row) => [row.providerId, row]));
  const flagged: string[] = [];
  for (const item of remote) {
    const row = byId.get(item.id);
    if (!row) {
      flagged.push(item.id);
      continue;
    }
    if (row.status !== item.status) {
      flagged.push(item.id);
      continue;
    }
    const remoteAt = Date.parse(item.dateLastUpdated);
    const localAt = Date.parse(row.updatedAt);
    if (Number.isFinite(remoteAt) && Number.isFinite(localAt) && remoteAt > localAt) {
      flagged.push(item.id);
    }
  }
  return flagged;
}
