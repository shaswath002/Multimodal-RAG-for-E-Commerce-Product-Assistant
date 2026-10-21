import { useState, useRef, type KeyboardEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Camera, X } from 'lucide-react'

interface Props {
  dark?: boolean
  placeholder?: string
  initialQuery?: string
}

export default function SearchBar({ dark = true, placeholder = 'Search the whole market…', initialQuery = '' }: Props) {
  const [query, setQuery] = useState(initialQuery)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  function handleImageSelect(file: File) {
    const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif', 'image/bmp']
    if (!allowed.includes(file.type)) return
    if (file.size > 5 * 1024 * 1024) return
    setImageFile(file)
    const url = URL.createObjectURL(file)
    setImagePreview(url)
  }

  function handleSearch() {
    if (!query.trim() && !imageFile) return
    const params = new URLSearchParams()
    if (query.trim()) params.set('q', query.trim())
    navigate(`/search?${params}`)
  }

  function handleKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') handleSearch()
  }

  const bg = dark ? 'var(--ink-700)' : 'var(--card)'
  const border = dark ? 'var(--border-dark)' : 'var(--line)'
  const textColor = dark ? '#ffffff' : 'var(--text)'
  const placeholderColor = dark ? 'var(--on-dark-muted)' : 'var(--text-muted)'

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {/* Image preview */}
      {imagePreview && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--ink-700)',
            borderRadius: 'var(--r-md)',
            padding: '8px 12px',
          }}
        >
          <img
            src={imagePreview}
            alt="Search image"
            style={{ width: 40, height: 40, objectFit: 'cover', borderRadius: 'var(--r-sm)' }}
          />
          <span style={{ fontSize: '0.8rem', color: 'var(--on-dark-muted)', flex: 1 }}>
            {imageFile?.name}
          </span>
          <button
            aria-label="Remove image"
            onClick={() => {
              setImageFile(null)
              setImagePreview(null)
            }}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--on-dark-muted)', padding: 4 }}
          >
            <X size={14} strokeWidth={1.5} />
          </button>
        </div>
      )}

      {/* Main bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          backgroundColor: bg,
          border: `1px solid ${border}`,
          borderRadius: 'var(--r-pill)',
          overflow: 'hidden',
          height: 52,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            paddingLeft: '18px',
            color: placeholderColor,
          }}
        >
          <Search size={16} strokeWidth={1.5} />
        </div>

        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKey}
          placeholder={placeholder}
          aria-label="Search products"
          style={{
            flex: 1,
            border: 'none',
            background: 'transparent',
            color: textColor,
            fontSize: '0.9rem',
            fontFamily: 'Manrope, sans-serif',
            padding: '0 12px',
            outline: 'none',
          }}
        />

        {/* Camera button */}
        <button
          aria-label="Upload an image to search"
          onClick={() => fileInputRef.current?.click()}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '0 12px',
            color: placeholderColor,
            display: 'flex',
            alignItems: 'center',
            minHeight: 44,
            transition: `color var(--dur-fast)`,
          }}
          onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.color = dark ? 'var(--on-dark)' : 'var(--text)')}
          onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.color = placeholderColor)}
        >
          <Camera size={16} strokeWidth={1.5} />
        </button>

        {/* Search button */}
        <button
          aria-label="Search"
          onClick={handleSearch}
          style={{
            backgroundColor: 'var(--champagne)',
            color: '#000000',
            border: 'none',
            borderRadius: 'var(--r-pill)',
            margin: '6px',
            padding: '0 22px',
            height: 40,
            fontSize: '0.8rem',
            fontWeight: 700,
            letterSpacing: '0.08em',
            cursor: 'pointer',
            fontFamily: 'Manrope, sans-serif',
            whiteSpace: 'nowrap',
            transition: `background-color var(--dur-fast)`,
          }}
          onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--champagne-hover)')}
          onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--champagne)')}
        >
          Search
        </button>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/jpg,image/png,image/webp,image/gif,image/bmp"
        capture="environment"
        aria-hidden="true"
        tabIndex={-1}
        style={{ display: 'none' }}
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) handleImageSelect(file)
          e.target.value = ''
        }}
      />
    </div>
  )
}
