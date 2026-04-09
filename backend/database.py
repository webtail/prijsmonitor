"""
Database module - PostgreSQL via asyncpg
Beheert producten, prijzen en email adressen
"""

import os
import asyncpg
from datetime import datetime
from typing import Optional


class Database:
    def __init__(self):
        self.pool = None

    async def init(self):
        """Maak verbinding met de database en maak tabellen aan."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL omgevingsvariabele ontbreekt")

        # Railway geeft postgres:// maar asyncpg verwacht postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        self.pool = await asyncpg.create_pool(database_url)
        await self._maak_tabellen_aan()
        print("✓ Database verbonden")

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def _maak_tabellen_aan(self):
        """Maak alle tabellen aan als ze nog niet bestaan."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS producten (
                    id          SERIAL PRIMARY KEY,
                    naam        TEXT NOT NULL,
                    url         TEXT NOT NULL UNIQUE,
                    is_eigen    BOOLEAN DEFAULT FALSE,
                    aangemaakt  TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS prijzen (
                    id              SERIAL PRIMARY KEY,
                    product_id      INT REFERENCES producten(id) ON DELETE CASCADE,
                    prijs           NUMERIC(10,2),
                    verzendkosten   TEXT,
                    totaalprijs     NUMERIC(10,2),
                    fout            TEXT,
                    gescraped_op    TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS emails (
                    id      SERIAL PRIMARY KEY,
                    email   TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS scrape_log (
                    id          SERIAL PRIMARY KEY,
                    gestart_op  TIMESTAMP DEFAULT NOW(),
                    klaar_op    TIMESTAMP,
                    aantal      INT DEFAULT 0
                );
            """)

    # ── Producten ─────────────────────────────────────────────────────────────

    async def voeg_product_toe(self, naam: str, url: str, is_eigen: bool) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO producten (naam, url, is_eigen) VALUES ($1, $2, $3) "
                "ON CONFLICT (url) DO UPDATE SET naam=$1 RETURNING id",
                naam, url, is_eigen
            )
            return row["id"]

    async def get_alle_producten(self) -> list:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT p.id, p.naam, p.url, p.is_eigen,
                       (SELECT totaalprijs FROM prijzen
                        WHERE product_id = p.id
                        ORDER BY gescraped_op DESC LIMIT 1) as laatste_prijs,
                       (SELECT gescraped_op FROM prijzen
                        WHERE product_id = p.id
                        ORDER BY gescraped_op DESC LIMIT 1) as laatste_scrape
                FROM producten p
                ORDER BY p.is_eigen DESC, p.naam
            """)
            return [dict(r) for r in rows]

    async def get_producten_met_prijzen(self) -> list:
        """Haal producten op met hun volledige prijshistoriek."""
        async with self.pool.acquire() as conn:
            producten = await conn.fetch("""
                SELECT p.id, p.naam, p.url, p.is_eigen,
                       (SELECT totaalprijs FROM prijzen
                        WHERE product_id = p.id
                        ORDER BY gescraped_op DESC LIMIT 1) as huidige_prijs,
                       (SELECT totaalprijs FROM prijzen
                        WHERE product_id = p.id
                        ORDER BY gescraped_op DESC LIMIT 1 OFFSET 1) as vorige_prijs,
                       (SELECT gescraped_op FROM prijzen
                        WHERE product_id = p.id
                        ORDER BY gescraped_op DESC LIMIT 1) as laatste_update,
                       (SELECT fout FROM prijzen
                        WHERE product_id = p.id
                        ORDER BY gescraped_op DESC LIMIT 1) as laatste_fout
                FROM producten p
                ORDER BY p.is_eigen DESC, p.naam
            """)
            return [dict(r) for r in producten]

    async def verwijder_product(self, product_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM producten WHERE id = $1", product_id)

    # ── Prijzen ───────────────────────────────────────────────────────────────

    async def sla_prijs_op(
        self,
        product_id: int,
        prijs: Optional[float],
        verzendkosten: Optional[str],
        totaalprijs: Optional[float],
        fout: Optional[str] = None,
    ):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO prijzen (product_id, prijs, verzendkosten, totaalprijs, fout)
                   VALUES ($1, $2, $3, $4, $5)""",
                product_id, prijs, verzendkosten, totaalprijs, fout
            )

    async def get_prijshistoriek(self, product_id: int) -> list:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT prijs, verzendkosten, totaalprijs, fout, gescraped_op
                   FROM prijzen WHERE product_id = $1
                   ORDER BY gescraped_op DESC LIMIT 52""",
                product_id
            )
            return [dict(r) for r in rows]

    async def get_laatste_scrape(self) -> dict:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM scrape_log ORDER BY gestart_op DESC LIMIT 1"
            )
            return dict(row) if row else {"gestart_op": None}

    # ── Emails ────────────────────────────────────────────────────────────────

    async def get_emails(self) -> list:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT email FROM emails ORDER BY id")
            return [dict(r) for r in rows]

    async def voeg_email_toe(self, email: str):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO emails (email) VALUES ($1) ON CONFLICT DO NOTHING",
                email
            )

    async def verwijder_email(self, email: str):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM emails WHERE email = $1", email)


# Singleton instantie
db = Database()
