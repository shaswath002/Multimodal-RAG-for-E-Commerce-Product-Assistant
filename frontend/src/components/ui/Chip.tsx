import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  active?: boolean
  onClick?: () => void
  dark?: boolean
}

export default function Chip({ children, active = false, onClick, dark = false }: Props) {
  const style = dark
    ? {
        backgroundColor: active ? 'var(--champagne)' : 'rgba(255,255,255,0.07)',
        color: active ? '#000000' : 'var(--on-dark-muted)',
        border: `1px solid ${active ? 'var(--champagne)' : 'var(--border-dark)'}`,
      }
    : {
        backgroundColor: active ? 'var(--ink-900)' : 'var(--card)',
        color: active ? 'var(--on-dark)' : 'var(--text-muted)',
        border: `1px solid ${active ? 'var(--ink-900)' : 'var(--line)'}`,
      }

  const Tag = onClick ? 'button' : 'span'

  return (
    <Tag
      onClick={onClick}
      style={{
        ...style,
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '6px 14px',
        borderRadius: 'var(--r-pill)',
        fontSize: '0.75rem',
        fontWeight: 500,
        fontFamily: 'Manrope, sans-serif',
        cursor: onClick ? 'pointer' : 'default',
        whiteSpace: 'nowrap',
        transition: `background var(--dur-fast), color var(--dur-fast)`,
        minHeight: 32,
      }}
    >
      {children}
    </Tag>
  )
}
