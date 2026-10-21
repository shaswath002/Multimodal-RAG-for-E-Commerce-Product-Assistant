import type { ReactNode } from 'react'

interface Props {
  title: string
  action?: ReactNode
  dark?: boolean
}

export default function SectionHeader({ title, action, dark = false }: Props) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '1.25rem',
      }}
    >
      <h2
        className="font-display"
        style={{
          fontSize: 'clamp(1.25rem, 2.5vw, 1.6rem)',
          fontWeight: 400,
          color: dark ? 'var(--on-dark)' : 'var(--text)',
        }}
      >
        {title}
      </h2>
      {action && (
        <span style={{ fontSize: '0.8rem', color: dark ? 'var(--champagne)' : 'var(--champagne-deep)' }}>
          {action}
        </span>
      )}
    </div>
  )
}
