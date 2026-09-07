// The price, on the web side, in one place.
//
// WHY THIS IS SEPARATE FROM site.ts. site.ts reads `import.meta.env`, which only
// exists inside the Astro build; plain Node throws on it. The price has to be
// readable from a Node script so `pnpm verify` can compare it against what the
// payments service actually charges, so it lives in a module with no build-time
// globals. site.ts re-exports it, and every existing call site keeps working.
//
// WHY A COPY EXISTS AT ALL. `payments/src/price.ts` is the source of truth: it is
// the number that reaches Mercado Pago. web/ is a separate package with its own
// install, so it cannot import across the boundary at build time. The copy is
// therefore unavoidable — what is avoidable is the DRIFT, and that is what
// `scripts/check-price.mjs` fails on. A landing page advertising one number while
// the checkout charges another is the failure this guards.

/** ISO-4217. Must equal CURRENCY in payments/src/price.ts. */
export const MONEDA = 'COP';

/** Decimals of MONEDA. COP: 0. Must equal DECIMALS in payments/src/price.ts. */
export const DECIMALES = 0;

/** Monthly price in MINOR units. Must equal PRICE_MINOR in payments/src/price.ts. */
export const PRECIO_MENOR = 39_900;

/**
 * The bare number, no separators: `35000`.
 *
 * This is the schema.org form. `price` in a JSON-LD Offer must be a plain number
 * — a thousands separator there is a parse error for the crawler, not a style
 * choice, and `35.000` would be read as thirty-five.
 */
export const PRECIO = String(DECIMALES === 0
  ? PRECIO_MENOR
  : (PRECIO_MENOR / 10 ** DECIMALES).toFixed(DECIMALES));

/**
 * The price as PROSE, per language: `35.000` in Spanish, `35,000` in English.
 *
 * Colombia writes thirty-five thousand as 35.000 and the anglophone world writes
 * it 35,000. Getting this backwards does not look like a typo, it looks like a
 * different price by three orders of magnitude, so the separator is part of the
 * translation and not a formatting detail.
 */
export const PRECIO_TEXTO: Record<string, string> = {
  es: (PRECIO_MENOR / 10 ** DECIMALES).toLocaleString('es-CO'),
  en: (PRECIO_MENOR / 10 ** DECIMALES).toLocaleString('en-US'),
};

/**
 * NO HAY PRECIO TACHADO. Hasta el 2026-09-05 la landing y /pago mostraban un
 * «antes $99.999» junto al precio real. Nunca se cobró: era un ancla de
 * marketing, y un precio de referencia que no existió es exactamente lo que la
 * Ley 1480 (información engañosa) sanciona, además de decir «esto es una
 * rebaja» cuando la propuesta es «esto es barato a propósito: IA para todos».
 * El ancla ahora es real y vive en el copy: lo que cuesta un domicilio, dos
 * cafés o una salida a cine, comparado con el precio. Si alguna vez se vende a
 * un precio mayor y luego se baja, el tachado se puede volver a declarar aquí.
 */

/**
 * Una cantidad en unidades menores como prosa: `35.000 COP`.
 *
 * Existe para el cupón, que es el único importe que la web no conoce de antemano.
 * Antes el navegador hacía `(result.totalCents / 100).toFixed(2)` y le pegaba
 * «USD» delante: con COP eso pintaba «USD 350.00» sobre un cobro de 35.000 pesos.
 */
export function textoImporte(menor: number, lang = 'es'): string {
  const valor = menor / 10 ** DECIMALES;
  const loc = lang === 'en' ? 'en-US' : 'es-CO';
  return `${valor.toLocaleString(loc, { minimumFractionDigits: DECIMALES,
    maximumFractionDigits: DECIMALES })} ${MONEDA}`;
}

/**
 * El precio tal y como se PINTA en grande, con su marcador de moneda.
 *
 * Por qué el marcador cambia de idioma y no solo el separador: en Colombia `$`
 * significa pesos y `$35.000` se lee sin ambigüedad. En inglés `$35,000` se lee
 * treinta y cinco mil DÓLARES, que es mil veces el precio — un error de otra
 * clase que el del separador de miles. Así que en inglés el símbolo se cae y la
 * moneda se escribe: `35,000 COP`.
 */
export const PRECIO_VISUAL: Record<string, string> = {
  es: `$${PRECIO_TEXTO.es}`,
  en: `${PRECIO_TEXTO.en} ${MONEDA}`,
};
