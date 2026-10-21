import { Link } from 'react-router-dom'
import { SearchX } from 'lucide-react'

export default function NotFound() {
  return (
    <div
      style={{
        minHeight: '60vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '16px',
        padding: '4rem 2rem',
        textAlign: 'center',
      }}
    >
      <SearchX size={48} strokeWidth={1} style={{ color: 'var(--champagne-deep)', opacity: 0.5 }} />
      <h1
        className="font-display"
        style={{ fontSize: 'clamp(1.5rem, 4vw, 2.5rem)', color: 'var(--text)', fontWeight: 400 }}
      >
        Page not found
      </h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: 320 }}>
        That page doesn't exist. Let's get you back to the market.
      </p>
      <Link
        to="/"
        style={{
          marginTop: '8px',
          backgroundColor: 'var(--ink-900)',
          color: 'var(--on-dark)',
          textDecoration: 'none',
          padding: '11px 24px',
          borderRadius: 'var(--r-pill)',
          fontSize: '0.85rem',
          fontWeight: 600,
        }}
      >
        Go home
      </Link>
    </div>
  )
}
