import { useState } from 'react'
import './PrijsTabel.css'

function formatPrijs(val) {
  if (val == null) return '—'
  return `€ ${parseFloat(val).toFixed(2).replace('.', ',')}`
}

function PrijsWijziging({ huidige, vorige }) {
  if (!huidige || !vorige) return null
  const diff = parseFloat(huidige) - parseFloat(vorige)
  if (Math.abs(diff) < 0.01) return null
  const stijging = diff > 0
  return (
    <span className={`badge ${stijging ? 'badge-up' : 'badge-down'}`}>
      {stijging ? '↑' : '↓'} {formatPrijs(Math.abs(diff))}
    </span>
  )
}

function formatDatum(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('nl-BE', {
    day: '2-digit', month: '2-digit', year: 'numeric'
  })
}

export default function PrijsTabel({ producten, onVerwijder }) {
  const [bevestigVerwijder, setBevestigVerwijder] = useState(null)

  const eigenProducten = producten.filter(p => p.is_eigen)
  const concurrenten = producten.filter(p => !p.is_eigen)

  // Goedkoopste concurrent prijs
  const goedkoopsteConcurrent = Math.min(
    ...concurrenten
      .filter(p => p.huidige_prijs)
      .map(p => parseFloat(p.huidige_prijs))
  )

  const handleVerwijder = (id) => {
    if (bevestigVerwijder === id) {
      onVerwijder(id)
      setBevestigVerwijder(null)
    } else {
      setBevestigVerwijder(id)
      setTimeout(() => setBevestigVerwijder(null), 3000)
    }
  }

  const renderRij = (product) => {
    const prijs = parseFloat(product.huidige_prijs)
    const isGoedkoopst = !product.is_eigen && prijs === goedkoopsteConcurrent && !isNaN(prijs)
    const isEigen = product.is_eigen

    return (
      <tr key={product.id} className={`rij ${isEigen ? 'rij-eigen' : ''}`}>
        <td className="cel-type">
          <span className={`tag ${isEigen ? 'tag-eigen' : 'tag-concurrent'}`}>
            {isEigen ? 'Eigen' : 'Concurrent'}
          </span>
        </td>
        <td className="cel-naam">
          <a href={product.url} target="_blank" rel="noopener noreferrer" className="product-link">
            {product.naam}
            <span className="link-icon">↗</span>
          </a>
        </td>
        <td className="cel-prijs">
          {product.huidige_prijs ? (
            <span className={`prijs-waarde ${isGoedkoopst ? 'goedkoopst' : ''}`}>
              {formatPrijs(product.huidige_prijs)}
              {isGoedkoopst && <span className="goedkoopst-badge">laagste</span>}
            </span>
          ) : (
            <span className="geen-prijs">
              {product.laatste_fout ? '⚠ Fout' : 'Nog niet gescraped'}
            </span>
          )}
        </td>
        <td className="cel-wijziging">
          <PrijsWijziging huidige={product.huidige_prijs} vorige={product.vorige_prijs} />
        </td>
        <td className="cel-datum mono">
          {formatDatum(product.laatste_update)}
        </td>
        <td className="cel-acties">
          <button
            className={`btn-verwijder ${bevestigVerwijder === product.id ? 'confirm' : ''}`}
            onClick={() => handleVerwijder(product.id)}
            title={bevestigVerwijder === product.id ? 'Klik nogmaals om te bevestigen' : 'Verwijderen'}
          >
            {bevestigVerwijder === product.id ? 'Zeker?' : '×'}
          </button>
        </td>
      </tr>
    )
  }

  return (
    <div className="tabel-wrapper">
      <table className="prijs-tabel">
        <thead>
          <tr>
            <th>Type</th>
            <th>Product</th>
            <th>Totaalprijs</th>
            <th>Wijziging</th>
            <th>Laatste update</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {eigenProducten.length > 0 && (
            <>
              <tr className="groep-header">
                <td colSpan={6}>Eigen producten</td>
              </tr>
              {eigenProducten.map(renderRij)}
            </>
          )}
          {concurrenten.length > 0 && (
            <>
              <tr className="groep-header">
                <td colSpan={6}>Concurrenten</td>
              </tr>
              {concurrenten.map(renderRij)}
            </>
          )}
        </tbody>
      </table>

      {/* Samenvatting */}
      {eigenProducten.length > 0 && concurrenten.length > 0 && (
        <div className="samenvatting">
          {eigenProducten.map(ep => {
            if (!ep.huidige_prijs || isNaN(goedkoopsteConcurrent)) return null
            const eigenPrijs = parseFloat(ep.huidige_prijs)
            const verschil = eigenPrijs - goedkoopsteConcurrent
            const pct = ((verschil / goedkoopsteConcurrent) * 100).toFixed(1)
            return (
              <div key={ep.id} className={`samenvatting-card ${verschil > 0 ? 'duurder' : 'goedkoper'}`}>
                <span className="samenvatting-label">
                  {ep.naam} vs goedkoopste concurrent:
                </span>
                <span className="samenvatting-waarde">
                  {verschil > 0 ? '↑' : '↓'} {formatPrijs(Math.abs(verschil))} ({verschil > 0 ? '+' : ''}{pct}%)
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
