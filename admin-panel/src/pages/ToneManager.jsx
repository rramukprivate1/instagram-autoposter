import React, { useState, useEffect } from 'react'
import { fetchTones, createTone, updateTone, deleteTone } from '../lib/supabase'

export default function ToneManager() {
  const [tones, setTones] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingTone, setEditingTone] = useState(null)
  const [formData, setFormData] = useState({ name: '', description: '', example: '', is_active: true })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadTones()
  }, [])

  const loadTones = async () => {
    setLoading(true)
    const { data } = await fetchTones()
    setTones(data || [])
    setLoading(false)
  }

  const handleOpenModal = (tone = null) => {
    if (tone) {
      setEditingTone(tone)
      setFormData({ name: tone.name, description: tone.description || '', example: tone.example || '', is_active: tone.is_active })
    } else {
      setEditingTone(null)
      setFormData({ name: '', description: '', example: '', is_active: true })
    }
    setModalOpen(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    if (editingTone) {
      await updateTone(editingTone.id, formData)
    } else {
      await createTone(formData)
    }
    setSaving(false)
    setModalOpen(false)
    loadTones()
  }

  const handleToggleActive = async (tone) => {
    await updateTone(tone.id, { is_active: !tone.is_active })
    loadTones()
  }

  const handleDelete = async (id) => {
    if (confirm('Delete this tone preset?')) {
      await deleteTone(id)
      loadTones()
    }
  }

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /><p>Loading Tones...</p></div>

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Tone & Context Manager</h1>
          <p>Configure emotional tone presets (Teacher, Friend, Parent, Raw, Advisor)</p>
        </div>
        <button className="btn btn-primary" onClick={() => handleOpenModal()}>
          ➕ Add New Tone Preset
        </button>
      </div>

      <div className="post-grid">
        {tones.map((t) => (
          <div key={t.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 style={{ fontSize: 18, fontWeight: 700 }}>🎭 {t.name}</h3>
                <button
                  className={`badge ${t.is_active ? 'badge-active' : 'badge-inactive'}`}
                  style={{ border: 'none', cursor: 'pointer' }}
                  onClick={() => handleToggleActive(t)}
                >
                  {t.is_active ? 'Active' : 'Disabled'}
                </button>
              </div>
              <p className="text-sm text-muted mb-4">{t.description}</p>
              {t.example && (
                <div style={{ background: 'var(--color-surface-2)', padding: '12px', borderRadius: '8px', fontSize: 13, fontStyle: 'italic', marginBottom: 16 }}>
                  &ldquo;{t.example}&rdquo;
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <button className="btn btn-secondary btn-sm" style={{ flex: 1 }} onClick={() => handleOpenModal(t)}>✏️ Edit</button>
              <button className="btn btn-danger btn-sm" onClick={() => handleDelete(t.id)}>🗑️</button>
            </div>
          </div>
        ))}
      </div>

      {modalOpen && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>{editingTone ? 'Edit Tone Preset' : 'Add New Tone Preset'}</h2>
              <button className="modal-close" onClick={() => setModalOpen(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Tone Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Tough Love Coach"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Tone Guidelines / Prompt Instruction</label>
                <textarea
                  className="form-textarea"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe how the AI should adopt this persona (e.g. Raw, direct, no sugarcoating)"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Example Phrase (Optional)</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.example}
                  onChange={(e) => setFormData({ ...formData, example: e.target.value })}
                  placeholder="An example of how a post in this tone should sound"
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
                  {saving ? 'Saving...' : 'Save Tone'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
