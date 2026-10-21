import { useId, type InputHTMLAttributes } from 'react'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  dark?: boolean
}

export default function Input({ label, error, dark = false, id, style, ...props }: Props) {
  const generatedId = useId()
  const baseId = id ?? `input-${generatedId}`

  const inputStyle = dark
    ? {
        backgroundColor: 'var(--ink-700)',
        color: 'var(--on-dark)',
        border: '1px solid var(--ink-500)',
        caretColor: 'var(--champagne)',
      }
    : {
        backgroundColor: 'var(--card)',
        color: 'var(--text)',
        border: '1px solid var(--line)',
      }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
      {label && (
        <label
          htmlFor={baseId}
          className="eyebrow"
          style={{
            color: dark ? 'var(--on-dark-muted)' : 'var(--text-muted)',
            fontSize: '0.7rem',
          }}
        >
          {label}
        </label>
      )}
      <input
        id={baseId}
        {...props}
        style={{
          ...inputStyle,
          borderRadius: 'var(--r-md)',
          padding: '12px 16px',
          fontSize: '0.9rem',
          fontFamily: 'Manrope, sans-serif',
          outline: 'none',
          width: '100%',
          minHeight: 44,
          transition: `border-color var(--dur-fast)`,
          ...style,
        }}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = dark ? 'var(--champagne)' : 'var(--champagne-deep)'
          props.onFocus?.(e)
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = dark ? 'var(--ink-500)' : 'var(--line)'
          props.onBlur?.(e)
        }}
      />
      {error && (
        <p role="alert" style={{ color: 'var(--verdict-wait)', fontSize: '0.75rem' }}>
          {error}
        </p>
      )}
    </div>
  )
}
