import React, { useState, useEffect } from 'react'
import { fetchTopics, createTopic, updateTopic, deleteTopic } from '../lib/supabase'

export default function TopicManager() {
  const [topics, setTopics] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingTopic, setEditingTopic] = useState(null)
  const [formData, setFormData] = useState({ name: '', description: '', emoji: '💡', is_active: true })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadTopics()
  }, [])

  const loadTopics = async () => {
    setLoading(true)
    const { data } = await fetchTopics()
    setTopics(data || [])
    setLoading(false)
  }

  const handleOpenModal = (topic = null) => {
    if (topic) {
      setEditingTopic(topic)
      setFormData({ name: topic.name, description: topic.description || '', emoji: topic.emoji || '💡', is_active: topic.is_active })
    } else {
      setEditingTopic(null)
      setFormData({ name: '', description: '', emoji: '💡', is_active: true })
    }
    setModalOpen(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    if (editingTopic) {
      await updateTopic(editingTopic.id, formData)
    } else {
      await createTopic(formData)
    }
    setSaving(false)
    setModalOpen(false)
    loadTopics()
  }

  const handleToggleActive = async (topic) => {
    await updateTopic(topic.id, { is_active: !topic.is_active })
    loadTopics()
  }

  const handleDelete = async (id) => {
    if (confirm('Are you sure you want to delete this topic?')) {
      await deleteTopic(id)
      loadTopics()
    }
  }

  if (loading) {
    return <div className="loading-screen"><div className="loading-spinner" /><p>Loading Topics...</p></div>
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Topic Manager</h1>
          <p>Add, edit, or disable topics that the post generator uses</p>
        </div>
        <button className="btn btn-primary" onClick={() => handleOpenModal()}>
          ➕ Add New Topic
        </button>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Topic Name</th>
              <th>Description</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {topics.map((t) => (
              <tr key={t.id}>
                <td>
                  <span style={{ marginRight: 8, fontSize: 18 }}>{t.emoji}</span>
                  <strong>{t.name}</strong>
                </td>
                <td>{t.description || <span className="text-muted">No description</span>}</td>
                <td>
                  <button
                    className={`badge ${t.is_active ? 'badge-active' : 'badge-inactive'}`}
                    style={{ border: 'none', cursor: 'pointer' }}
                    onClick={() => handleToggleActive(t)}
                  >
                    {t.is_active ? '● Active' : '○ Disabled'}
                  </button>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <button className="btn btn-secondary btn-sm" style={{ marginRight: 6 }} onClick={() => handleOpenModal(t)}>
                    ✏️ Edit
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(t.id)}>
                    🗑️
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalOpen && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>{editingTopic ? 'Edit Topic' : 'Add New Topic'}</h2>
              <button className="modal-close" onClick={() => setModalOpen(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Emoji Icon</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.emoji}
                    onChange={(e) => setFormData({ ...formData, emoji: e.target.value })}
                    maxLength={2}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Topic Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Sports Motivation"
                    required
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Description / Context</label>
                <textarea
                  className="form-textarea"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describes what kind of quotes should be generated for this topic"
                />
              </div>
              <div className="toggle-wrapper mt-4">
                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  <span className="toggle-track"><span className="toggle-thumb" /></span>
                </label>
                <span className="toggle-label">Active (Include in generation pool)</span>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : 'Save Topic'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
