import React, { useState, useEffect } from 'react'
import { fetchPosts, fetchLogs } from '../lib/supabase'

export default function Analytics() {
  const [loading, setLoading] = useState(true)
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState({ total: 0, published: 0, rejected: 0, approvalRate: 0 })

  useEffect(() => {
    loadAnalyticsData()
  }, [])

  const loadAnalyticsData = async () => {
    setLoading(true)
    try {
      const [postsRes, logsRes] = await Promise.all([
        fetchPosts(null, 200),
        fetchLogs(50)
      ])

      const allPosts = postsRes.data || []
      const published = allPosts.filter(p => p.status === 'published').length
      const rejected = allPosts.filter(p => p.status === 'rejected').length
      const approved = allPosts.filter(p => p.status === 'approved' || p.status === 'published').length
      const totalDecided = approved + rejected

      setLogs(logsRes.data || [])
      setStats({
        total: allPosts.length,
        published,
        rejected,
        approvalRate: totalDecided > 0 ? Math.round((approved / totalDecided) * 100) : 100
      })
    } catch (err) {
      console.error('Error loading analytics:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /><p>Loading Analytics...</p></div>

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>System Analytics & Run Logs</h1>
          <p>Performance metrics, approval rates, and automation logs</p>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Generated</div>
          <div className="stat-value">{stats.total}</div>
          <div className="stat-icon">📊</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Published to IG</div>
          <div className="stat-value" style={{ color: 'var(--color-info)' }}>{stats.published}</div>
          <div className="stat-icon">📸</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Approval Rate</div>
          <div className="stat-value" style={{ color: 'var(--color-success)' }}>{stats.approvalRate}%</div>
          <div className="stat-icon">👍</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Rejected Posts</div>
          <div className="stat-value" style={{ color: 'var(--color-danger)' }}>{stats.rejected}</div>
          <div className="stat-icon">👎</div>
        </div>
      </div>

      {/* System Automation Run Logs */}
      <div className="card">
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>📋 Recent Automation Logs</h2>

        {logs.length === 0 ? (
          <p className="text-muted text-sm">No run logs recorded yet. Logs will populate as GitHub Actions runs.</p>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Workflow</th>
                  <th>Status</th>
                  <th>Message</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>{new Date(log.created_at).toLocaleString()}</td>
                    <td><strong style={{ color: '#fff' }}>{log.run_type}</strong></td>
                    <td>
                      <span className={`badge ${log.status === 'success' ? 'badge-approved' : 'badge-rejected'}`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="text-sm">{log.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
