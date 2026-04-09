"""
PrijsMonitor - Backend API
FastAPI app met scraper, database en email alerts
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import db
from scraper import scrape_product
from emailer import stuur_prijs_alerts

app = FastAPI(title="PrijsMonitor API")

# Sta verbindingen toe van de frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wekelijkse cron job scheduler
scheduler = AsyncIOScheduler()


# ── Models ────────────────────────────────────────────────────────────────────

class ProductIn(BaseModel):
    naam: str
    url: str
    is_eigen_product: bool = False  # True = eigen product, False = concurrent

class EmailIn(BaseModel):
    email: str

class ScrapeResultaat(BaseModel):
    product_id: int
    prijs: Optional[float]
    verzendkosten: Optional[str]
    totaalprijs: Optional[float]
    fout: Optional[str]


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    await db.init()
    # Elke maandag om 08:00 automatisch scrapen
    scheduler.add_job(automatisch_scrapen, "cron", day_of_week="mon", hour=8, minute=0)
    scheduler.start()
    print("✓ PrijsMonitor API gestart")


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
    await db.close()


# ── Producten ─────────────────────────────────────────────────────────────────

@app.get("/producten")
async def get_producten():
    """Haal alle producten op met hun laatste prijs."""
    return await db.get_producten_met_prijzen()


@app.post("/producten")
async def voeg_product_toe(product: ProductIn):
    """Voeg een nieuw product toe."""
    product_id = await db.voeg_product_toe(product.naam, product.url, product.is_eigen_product)
    return {"id": product_id, "bericht": "Product toegevoegd"}


@app.delete("/producten/{product_id}")
async def verwijder_product(product_id: int):
    """Verwijder een product."""
    await db.verwijder_product(product_id)
    return {"bericht": "Product verwijderd"}


# ── Prijzen ───────────────────────────────────────────────────────────────────

@app.get("/prijzen/{product_id}")
async def get_prijshistoriek(product_id: int):
    """Haal de prijshistoriek op van één product."""
    return await db.get_prijshistoriek(product_id)


@app.post("/scrape")
async def manueel_scrapen(background_tasks: BackgroundTasks):
    """Start manueel een scrape van alle producten."""
    background_tasks.add_task(voer_scrape_uit)
    return {"bericht": "Scrape gestart, resultaten volgen zo dadelijk"}


@app.get("/laatste-scrape")
async def laatste_scrape():
    """Wanneer was de laatste scrape?"""
    return await db.get_laatste_scrape()


# ── Email adressen ────────────────────────────────────────────────────────────

@app.get("/emails")
async def get_emails():
    return await db.get_emails()


@app.post("/emails")
async def voeg_email_toe(data: EmailIn):
    await db.voeg_email_toe(data.email)
    return {"bericht": f"{data.email} toegevoegd"}


@app.delete("/emails/{email}")
async def verwijder_email(email: str):
    await db.verwijder_email(email)
    return {"bericht": f"{email} verwijderd"}


# ── Interne functies ──────────────────────────────────────────────────────────

async def automatisch_scrapen():
    """Wekelijkse automatische scrape (via cron job)."""
    print(f"[{datetime.now()}] Automatische wekelijkse scrape gestart...")
    await voer_scrape_uit()


async def voer_scrape_uit():
    """Scrape alle producten en sla prijzen op. Stuur alerts bij wijzigingen."""
    producten = await db.get_alle_producten()
    if not producten:
        print("Geen producten om te scrapen.")
        return

    wijzigingen = []

    for product in producten:
        print(f"  Scraping: {product['naam']}...")
        resultaat = await scrape_product(product["url"])

        oude_prijs = product.get("laatste_prijs")
        nieuwe_prijs = resultaat.get("totaalprijs") or resultaat.get("prijs")

        # Sla nieuwe prijs op
        if nieuwe_prijs:
            await db.sla_prijs_op(
                product_id=product["id"],
                prijs=resultaat.get("prijs"),
                verzendkosten=resultaat.get("verzendkosten"),
                totaalprijs=nieuwe_prijs,
                fout=resultaat.get("fout"),
            )

        # Controleer op prijswijziging (>0.01 verschil)
        if oude_prijs and nieuwe_prijs and abs(float(oude_prijs) - nieuwe_prijs) > 0.01:
            wijzigingen.append({
                "naam": product["naam"],
                "url": product["url"],
                "oude_prijs": oude_prijs,
                "nieuwe_prijs": nieuwe_prijs,
            })

        await asyncio.sleep(3)  # Beleefd scrapen

    # Stuur email alerts als er wijzigingen zijn
    if wijzigingen:
        emails = await db.get_emails()
        email_adressen = [e["email"] for e in emails]
        if email_adressen:
            await stuur_prijs_alerts(email_adressen, wijzigingen)
            print(f"  ✓ Alerts gestuurd naar {len(email_adressen)} personen")

    print(f"  ✓ Scrape klaar. {len(wijzigingen)} prijswijzigingen gevonden.")
