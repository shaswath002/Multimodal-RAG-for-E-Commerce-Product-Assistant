import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff } from 'lucide-react'
import AuthLayout from '../components/layout/AuthLayout'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'

export default function Signup() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!name || !email || !password || !confirm) {
      setError('Please fill in all fields.')
      return
    }
    if (password !== confirm) {
      setError("Passwords don't match.")
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    // Phase 1: mock – just navigate
    await new Promise((r) => setTimeout(r, 700))
    setLoading(false)
    navigate('/')
  }

  return (
    <AuthLayout>
      {/* Heading */}
      <h1
        className="font-display"
        style={{
          color: '#ffffff',
          fontSize: 'clamp(1.6rem, 4vw, 2.2rem)',
          fontWeight: 400,
          marginBottom: '1.75rem',
          textAlign: 'center',
        }}
      >
        Create account
      </h1>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}
        noValidate
      >
        <Input
          id="signup-name"
          label="FULL NAME"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoComplete="name"
          dark
          required
          style={{ minHeight: 48 }}
        />
        <Input
          id="signup-email"
          label="EMAIL"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          dark
          required
          style={{ minHeight: 48 }}
        />

        <div style={{ position: 'relative' }}>
          <Input
            id="signup-password"
            label="PASSWORD"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            dark
            required
            style={{ paddingRight: '44px', minHeight: 48 }}
          />
          <button
            type="button"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            onClick={() => setShowPassword((s) => !s)}
            style={{
              position: 'absolute',
              right: '12px',
              bottom: '12px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--on-dark-muted)',
              padding: '2px',
            }}
          >
            {showPassword ? <EyeOff size={15} strokeWidth={1.5} /> : <Eye size={15} strokeWidth={1.5} />}
          </button>
        </div>

        <Input
          id="signup-confirm"
          label="CONFIRM PASSWORD"
          type={showPassword ? 'text' : 'password'}
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          autoComplete="new-password"
          dark
          required
          style={{ minHeight: 48 }}
        />

        {error && (
          <p role="alert" style={{ color: 'var(--verdict-wait)', fontSize: '0.8rem', textAlign: 'center' }}>
            {error}
          </p>
        )}

        <Button
          type="submit"
          variant="primary-dark"
          fullWidth
          disabled={loading}
          style={{
            marginTop: '8px',
            letterSpacing: '0.12em',
            minHeight: 48,
            backgroundColor: 'var(--champagne)',
            color: '#000000',
          }}
        >
          {loading ? 'Creating account…' : 'CREATE ACCOUNT'}
        </Button>
      </form>

      {/* Footer links */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          marginTop: '1.25rem',
        }}
      >
        <Link
          to="/login"
          style={{ color: 'var(--champagne)', fontSize: '0.78rem', textDecoration: 'none', fontWeight: 600 }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--champagne-hover)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--champagne)')}
        >
          Already have an account? Sign in
        </Link>
      </div>
    </AuthLayout>
  )
}
