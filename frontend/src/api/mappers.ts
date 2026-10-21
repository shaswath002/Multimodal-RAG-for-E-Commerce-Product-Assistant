/** Field mapper — one place to translate wire-format fields to frontend types.
 *  Change backend field names here only; no other file should touch raw names.
 */

import type { Product, StoreLink, PricePoint } from './types'

function safeParseJSON<T>(raw: string | T | undefined, fallback: T): T {
  if (raw === undefined || raw === null) return fallback
  if (typeof raw !== 'string') return raw
  try {
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

/** Map raw backend product object to a typed Product */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function mapProduct(raw: any): Product {
  return {
    id: String(raw.id ?? ''),
    title: raw.title ?? '',
    brand: raw.brand,
    category: raw.category,
    price: Number(raw.price ?? 0),
    original_price: raw.original_price !== undefined ? Number(raw.original_price) : undefined,
    discount_percentage:
      raw.discount_percentage !== undefined ? Number(raw.discount_percentage) : undefined,
    rating: raw.rating !== undefined ? Number(raw.rating) : undefined,
    image_url: raw.image_url,
    specs: raw.specs,
    store_availability: safeParseJSON<StoreLink[]>(raw.store_availability, []),
    price_history: safeParseJSON<PricePoint[]>(raw.price_history, []),
  }
}
