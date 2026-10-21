/** API type definitions — verified against backend/schemas.py field names.
 *  All field mapping that touches the wire format lives in mappers.ts.
 */

export interface Product {
  id: string
  title: string
  brand?: string
  category?: string
  price: number
  original_price?: number
  discount_percentage?: number
  rating?: number
  image_url?: string
  specs?: Record<string, string>
  /** Raw JSON string or parsed list */
  store_availability?: string | StoreLink[]
  /** Raw JSON string or parsed list */
  price_history?: string | PricePoint[]
}

export interface StoreLink {
  name: string
  price?: number
  url: string
}

export interface PricePoint {
  date: string
  price: number
}

export interface SearchRequest {
  text_prompt?: string
  image_file?: File
  max_price?: number
  category?: string
  top_k?: number
}

export interface SearchResponse {
  query: string
  recommended_products: Product[]
  ai_analysis: string
  comparison_table: Record<string, unknown>[]
  total_results: number
  search_type: 'text' | 'image' | 'multimodal'
}

export interface HealthResponse {
  status: string
}
