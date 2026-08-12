import React, { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { signOut } from '../lib/supabase'
import '../styles/Sidebar.css'

const NAV_ITEMS = [
  { to: '/',          icon: '📊', label: 'Dashboard' },
  { to: '/queue',     icon: '📋', label: 'Post Queue' },
  { to: '/topics',    icon: '🏷️', label: 'Topics' },
  { to: '/tones',     icon: '🎭', label: 'Tones' },
  { to: '/schedule',  icon: '⏰', label: 'Schedule' },
  { to: '/analytics', icon: '📈', label: 'Analytics' },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <>
      <button
        id="sidebar-toggle"
        className="sidebar-hamburger"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label="Toggle sidebar"
      >
        {mobileOpen ? '✕' : '☰'}
      </button>

      {mobileOpen && (
        <div className="sidebar-backdrop" onClick={() => setMobileOpen(false)} />
      )}

      <aside className={`sidebar ${mobileOpen ? 'sidebar--open' : ''}`}>
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">📸</div>
          <div>
            <div className="sidebar-logo-title">IG AutoPoster</div>
            <div className="sidebar-logo-subtitle">Admin Panel</div>
          </div>
        </div>

        <nav className="sidebar-nav" role="navigation" aria-label="Main navigation">
          {NAV_ITEMS.map(({ to, icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `sidebar-nav-item ${isActive ? 'sidebar-nav-item--active' : ''}`
              }
              onClick={() => setMobileOpen(false)}
            >
              <span className="sidebar-nav-icon">{icon}</span>
              <span className="sidebar-nav-label">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-status">
            <span className="sidebar-status-dot" />
            <span className="sidebar-status-text">Automation Active</span>
          </div>
          <button
            id="sidebar-signout"
            className="sidebar-signout"
            onClick={handleSignOut}
          >
            <span>🚪</span>
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  )
}
