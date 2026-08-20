import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { supabase } from './lib/supabase'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import TopicManager from './pages/TopicManager'
import ToneManager from './pages/ToneManager'
import ScheduleSettings from './pages/ScheduleSettings'
import PostQueue from './pages/PostQueue'
import Analytics from './pages/Analytics'
import Sidebar from './components/Sidebar'
import './styles/index.css'

function ProtectedLayout({ children }) {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="app-main">
        {children}
      </main>
    </div>
  )
}

export default function App() {
  const [session, setSession] = useState(undefined)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
    })
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })
    return () => subscription.unsubscribe()
  }, [])

  if (session === undefined) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={session ? <Navigate to="/" replace /> : <Login />}
        />
        <Route
          path="/"
          element={
            session ? (
              <ProtectedLayout><Dashboard /></ProtectedLayout>
            ) : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/topics"
          element={
            session ? (
              <ProtectedLayout><TopicManager /></ProtectedLayout>
            ) : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/tones"
          element={
            session ? (
              <ProtectedLayout><ToneManager /></ProtectedLayout>
            ) : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/schedule"
          element={
            session ? (
              <ProtectedLayout><ScheduleSettings /></ProtectedLayout>
            ) : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/queue"
          element={
            session ? (
              <ProtectedLayout><PostQueue /></ProtectedLayout>
            ) : <Navigate to="/login" replace />
          }
        />
        <Route
          path="/analytics"
          element={
            session ? (
              <ProtectedLayout><Analytics /></ProtectedLayout>
            ) : <Navigate to="/login" replace />
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
