// El precio y la moneda, en UN solo sitio.
//
// POR QUÉ ESTE FICHERO EXISTE. El precio estaba en `PRICE_CENTS = 999` dentro de
// db.ts y en dos literales `9.99` dentro de mercadopago.ts, y la conversión al
// importe que recibe el proveedor era un `/ 100` escrito a mano en dos sitios más
// (mercadopago.ts y web/src/pages/pago.astro). Pasar a COP con esa forma es una
// trampa de un solo carácter: poner 35000 donde había 999 y dejar los `/100`
// intactos cobra 350 pesos en vez de 35.000, y el cobro sale sin error.
//
// LA UNIDAD MENOR NO SIEMPRE ES UN CÉNTIMO. USD tiene dos decimales, así que
// «cents» y «unidad menor» coincidían y nadie tuvo que distinguirlos. COP no
// tiene decimales en la práctica: Mercado Pago espera 35000, no 3500000. Por eso
// el exponente es un dato explícito y no un 100 repartido por el código, y por
// eso los campos ya no se llaman *Cents — un nombre que dice «céntimos» mientras
// guarda pesos es peor que no tener nombre.
export const CURRENCY = 'COP';

/**
 * Decimales de la moneda. COP: 0. USD sería 2.
 *
 * Es lo único que hay que tocar, junto con PRICE_MINOR y CURRENCY, para volver a
 * una moneda con céntimos.
 */
export const DECIMALS = 0;

/**
 * El precio mensual en unidades MENORES de CURRENCY.
 *
 * COP 39.990 al mes. Historial: 35.000 -> 39.900 (2026-09-05) -> 38.899
 * (2026-09-07) -> 39.990 (2026-09-08, el dueño del producto lo subió). Con
 * DECIMALS = 0, la unidad menor es el peso, así que este número es el precio
 * tal cual.
 */
export const PRICE_MINOR = 39_990;

/**
 * Días de acceso que compra UN pago (modo `one_time`). La suscripción
 * (`subscription`) renueva sola cada mes y su vencimiento lo dice Mercado Pago
 * (`next_payment_date`); un pago suelto no tiene quién lo venza, así que el
 * vencimiento se calcula aquí: fecha de aprobación + ONE_TIME_DAYS.
 *
 * 30 y no «un mes»: un cobro el 31 de enero vencería el 3 de marzo si se sumara
 * un mes de calendario, y la landing promete «el mes que ya pagaste».
 */
export const ONE_TIME_DAYS = 30;

/**
 * Desde cuándo un pago suelto vence. Antes de esta fecha el producto se vendía
 * como «pago único» con «actualizaciones futuras sin pagar otra vez»
 * (api/src/product.ts), y quien compró así conserva su acceso: su pago no lleva
 * vencimiento. Un pago aprobado a partir de aquí compra ONE_TIME_DAYS días.
 *
 * Medianoche de Bogotá (UTC-5) del 8 al 9 de septiembre, la fecha que citan los
 * términos. Movida del 5 al 9 el 2026-09-08 porque el despliegue se corrió: la
 * versión en producción seguía siendo la del 1 de septiembre, así que entre el
 * 5 y el 8 nadie llegó a ver «pago único» y dejarla en el 5 habría reclasificado
 * a 30 días compras hechas bajo los términos viejos. Seguro además por medición:
 * docs/MVP-READINESS.md:11 (auditoría de la cuenta real de Mercado Pago) —
 * «Nothing approved since 2026-09-05», no hay comprador que quede colgado.
 * NO puede quedar antes del despliegue de este cambio: quien pagó
 * viendo «pago único» compró sin vencimiento. Si el despliegue se corre, esta
 * fecha se corre con él. De los dos errores posibles, un instante posterior al
 * despliegue regala acceso perpetuo a quien compre entre medias; uno anterior
 * convierte en 30 días una compra vendida como perpetua. El segundo es el caro.
 */
export const ONE_TIME_EXPIRES_FROM = '2026-09-09T05:00:00Z';

/**
 * De unidad menor al importe que espera el proveedor.
 *
 * Con DECIMALS = 0 es la identidad, y ESO ES LO IMPORTANTE: la división ya no
 * está escrita a mano en cada llamada, así que cambiar de moneda no deja un
 * `/100` huérfano cobrando la centésima parte.
 */
export function providerAmount(minor: number): number {
  return DECIMALS === 0 ? minor : Number((minor / 10 ** DECIMALS).toFixed(DECIMALS));
}

/** Para logs y mensajes: «35.000 COP». Separador de miles del locale colombiano. */
export function formatMinor(minor: number): string {
  return `${providerAmount(minor).toLocaleString('es-CO')} ${CURRENCY}`;
}
