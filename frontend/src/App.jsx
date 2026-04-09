import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { api } from './api'
import PrijsTabel from './components/PrijsTabel'
import ProductToevoegen from './components/ProductToevoegen'
import EmailBeheer from './components/EmailBeheer'
import './App.css'

export default function App() {
  const [producten, setProducten] = useState([])
  const [loading, setLoading] = useState(true)
  const [scraping, setScraping] = useState(false)
  const [actieveTab, setActieveTab] = useState('dashboard')
  const [laatsteScrape, setLaatsteScrape] = useState(null)

  const laadProducten = useCallback(async () => {
    try {
      const data = await api.getProducten()
      setProducten(data)
    } catch (e) {
      toast.error('Kon producten niet laden')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    laadProducten()
    api.getLaatsteScrape().then(setLaatsteScrape).catch(() => {})
  }, [laadProducten])

  const handleScrape = async () => {
    setScraping(true)
    try {
      await api.startScrape()
      toast.success('Scrape gestart! Resultaten verschijnen binnen enkele minuten.')
      // Herlaad na 30s
      setTimeout(() => {
        laadProducten()
        setScraping(false)
      }, 30000)
    } catch (e) {
      toast.error('Scrape mislukt')
      setScraping(false)
    }
  }

  const handleVerwijderProduct = async (id) => {
    try {
      await api.verwijderProduct(id)
      setProducten(p => p.filter(x => x.id !== id))
      toast.success('Product verwijderd')
    } catch {
      toast.error('Verwijderen mislukt')
    }
  }

  const formatDatum = (d) => {
    if (!d) return null
    return new Date(d).toLocaleDateString('nl-BE', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    })
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-mark">PM</span>
            <span className="logo-text">PrijsMonitor</span>
          </div>
          <nav className="nav">
            {['dashboard', 'producten', 'emails'].map(tab => (
              <button
                key={tab}
                className={`nav-btn ${actieveTab === tab ? 'active' : ''}`}
                onClick={() => setActieveTab(tab)}
              >
                {tab === 'dashboard' ? '📊 Overzicht' :
                 tab === 'producten' ? '➕ Producten' : '📧 Emails'}
              </button>
            ))}
          </nav>
          <button
            className={`scrape-btn ${scraping ? 'loading' : ''}`}
            onClick={handleScrape}
            disabled={scraping}
          >
            {scraping ? (
              <><span className="spinner" /> Scrapen...</>
            ) : (
              <> Prijzen ophalen</>
            )}
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="main">
        {actieveTab === 'dashboard' && (
          <>
            {/* Stats */}
            <div className="stats-row">
              <div className="stat">
                <span className="stat-num">{producten.filter(p => p.is_eigen).length}</span>
                <span className="stat-label">Eigen producten</span>
              </div>
              <div className="stat">
                <span className="stat-num">{producten.filter(p => !p.is_eigen).length}</span>
                <span className="stat-label">Concurrenten</span>
              </div>
              <div className="stat">
                <span className="stat-num">
                  {producten.filter(p => p.huidige_prijs).length}
                </span>
                <span className="stat-label">Prijzen gekend</span>
              </div>
              <div className="stat">
                <span className="stat-num mono">
                  {laatsteScrape?.gestart_op ? formatDatum(laatsteScrape.gestart_op) : '—'}
                </span>
                <span className="stat-label">Laatste update</span>
              </div>
            </div>

            {/* Tabel */}
            {loading ? (
              <div className="loading-state">
                <div className="spinner large" />
                <p>Producten laden...</p>
              </div>
            ) : producten.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📦</div>
                <h2>Nog geen producten</h2>
                <p>Voeg je eigen product en concurrenten toe via het tabblad <strong>Producten</strong>.</p>
                <button className="btn-primary" onClick={() => setActieveTab('producten')}>
                  Producten toevoegen →
                </button>
              </div>
            ) : (
              <PrijsTabel
                producten={producten}
                onVerwijder={handleVerwijderProduct}
              />
            )}
          </>
        )}

        {actieveTab === 'producten' && (
          <ProductToevoegen
            onToegevoegd={(p) => {
              setProducten(prev => [...prev, p])
              toast.success(`"${p.naam}" toegevoegd`)
              setActieveTab('dashboard')
            }}
          />
        )}

        {actieveTab === 'emails' && (
          <EmailBeheer />
        )}
      </main>
    </div>
  )
}
