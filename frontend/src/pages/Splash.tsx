import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

/** Shown once per session, then redirects to Home. Press any key or click to skip. */
export default function Splash() {
  const navigate = useNavigate()

  useEffect(() => {
    // Skip if already shown this session
    if (sessionStorage.getItem('splash_done')) {
      navigate('/', { replace: true })
      return
    }

    const timer = setTimeout(() => {
      sessionStorage.setItem('splash_done', '1')
      navigate('/', { replace: true })
    }, 2400)

    function skip() {
      clearTimeout(timer)
      sessionStorage.setItem('splash_done', '1')
      navigate('/', { replace: true })
    }

    document.addEventListener('keydown', skip)
    document.addEventListener('click', skip)

    return () => {
      clearTimeout(timer)
      document.removeEventListener('keydown', skip)
      document.removeEventListener('click', skip)
    }
  }, [navigate])

  const letters = 'URBANPICK'.split('')

  return (
    <div
      aria-label="Loading UrbanPick"
      role="status"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'var(--ink-900)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '16px',
      }}
    >
      {/* Staggered wordmark */}
      <motion.div
        style={{ display: 'flex' }}
        initial="hidden"
        animate="visible"
        variants={{
          visible: { transition: { staggerChildren: 0.06 } },
        }}
        aria-label="URBANPICK"
      >
        {letters.map((letter, i) => (
          <motion.span
            key={i}
            variants={{
              hidden: { opacity: 0, y: 16 },
              visible: {
                opacity: 1,
                y: 0,
                transition: { duration: 0.5, ease: [0.22, 0.1, 0.36, 1] },
              },
            }}
            style={{
              fontFamily: 'Bodoni Moda, Georgia, serif',
              fontSize: '1.6rem',
              letterSpacing: '0.28em',
              color: 'var(--on-dark)',
              fontWeight: 400,
            }}
          >
            {letter}
          </motion.span>
        ))}
      </motion.div>

      {/* Champagne rule */}
      <motion.div
        initial={{ scaleX: 0, originX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ delay: 0.7, duration: 0.6, ease: [0.22, 0.1, 0.36, 1] }}
        style={{
          height: 1,
          width: 120,
          backgroundColor: 'var(--champagne)',
          transformOrigin: 'left',
        }}
      />

      {/* Tagline */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.4, duration: 0.5 }}
        style={{
          fontFamily: 'Manrope, sans-serif',
          fontSize: '0.8rem',
          color: 'var(--on-dark-muted)',
          letterSpacing: '0.12em',
        }}
      >
        Every category, one smart search.
      </motion.p>
    </div>
  )
}
