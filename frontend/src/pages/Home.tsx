import { Link } from 'react-router-dom'
import {
  Shirt,
  Footprints,
  Watch,
  Cpu,
  Home as HomeIcon,
  Sparkles,
  ArrowRight,
  BarChart2,
  ExternalLink,
  Zap,
} from 'lucide-react'
import SearchBar from '../components/search/SearchBar'
import SectionHeader from '../components/ui/SectionHeader'
import Chip from '../components/ui/Chip'
import ProductCard, { type ProductCardData } from '../components/product/ProductCard'
import { useState } from 'react'

/* ── Category data ─────────────────────────────────────────────── */
const CATEGORIES = [
  { label: 'Clothing', slug: 'clothing', Icon: Shirt },
  { label: 'Shoes', slug: 'shoes', Icon: Footprints },
  { label: 'Watches', slug: 'watches', Icon: Watch },
  { label: 'Electronics', slug: 'electronics', Icon: Cpu },
  { label: 'Home', slug: 'home', Icon: HomeIcon },
  { label: 'Beauty', slug: 'beauty', Icon: Sparkles },
]

/* ── Hero chips replaced with category names ────────────────────── */
const CHIPS = ['Clothing', 'Shoes', 'Watches', 'Electronics', 'Home', 'Beauty']

/* ── Mock trending products (static for Phase 1) ───────────────── */
const TRENDING: ProductCardData[] = [
  { id: 't1', title: 'Linen Blend Shirt', price: 1299, originalPrice: 2199, category: 'Clothing' },
  { id: 't2', title: 'Last 2 hours sale', price: 899, originalPrice: 1499, category: 'Shoes' },
  { id: 't3', title: 'Minimalist Desk Lamp', price: 2499, originalPrice: 3999, category: 'Home' },
  { id: 't4', title: 'Ceramic Table Lamp', price: 3199, originalPrice: 4999, category: 'Home' },
  { id: 't5', title: 'Relaxing Joggers', price: 799, originalPrice: 1299, category: 'Clothing' },
  { id: 't6', title: 'Running Shoes', price: 2999, originalPrice: 4499, category: 'Shoes' },
  { id: 't7', title: 'Pillow Essentials', price: 599, originalPrice: 999, category: 'Home' },
  { id: 't8', title: 'Kitchen 2-piece set', price: 1199, originalPrice: 1899, category: 'Home' },
]

/* ── Featured "watch edit" mock – 4 real products ───────────────── */
const FEATURED: ProductCardData[] = [
  { id: 'f1', title: 'Automatic Chronograph', price: 12999, originalPrice: 18999, category: 'Watches' },
  { id: 'f2', title: 'Dress Watch Polish', price: 7999, originalPrice: 11499, category: 'Watches' },
  { id: 'f3', title: 'Diver Polish', price: 9499, originalPrice: 13999, category: 'Watches' },
  { id: 'f4', title: 'Smart Watch Pro', price: 15999, originalPrice: 21999, category: 'Watches' },
]

/* ── Trust items ───────────────────────────────────────────────── */
const TRUST = [
  { Icon: BarChart2, label: 'Compare store prices' },
  { Icon: BarChart2, label: 'Price history' },
  { Icon: ExternalLink, label: 'Direct links to stores' },
  { Icon: Zap, label: 'Smart recommendations' },
]

