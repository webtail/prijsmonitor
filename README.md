# PrijsMonitor

Vergelijk je eigen productprijzen met die van concurrenten. Automatische wekelijkse prijscheck met email alerts bij wijzigingen.

## Functies
- Eigen product én concurrenten naast elkaar in één tabel
- Prijs + verzendkosten = totaalprijs
- Goedkoopste concurrent automatisch gemarkeerd
- Wekelijkse automatische prijscheck (elke maandag)
- Email alert als een prijs wijzigt
- Prijshistoriek bijgehouden

## Tech stack
- **Frontend**: React + Vite
- **Backend**: FastAPI + Python
- **Scraper**: Playwright (Chromium)
- **Database**: PostgreSQL
- **Email**: Resend
- **Hosting**: Railway

## Deploy
Zie [DEPLOY.md](./DEPLOY.md) voor de volledige stap-voor-stap gids.

## Structuur
```
prijsmonitor/
├── backend/
│   ├── main.py          # API endpoints
│   ├── database.py      # Database logica
│   ├── scraper.py       # Playwright scraper
│   ├── emailer.py       # Email alerts
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/
│   │       ├── PrijsTabel.jsx
│   │       ├── ProductToevoegen.jsx
│   │       └── EmailBeheer.jsx
│   ├── package.json
│   └── .env.example
└── DEPLOY.md
```
