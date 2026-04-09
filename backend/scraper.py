"""
Scraper module - Playwright met stealth technieken
Haalt prijs + verzendkosten op van elke webshop URL
"""

import re
import json
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['nl-BE', 'nl', 'fr'] });
window.chrome = { runtime: {} };
"""


def parse_prijs(tekst: str) -> Optional[float]:
    """Zet prijstekst om naar float. Bijv. '€ 1.299,00' → 1299.0"""
    if not tekst:
        return None
    tekst = re.sub(r"[€$£\s\u00a0]", "", tekst.strip())
    if "," in tekst and "." in tekst:
        tekst = tekst.replace(".", "").replace(",", ".")
    elif "," in tekst:
        tekst = tekst.replace(",", ".")
    try:
        val = float(tekst)
        return val if val > 0 else None
    except ValueError:
        return None


async def scrape_product(url: str) -> dict:
    """
    Scrape één product URL.
    Geeft dict terug met: naam, prijs, verzendkosten, totaalprijs, fout
    """
    resultaat = {
        "url": url,
        "naam": None,
        "prijs": None,
        "prijs_raw": None,
        "verzendkosten": None,
        "totaalprijs": None,
        "fout": None,
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            locale="nl-BE",
            timezone_id="Europe/Brussels",
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            extra_http_headers={
                "Accept-Language": "nl-BE,nl;q=0.9,fr;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        page = await context.new_page()
        await page.add_init_script(STEALTH_SCRIPT)

        try:
            resp = await page.goto(url, wait_until="networkidle", timeout=40000)
            if resp and resp.status == 403:
                resultaat["fout"] = "403 - Geblokkeerd (Cloudflare)"
                return resultaat
            if resp and resp.status >= 400:
                resultaat["fout"] = f"HTTP fout {resp.status}"
                return resultaat

            await page.wait_for_timeout(2000)

            # ── Productnaam ───────────────────────────────────────────────
            for sel in ["h1.product-name", "h1[class*='product']", "h1[class*='title']", "h1"]:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0:
                        naam = (await el.text_content() or "").strip()
                        if naam:
                            resultaat["naam"] = naam
                            break
                except Exception:
                    continue

            # ── Prijs ophalen ─────────────────────────────────────────────
            prijs_selectors = [
                "[data-price-type='finalPrice'] .price",
                ".price-box .price",
                ".special-price .price",
                "[class*='product-price']",
                "[class*='current-price']",
                "[class*='price--current']",
                "[class*='price--sale']",
                ".price",
            ]
            for sel in prijs_selectors:
                try:
                    els = page.locator(sel)
                    count = await els.count()
                    for i in range(min(count, 5)):
                        tekst = await els.nth(i).text_content()
                        if tekst and "€" in tekst:
                            val = parse_prijs(tekst)
                            if val and val > 0:
                                resultaat["prijs_raw"] = tekst.strip()
                                resultaat["prijs"] = val
                                break
                    if resultaat["prijs"]:
                        break
                except Exception:
                    continue

            # Fallback: JSON-LD structured data
            if not resultaat["prijs"]:
                try:
                    scripts = await page.locator("script[type='application/ld+json']").all()
                    for script in scripts:
                        content = await script.text_content()
                        data = json.loads(content)
                        items = data if isinstance(data, list) else [data]
                        for item in items:
                            offers = item.get("offers", {})
                            if isinstance(offers, list):
                                offers = offers[0] if offers else {}
                            prijs_val = offers.get("price") or item.get("price")
                            if prijs_val:
                                resultaat["prijs"] = float(prijs_val)
                                resultaat["prijs_raw"] = f"€ {prijs_val}"
                                break
                        if resultaat["prijs"]:
                            break
                except Exception:
                    pass

            # ── Verzendkosten ─────────────────────────────────────────────
            verzend_selectors = [
                "[class*='shipping']", "[class*='delivery']",
                "[class*='verzend']", "[class*='levering']",
                ".shipping-cost", ".delivery-info",
            ]
            for sel in verzend_selectors:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0:
                        tekst = (await el.text_content() or "").strip()
                        if tekst and len(tekst) < 100:
                            resultaat["verzendkosten"] = tekst
                            break
                except Exception:
                    continue

            # Fallback: zoek in paginatekst
            if not resultaat["verzendkosten"]:
                try:
                    body = await page.locator("body").text_content()
                    for pattern in [
                        r"(gratis verzend\w*)",
                        r"(free shipping)",
                        r"verzend(?:kosten)?[:\s]+([\d€,.\s]+)",
                        r"levering[:\s]+([\d€,.\s]+)",
                    ]:
                        m = re.search(pattern, body or "", re.IGNORECASE)
                        if m:
                            resultaat["verzendkosten"] = m.group(1).strip()
                            break
                except Exception:
                    pass

            # ── Totaalprijs berekenen ─────────────────────────────────────
            if resultaat["prijs"]:
                verzend_val = parse_prijs(resultaat["verzendkosten"] or "")
                gratis = resultaat["verzendkosten"] and re.search(
                    r"gratis|free|0[,.]?00", resultaat["verzendkosten"] or "", re.IGNORECASE
                )
                if verzend_val:
                    resultaat["totaalprijs"] = round(resultaat["prijs"] + verzend_val, 2)
                elif gratis:
                    resultaat["totaalprijs"] = resultaat["prijs"]
                else:
                    resultaat["totaalprijs"] = resultaat["prijs"]

        except PlaywrightTimeout:
            resultaat["fout"] = "Timeout - pagina te traag"
        except Exception as e:
            resultaat["fout"] = str(e)[:200]
        finally:
            await browser.close()

    return resultaat
