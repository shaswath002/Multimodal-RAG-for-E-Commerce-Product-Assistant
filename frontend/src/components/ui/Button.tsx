import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary-dark' | 'primary-light' | 'outline' | 'ghost'
type Size = 'sm' | 'md' | 'lg'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  children: ReactNode
  fullWidth?: boolean
}

const variantStyles: Record<Variant, object> = {
  'primary-dark': {
    backgroundColor: 'var(--champagne)',
    color: 'var(--ink-900)',
    border: 'none',
  },
  'primary-light': {
    backgroundColor: 'var(--ink-900)',
    color: 'var(--on-dark)',
    border: 'none',
  },
  outline: {
    backgroundColor: 'transparent',
    color: 'var(--text)',
    border: '1px solid var(--line)',
  },
  ghost: {
    backgroundColor: 'transparent',
    color: 'var(--text-muted)',
    border: 'none',
  },
}

const sizeStyles: Record<Size, object> = {
  sm: { padding: '6px 14px', fontSize: '0.75rem' },
  md: { padding: '10px 20px', fontSize: '0.85rem' },
  lg: { padding: '13px 28px', fontSize: '0.9rem' },
}

export default function Button({
  variant = 'primary-dark',
  size = 'md',
  children,
  fullWidth = false,
  style,
  ...props
}: Props) {
  return (
    <button
      {...props}
      style={{
        ...variantStyles[variant],
        ...sizeStyles[size],
        borderRadius: 'var(--r-pill)',
        fontFamily: 'Manrope, sans-serif',
        fontWeight: 600,
        letterSpacing: '0.06em',
        cursor: 'pointer',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '6px',
        transition: `opacity var(--dur-fast) var(--ease-out), background var(--dur-fast)`,
        minHeight: 44,
        width: fullWidth ? '100%' : undefined,
        ...style,
      }}
      onMouseEnter={(e) => {
        ;(e.currentTarget as HTMLButtonElement).style.opacity = '0.85'
        props.onMouseEnter?.(e)
      }}
      onMouseLeave={(e) => {
        ;(e.currentTarget as HTMLButtonElement).style.opacity = '1'
        props.onMouseLeave?.(e)
      }}
    >
      {children}
    </button>
  )
}
