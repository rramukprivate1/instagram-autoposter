import React, { useState } from 'react'
import { signIn } from '../lib/supabase'
import '../styles/Login.css'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    const { error } = await signIn(email, password)
    if (error) {
      setError(error.message)
    }
    setLoading(false)
  }

  return (
    <div className="login-page">
      <div className="login-glow login-glow-1" />
      <div className="login-glow login-glow-2" />

      <div className="login-card">
        <div className="login-logo">
          <div className="login-logo-icon">📸</div>
          <h1 className="login-title">IG AutoPoster</h1>
          <p className="login-subtitle">Admin Dashboard · Sign in to continue</p>
        </div>

        {error && (
          <div id="login-error" className="alert alert-error">
            <span>⚠️</span> {error}
          </div>
        )}

        <form id="login-form" onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="login-email" className="form-label">Email</label>
            <input
              id="login-email"
              type="email"
              className="form-input"
              placeholder="admin@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="login-password" className="form-label">Password</label>
            <input
              id="login-password"
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          <button
            id="login-submit"
            type="submit"
            className="btn btn-primary btn-lg w-full"
            disabled={loading}
          >
            {loading ? 'Signing in...' : '🔐 Sign In'}
          </button>
        </form>

        <p className="login-footer">
          Instagram Auto-Poster &bull; For authorized admin use only
        </p>
      </div>
    </div>
  )
}
