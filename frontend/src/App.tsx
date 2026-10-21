import { Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import Layout from './components/layout/Layout'

// Lazy-loaded pages for route-level code splitting
const Splash = lazy(() => import('./pages/Splash'))
const Home = lazy(() => import('./pages/Home'))
const Login = lazy(() => import('./pages/Login'))
const Signup = lazy(() => import('./pages/Signup'))
const NotFound = lazy(() => import('./pages/NotFound'))

/** Show splash once per session, then redirect to home */
function RootRedirect() {
  const splashDone = sessionStorage.getItem('splash_done')
  if (!splashDone) {
    return <Navigate to="/__splash" replace />
  }
  return <Home />
}

function App() {
  return (
    <Suspense fallback={null}>
      <Routes>
        {/* Splash is standalone, no layout */}
        <Route path="/__splash" element={<Splash />} />
        {/* Login / signup standalone (dark full-page) */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        {/* Main layout */}
        <Route element={<Layout />}>
          <Route path="/" element={<RootRedirect />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  )
}

export default App
