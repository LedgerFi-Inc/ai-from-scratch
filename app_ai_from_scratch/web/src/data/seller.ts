import { AUTOR, CORREO, ORG } from '../lib/site';

const env = (k: string): string => String(import.meta.env[k] ?? process.env[k] ?? '').trim();

/** Seller identity for terms, footer, JSON-LD. Empty legal fields stay empty — never invented. */
export const seller = {
  name: AUTOR,
  org: ORG,
  email: CORREO,
  city: 'Medellín',
  country: 'CO',
  taxId: env('PUBLIC_VENDEDOR_ID'),
  address: env('PUBLIC_VENDEDOR_DIRECCION'),
  phone: env('PUBLIC_VENDEDOR_TEL'),
};

export const sellerLine = (): string => {
  const bits = [seller.name, seller.city, seller.country];
  if (seller.taxId) bits.push(`NIT/ID ${seller.taxId}`);
  if (seller.address) bits.push(seller.address);
  if (seller.phone) bits.push(seller.phone);
  bits.push(seller.email);
  return bits.join(' · ');
};
