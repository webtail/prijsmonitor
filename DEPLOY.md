# 🚀 PrijsMonitor — Deploy Gids
> Geen technische kennis vereist. Volg deze stappen één voor één.

---

## Wat je nodig hebt (maak deze accounts aan, alles gratis of goedkoop)

| Dienst | Waarvoor | Kost |
|--------|----------|------|
| [github.com](https://github.com) | Code opslaan | Gratis |
| [railway.app](https://railway.app) | Website hosten | ~$5/maand |
| [resend.com](https://resend.com) | Emails versturen | Gratis |

---

## Stap 1 — Code op GitHub zetten

1. Ga naar [github.com](https://github.com) en maak een account aan
2. Klik op de groene knop **"New"** (rechtsboven)
3. Geef het de naam `prijsmonitor`
4. Klik op **"Create repository"**
5. Download [GitHub Desktop](https://desktop.github.com/) als je niet weet hoe git werkt
6. In GitHub Desktop: **File → Add local repository** → kies de map `prijsmonitor`
7. Klik op **"Publish repository"**

✅ Je code staat nu op GitHub.

---

## Stap 2 — Database aanmaken op Railway

1. Ga naar [railway.app](https://railway.app) en maak een account aan
2. Klik op **"New Project"**
3. Kies **"Provision PostgreSQL"**
4. Wacht even tot de database aangemaakt is
5. Klik op de database → tabblad **"Variables"**
6. Kopieer de waarde van **`DATABASE_URL`** — die heb je zo nodig

✅ Database is klaar.

---

## Stap 3 — Backend deployen op Railway

1. In je Railway project, klik op **"New"** → **"GitHub Repo"**
2. Selecteer je `prijsmonitor` repository
3. Railway vraagt welke map: kies **`backend`**
4. Wacht tot de deploy klaar is (duurt 2-3 minuten)
5. Ga naar **"Variables"** en voeg toe:

```
DATABASE_URL     → (de waarde die je in stap 2 gekopieerd hebt)
RESEND_API_KEY   → (zie stap 4 hieronder)
FROM_EMAIL       → alerts@jouwbedrijf.be
```

6. Na het toevoegen van de variabelen herstart Railway automatisch
7. Ga naar **"Settings"** → kopieer de **publieke URL**
   (ziet eruit als: `https://prijsmonitor-backend.up.railway.app`)

✅ Backend draait live.

---

## Stap 4 — Resend instellen (emails)

1. Ga naar [resend.com](https://resend.com) en maak een account aan
2. Ga naar **"API Keys"** → klik **"Create API Key"**
3. Geef het een naam (bijv. "PrijsMonitor") en klik op **"Add"**
4. Kopieer de API key (begint met `re_`)
5. Plak deze als `RESEND_API_KEY` in Railway (stap 3)

**Optioneel maar aanbevolen:** Voeg je eigen domein toe in Resend zodat emails verstuurd worden vanaf `alerts@jouwbedrijf.be` in plaats van een Resend adres.

✅ Emails zijn klaar.

---

## Stap 5 — Frontend deployen op Railway

1. In je Railway project, klik nogmaals op **"New"** → **"GitHub Repo"**
2. Selecteer opnieuw je `prijsmonitor` repository
3. Kies nu de map **`frontend`**
4. Ga naar **"Variables"** en voeg toe:

```
VITE_API_URL  →  (de URL van je backend uit stap 3)
```

5. Wacht tot de deploy klaar is
6. Ga naar **"Settings"** → kopieer de **publieke URL** van de frontend
   (ziet eruit als: `https://prijsmonitor-frontend.up.railway.app`)

✅ De tool is live!

---

## Stap 6 — De tool gebruiken

1. Open de frontend URL in je browser
2. Ga naar **"Producten"** en voeg je eigen product toe:
   - Naam: `HBM 200 Motorheftafel Zwart`
   - URL: `https://www.hbm-machines.com/be-nl/p/hbm-200-motorheftafel-zwart`
   - Type: **Eigen product**
3. Voeg ook de concurrent URL's toe (type: **Concurrent**)
4. Ga naar **"Emails"** en voeg de emailadressen toe van je collega's
5. Klik op **"Prijzen ophalen"** om de eerste scrape te starten
6. Na ~1 minuut verschijnen de prijzen in de tabel

---

## Stap 7 — Link delen met collega's

Stuur simpelweg de frontend URL door naar je collega's:
`https://prijsmonitor-frontend.up.railway.app`

Iedereen met de link kan de tool gebruiken. Geen login nodig.

---

## Veelgestelde vragen

**De prijs verschijnt niet, wat nu?**
→ Sommige sites blokkeren scrapers. Klik op het product in de tabel om de foutmelding te zien. Neem dan contact op als je hulp nodig hebt.

**Kan ik meer dan één eigen product toevoegen?**
→ Ja, je kan zoveel producten toevoegen als je wil.

**Hoe pas ik de dag/tijd van de wekelijkse scrape aan?**
→ In `backend/main.py` zoek je naar `"cron"` en pas je `day_of_week` en `hour` aan. Na aanpassing push je naar GitHub en Railway herstart automatisch.

**Iets werkt niet na een aanpassing aan de code?**
→ Push de wijziging naar GitHub. Railway detecteert dit automatisch en herdeployt.
