"""
Database module - PostgreSQL via psycopg2
"""

import os
import psycopg2
import psycopg2.extras
from typing import Optional


def get_conn():
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url)


class Database:
    def __init__(self):
        pass

    async def init(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
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
        conn.commit()
        cur.close()
        conn.close()
        print("✓ Database verbonden")

    async def close(self):
        pass

    async def voeg_product_toe(self, naam, url, is_eigen):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO producten (naam, url, is_eigen) VALUES (%s, %s, %s) "
            "ON CONFLICT (url) DO UPDATE SET naam=%s RETURNING id",
            (naam, url, is_eigen, naam)
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return row[0]

    async def get_alle_producten(self):
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT p.id, p.naam, p.url, p.is_eigen,
                   (SELECT totaalprijs FROM prijzen WHERE product_id = p.id ORDER BY gescraped_op DESC LIMIT 1) as laatste_prijs,
                   (SELECT gescraped_op FROM prijzen WHERE product_id = p.id ORDER BY gescraped_op DESC LIMIT 1) as laatste_scrape
            FROM producten p ORDER BY p.is_eigen DESC, p.naam
        """)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    async def get_producten_met_prijzen(self):
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT p.id, p.naam, p.url, p.is_eigen,
                   (SELECT totaalprijs FROM prijzen WHERE product_id = p.id ORDER BY gescraped_op DESC LIMIT 1) as huidige_prijs,
                   (SELECT totaalprijs FROM prijzen WHERE product_id = p.id ORDER BY gescraped_op DESC LIMIT 1 OFFSET 1) as vorige_prijs,
                   (SELECT gescraped_op FROM prijzen WHERE product_id = p.id ORDER BY gescraped_op DESC LIMIT 1) as laatste_update,
                   (SELECT fout FROM prijzen WHERE product_id = p.id ORDER BY gescraped_op DESC LIMIT 1) as laatste_fout
            FROM producten p ORDER BY p.is_eigen DESC, p.naam
        """)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    async def verwijder_product(self, product_id):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM producten WHERE id = %s", (product_id,))
        conn.commit()
        cur.close()
        conn.close()

    async def sla_prijs_op(self, product_id, prijs, verzendkosten, totaalprijs, fout=None):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO prijzen (product_id, prijs, verzendkosten, totaalprijs, fout) VALUES (%s, %s, %s, %s, %s)",
            (product_id, prijs, verzendkosten, totaalprijs, fout)
        )
        conn.commit()
        cur.close()
        conn.close()

    async def get_prijshistoriek(self, product_id):
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT prijs, verzendkosten, totaalprijs, fout, gescraped_op FROM prijzen WHERE product_id = %s ORDER BY gescraped_op DESC LIMIT 52",
            (product_id,)
        )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    async def get_laatste_scrape(self):
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM scrape_log ORDER BY gestart_op DESC LIMIT 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else {"gestart_op": None}

    async def get_emails(self):
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT email FROM emails ORDER BY id")
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    async def voeg_email_toe(self, email):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO emails (email) VALUES (%s) ON CONFLICT DO NOTHING", (email,))
        conn.commit()
        cur.close()
        conn.close()

    async def verwijder_email(self, email):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM emails WHERE email = %s", (email,))
        conn.commit()
        cur.close()
        conn.close()


db = Database()
