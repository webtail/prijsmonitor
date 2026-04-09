import { useState, useEffect } from 'react'
import { api } from '../api'
import toast from 'react-hot-toast'
import './EmailBeheer.css'

export default function EmailBeheer() {
  const [emails, setEmails] = useState([])
  const [nieuwEmail, setNieuwEmail] = useState('')
  const [bezig, setBezig] = useState(false)
  const [laden, setLaden] = useState(true)

  useEffect(() => {
    api.getEmails()
      .then(data => setEmails(data))
      .catch(() => toast.error('Kon emails niet laden'))
      .finally(() => setLaden(false))
  }, [])

  const handleToevoegen = async (e) => {
    e.preventDefault()
    if (!nieuwEmail.trim() || !nieuwEmail.includes('@')) {
      toast.error('Voer een geldig emailadres in')
      return
    }
    setBezig(true)
    try {
      await api.voegEmailToe(nieuwEmail.trim())
      setEmails(prev => [...prev, { email: nieuwEmail.trim() }])
      setNieuwEmail('')
      toast.success(`${nieuwEmail} toegevoegd`)
    } catch {
      toast.error('Toevoegen mislukt. Email bestaat mogelijk al.')
    } finally {
      setBezig(false)
    }
  }

  const handleVerwijder = async (email) => {
    try {
      await api.verwijderEmail(email)
      setEmails(prev => prev.filter(e => e.email !== email))
      toast.success('Email verwijderd')
    } catch {
      toast.error('Verwijderen mislukt')
    }
  }

  return (
    <div className="email-wrapper">
      <div className="email-card">
        <h2>Email alerts</h2>
        <p className="email-intro">
          Iedereen op deze lijst krijgt automatisch een email als er een prijs wijzigt.
          Alerts worden verstuurd elke maandag na de wekelijkse prijscheck.
        </p>

        <form onSubmit={handleToevoegen} className="email-form">
          <input
            type="email"
            placeholder="naam@bedrijf.be"
            value={nieuwEmail}
            onChange={e => setNieuwEmail(e.target.value)}
            autoFocus
          />
          <button type="submit" className="btn-toevoegen" disabled={bezig}>
            {bezig ? <span className="spinner" /> : '+ Toevoegen'}
          </button>
        </form>

        <div className="email-lijst">
          {laden ? (
            <div className="email-laden"><span className="spinner" /></div>
          ) : emails.length === 0 ? (
            <div className="email-leeg">
              <span>📭</span>
              <p>Nog geen emailadressen toegevoegd.</p>
            </div>
          ) : (
            emails.map(({ email }) => (
              <div key={email} className="email-rij">
                <span className="email-icon">✉</span>
                <span className="email-adres">{email}</span>
                <button
                  className="btn-verwijder-email"
                  onClick={() => handleVerwijder(email)}
                  title="Verwijderen"
                >
                  ×
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="email-info-card">
        <h3>Wanneer krijg je een email?</h3>
        <div className="info-item">
          <span className="info-icon">📅</span>
          <div>
            <strong>Elke maandag</strong>
            <p>De tool controleert automatisch alle prijzen wekelijks op maandag om 08:00.</p>
          </div>
        </div>
        <div className="info-item">
          <span className="info-icon">💰</span>
          <div>
            <strong>Alleen bij wijziging</strong>
            <p>Je krijgt alleen een email als er effectief een prijs veranderd is.</p>
          </div>
        </div>
        <div className="info-item">
          <span className="info-icon">📊</span>
          <div>
            <strong>Wat staat erin?</strong>
            <p>Een tabel met het product, de oude prijs, de nieuwe prijs en het verschil.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
