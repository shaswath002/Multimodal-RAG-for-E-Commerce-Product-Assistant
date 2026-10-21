interface Props {
  className?: string
  width?: number | string
  height?: number | string
  style?: object
  rounded?: 'sm' | 'md' | 'lg' | 'full'
}

const radiusMap = {
  sm: 'var(--r-sm)',
  md: 'var(--r-md)',
  lg: 'var(--r-lg)',
  full: 'var(--r-pill)',
}

export default function Skeleton({
  width = '100%',
  height = 20,
  style,
  rounded = 'md',
}: Props) {
  return (
    <div
      aria-hidden="true"
      style={{
        width,
        height,
        borderRadius: radiusMap[rounded],
        backgroundColor: 'var(--tile)',
        animation: 'pulse 1.5s ease-in-out infinite',
        ...style,
      }}
    />
  )
}

// Inject keyframes once via a style tag if not already present
if (typeof document !== 'undefined') {
  const id = 'up-skeleton-pulse'
  if (!document.getElementById(id)) {
    const style = document.createElement('style')
    style.id = id
    style.textContent = `@keyframes pulse { 0%,100%{opacity:.6} 50%{opacity:.3} }`
    document.head.appendChild(style)
  }
}