export default function Home() {
  const [activeChip, setActiveChip] = useState<string | null>(null)

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────── */}
      <section
        style={{ backgroundColor: 'var(--ink-900)', paddingBottom: '80px' }}
        aria-label="Hero"
      >
        <div className="container" style={{ paddingTop: '80px', textAlign: 'center' }}>
          {/* Eyebrow */}
          <p
            className="eyebrow"
            style={{
              color: 'var(--champagne)',
              marginBottom: '1rem',
              letterSpacing: '0.22em',
            }}
          >
            Ask. Show. Discover.
          </p>

          {/* Headline */}
          <h1
            className="font-display"
            style={{
              color: 'var(--on-dark)',
              fontSize: 'clamp(2.4rem, 5.5vw, 4rem)',
              lineHeight: 1.1,
              fontWeight: 400,
              marginBottom: '2.5rem',
            }}
          >
            The whole market, one smart search.
          </h1>

          {/* SearchBar – centered, 760px max width */}
          <div style={{ maxWidth: 760, margin: '0 auto' }}>
            <SearchBar dark />
          </div>

          {/* Category chips – centered row */}
          <div
            style={{
              display: 'flex',
              gap: '8px',
              flexWrap: 'wrap',
              marginTop: '1.25rem',
              justifyContent: 'center',
            }}
          >
            {CHIPS.map((chip) => (
              <Chip
                key={chip}
                dark
                active={activeChip === chip}
                onClick={() => setActiveChip((c) => (c === chip ? null : chip))}
              >
                {chip}
              </Chip>
            ))}
          </div>
        </div>
      </section>

      {/* ── Category cards ─────────────────────────────────────────── */}
      <section
        aria-label="Browse categories"
        style={{
          backgroundColor: 'var(--paper)',
          marginTop: '-48px',
          paddingBottom: '0',
        }}
      >
        <div className="container">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(6, 1fr)',
              gap: '12px',
            }}
          >
            {CATEGORIES.map(({ label, slug, Icon }) => (
              <Link
                key={slug}
                to={`/category/${slug}`}
                aria-label={`Browse ${label}`}
                style={{
                  backgroundColor: 'var(--card)',
                  border: '1px solid var(--line)',
                  borderRadius: 'var(--r-lg)',
                  padding: '24px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '10px',
                  textDecoration: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
                  transition: `transform var(--dur-mid) var(--ease-out), color var(--dur-fast)`,
                  textAlign: 'center',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)'
                  e.currentTarget.style.color = 'var(--champagne-deep)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.color = 'var(--text-muted)'
                }}
              >
                <Icon size={28} strokeWidth={1.5} />
                {label}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── Featured collection (The watch edit) ─────────────────── */}
      {/*
        Layout: one large feature tile on the left (~40%) + 2×2 grid of 4 cards on the right.
        Uses a CSS grid: [feature-tile | 2-col card grid]
      */}
      <section
        aria-label="Featured collection"
        style={{ paddingTop: '56px', paddingBottom: '56px', backgroundColor: 'var(--paper)' }}
      >
        <div className="container">
          <SectionHeader
            title="The watch edit"
            action={
              <Link
                to="/category/watches"
                style={{ display: 'flex', alignItems: 'center', gap: '4px', textDecoration: 'none', color: 'inherit' }}
              >
                Shop watches <ArrowRight size={14} strokeWidth={1.5} />
              </Link>
            }
          />

          {/* Outer grid: [feature-tile] [2×2 product cards] */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '2fr 3fr',
              gap: '16px',
              alignItems: 'stretch',
            }}
          >
            {/* Left: large feature tile */}
            <div
              style={{
                backgroundColor: 'var(--tile)',
                borderRadius: 'var(--r-xl)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
                padding: '32px 24px',
                border: '1px solid var(--line)',
                minHeight: 360,
              }}
            >
              <Watch size={64} strokeWidth={1} style={{ color: 'var(--text-muted)', opacity: 0.4, marginBottom: '24px' }} />
              <p
                className="font-display"
                style={{ color: 'var(--text-muted)', fontSize: '1.1rem', fontWeight: 400, textAlign: 'center' }}
              >
                Time, well chosen
              </p>
            </div>

            {/* Right: 2×2 grid of exactly 4 product cards */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '16px',
              }}
            >
              {FEATURED.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Trending now ─────────────────────────────────────────── */}
      <section
        aria-label="Trending now"
        style={{ paddingTop: '56px', paddingBottom: '56px' }}
      >
        <div className="container">
          <SectionHeader
            title="Trending now"
            action={
              <Link
                to="/search?q=trending"
                style={{ display: 'flex', alignItems: 'center', gap: '4px', textDecoration: 'none', color: 'inherit' }}
              >
                Show all <ArrowRight size={14} strokeWidth={1.5} />
              </Link>
            }
          />

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '16px',
            }}
          >
            {TRENDING.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </div>
      </section>

      {/* ── Trust row ────────────────────────────────────────────── */}
      <section
        style={{
          backgroundColor: 'var(--paper)',
          borderTop: '1px solid var(--line)',
          borderBottom: '1px solid var(--line)',
          padding: '32px 0',
        }}
        aria-label="Why UrbanPick"
      >
        <div
          className="container"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '24px',
          }}
        >
          {TRUST.map(({ Icon, label }) => (
            <div
              key={label}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '10px',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 'var(--r-pill)',
                  backgroundColor: 'var(--tile)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--champagne-deep)',
                }}
              >
                <Icon size={20} strokeWidth={1.5} />
              </div>
              <p style={{ fontSize: '0.82rem', fontWeight: 500, color: 'var(--text)' }}>{label}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
