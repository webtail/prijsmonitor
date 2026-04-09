import { useState } from 'react'
import { api } from '../api'
import toast from 'react-hot-toast'
import './ProductToevoegen.css'

export default function ProductToevoegen({ onToegevoegd }) {
  const [naam, setNaam] = useState('')
  const [url, setUrl] = useState('')
  const [isEigen, setIsEigen] = useState(false)
  const [bezig, setBezig] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!naam.trim() || !url.trim()) {
      toast.error('Vul naam en URL in')
      return
    }
    if (!url.startsWith('http')) {
      toast.error('URL moet beginnen met http:// of https://')
      return
    }

    setBezig(true)
    try {
      const result = await api.voegProductToe({
        naam: naam.trim(),
        url: url.trim(),
        is_eigen_product: isEigen,
      })
      onToegevoegd({ id: result.id, naam: naam.trim(), url: url.trim(), is_eigen: isEigen })
      setNaam('')
      setUrl('')
      setIsEigen(false)
    } catch (e) {
      toast.error('Toevoegen mislukt. URL bestaat misschien al.')
    } finally {
      setBezig(false)
    }
  }

  return (
    <div className="toevoegen-wrapper">
      <div className="toevoegen-card">
        <h2>Product toevoegen</h2>
        <p className="toevoegen-intro">
          Voeg je eigen product of een concurrent toe. Na het toevoegen klik je op
          <strong> "Prijzen ophalen"</strong> om de actuele prijzen op te halen.
        </p>

        <form onSubmit={handleSubmit} className="toevoegen-form">
          {/* Type selector */}
          <div className="type-selector">
            <button
              type="button"
              className={`type-btn ${!isEigen ? 'active' : ''}`}
              onClick={() => setIsEigen(false)}
            >
              <span className="type-icon">🏪</span>
              <span>Concurrent</span>
            </button>
            <button
              type="button"
              className={`type-btn ${isEigen ? 'active' : ''}`}
              onClick={() => setIsEigen(true)}
            >
              <span className="type-icon">⭐</span>
              <span>Eigen product</span>
            </button>
          </div>

          <div className="form-group">
            <label>Naam</label>
            <input
              type="text"
              placeholder={isEigen ? 'bijv. HBM 200 Motorheftafel Zwart' : 'bijv. Concurrent product X'}
              value={naam}
              onChange={e => setNaam(e.target.value)}
              autoFocus
            />
          </div>

          <div className="form-group">
            <label>Product URL</label>
            <input
              type="url"
              placeholder="https://www.webshop.com/product/..."
              value={url}
              onChange={e => setUrl(e.target.value)}
            />
            <span className="hint">De directe link naar de productpagina</span>
          </div>

          <button type="submit" className="btn-submit" disabled={bezig}>
            {bezig ? <><span className="spinner" /> Toevoegen...</> : 'Product toevoegen →'}
          </button>
        </form>
      </div>

      <div className="tips-card">
        <h3>Tips</h3>
        <ul>
          <li>Voeg de directe productpagina URL toe, niet de homepage</li>
          <li>Je kan meerdere eigen producten en concurrenten toevoegen</li>
          <li>Prijzen worden elke maandag automatisch bijgewerkt</li>
          <li>Je krijgt een email als er een prijs verandert</li>
        </ul>
      </div>
    </div>
  )
}
