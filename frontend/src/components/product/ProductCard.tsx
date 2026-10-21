import { useState } from 'react'
import { ShoppingCart, Heart, Star, Shirt, Footprints, Watch, Cpu, Home, Sparkles, Dumbbell, Package } from 'lucide-react'
import { Link } from 'react-router-dom'

export interface ProductCardData {
  id: string
  title: string
  brand?: string
  price: number
  originalPrice?: number
  discountPercentage?: number
  rating?: number
  imageUrl?: string
  category?: string
}

interface Props {
  product: ProductCardData
  onAddToCart?: (id: string) => void
  onSave?: (id: string) => void
}

function formatINR(amount: number) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

/** Returns the category icon component for the placeholder tile */
function CategoryIcon({ category }: { category?: string }) {
  const cat = category?.toLowerCase() ?? ''
  const size = 40
  const sw = 1.2
  const style = { opacity: 0.35, color: 'var(--text-muted)' }

  if (cat.includes('cloth') || cat.includes('shirt')) return <Shirt size={size} strokeWidth={sw} style={style} />
  if (cat.includes('shoe') || cat.includes('foot')) return <Footprints size={size} strokeWidth={sw} style={style} />
  if (cat.includes('watch')) return <Watch size={size} strokeWidth={sw} style={style} />
  if (cat.includes('electron') || cat.includes('tech')) return <Cpu size={size} strokeWidth={sw} style={style} />
  if (cat.includes('home') || cat.includes('lamp') || cat.includes('table')) return <Home size={size} strokeWidth={sw} style={style} />
  if (cat.includes('beauty') || cat.includes('cosmet')) return <Sparkles size={size} strokeWidth={sw} style={style} />
  if (cat.includes('sport') || cat.includes('gym')) return <Dumbbell size={size} strokeWidth={sw} style={style} />
  return <Package size={size} strokeWidth={sw} style={style} />
}

/** Only show brand if it's a real value (not the placeholder string) */
function isRealBrand(brand?: string) {
  if (!brand) return false
  const upper = brand.trim().toUpperCase()
  return upper !== 'BRAND' && upper !== '' && upper !== 'N/A'
}

export default function ProductCard({ product, onAddToCart, onSave }: Props) {
  const [imgError, setImgError] = useState(false)
  const [saved, setSaved] = useState(false)

  /* Only compute discount when both prices are real and price < originalPrice */
  const discount =
    product.discountPercentage && product.discountPercentage > 0
      ? product.discountPercentage
      : product.originalPrice && product.price && product.originalPrice > product.price
        ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)
        : undefined

  const hasImage = Boolean(product.imageUrl) && !imgError

  return (
    <article
      style={{
        backgroundColor: 'var(--card)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--r-lg)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        transition: `transform var(--dur-mid) var(--ease-out), box-shadow var(--dur-mid)`,
      }}
      onMouseEnter={(e) => {
        const el = e.currentTarget as HTMLElement
        el.style.transform = 'translateY(-2px)'
        el.style.boxShadow = '0 4px 20px rgba(0,0,0,0.08)'
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget as HTMLElement
        el.style.transform = 'translateY(0)'
        el.style.boxShadow = 'none'
      }}
    >
      {/* Image */}
      <div
        style={{
          position: 'relative',
          backgroundColor: 'var(--tile)',
          aspectRatio: '4/3',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
        }}
      >
        {hasImage ? (
          <img
            src={product.imageUrl}
            alt={product.title}
            loading="lazy"
            onError={() => setImgError(true)}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          /* Tinted tile with category icon – no broken-image icon */
          <CategoryIcon category={product.category} />
        )}

        {/* Discount badge – only when a real discount exists */}
        {discount && discount > 0 && (
          <span
            style={{
              position: 'absolute',
              top: '10px',
              left: '10px',
              backgroundColor: 'var(--ink-900)',
              color: 'var(--champagne)',
              fontSize: '0.65rem',
              fontWeight: 700,
              letterSpacing: '0.04em',
              padding: '3px 8px',
              borderRadius: 'var(--r-pill)',
            }}
          >
            -{discount}%
          </span>
        )}

        {/* Save */}
        <button
          aria-label={saved ? 'Remove from saved' : 'Save item'}
          onClick={() => {
            setSaved((s) => !s)
            onSave?.(product.id)
          }}
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            background: 'rgba(255,255,255,0.9)',
            border: 'none',
            borderRadius: 'var(--r-pill)',
            padding: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            color: saved ? 'var(--verdict-wait)' : 'var(--text-muted)',
          }}
        >
          <Heart size={14} strokeWidth={1.5} fill={saved ? 'currentColor' : 'none'} />
        </button>
      </div>

      {/* Info */}
      <div style={{ padding: '12px', flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {/* Brand – only if it's a real brand name */}
        {isRealBrand(product.brand) && (
          <p
            className="eyebrow"
            style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}
          >
            {product.brand}
          </p>
        )}

        <Link
          to={`/product/${product.id}`}
          style={{
            color: 'var(--text)',
            textDecoration: 'none',
            fontSize: '0.82rem',
            fontWeight: 500,
            lineHeight: 1.4,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {product.title}
        </Link>

        {/* Rating – only when a real numeric rating is provided */}
        {typeof product.rating === 'number' && product.rating > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Star size={11} strokeWidth={1.5} style={{ color: 'var(--champagne-deep)' }} />
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              {product.rating.toFixed(1)}
            </span>
          </div>
        )}

        {/* Price row */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            marginTop: 'auto',
            paddingTop: '6px',
          }}
        >
          <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text)' }}>
            {formatINR(product.price)}
          </span>
          {product.originalPrice && product.originalPrice > product.price && (
            <span
              style={{
                fontSize: '0.75rem',
                color: 'var(--text-muted)',
                textDecoration: 'line-through',
              }}
            >
              {formatINR(product.originalPrice)}
            </span>
          )}
        </div>
      </div>

      {/* Add to cart */}
      <div style={{ padding: '0 12px 12px' }}>
        <button
          aria-label={`Add ${product.title} to cart`}
          onClick={() => onAddToCart?.(product.id)}
          style={{
            width: '100%',
            backgroundColor: 'var(--ink-900)',
            color: 'var(--on-dark)',
            border: 'none',
            borderRadius: 'var(--r-pill)',
            padding: '9px',
            fontSize: '0.75rem',
            fontWeight: 600,
            letterSpacing: '0.05em',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            minHeight: 40,
            transition: `opacity var(--dur-fast)`,
          }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.opacity = '0.85')
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.opacity = '1')
          }
        >
          <ShoppingCart size={13} strokeWidth={1.5} />
          Add to cart
        </button>
      </div>
    </article>
  )
}
