"""
Scraper module - Playwright met cart/checkout flow voor verzendkosten
"""

import re
import json
import asyncio
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['nl-BE', 'nl', 'fr'] });
window.chrome = { runtime: {} };
"""


def parse_prijs(tekst: str) -> Optional[float]:
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
            print(f"  → Ophalen: {url}")
            resp = await page.goto(url, wait_until="networkidle", timeout=40000)

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
                            resultaat["naam"] = naam[:100]
                            break
                except Exception:
                    continue

            # ── Prijs ophalen van productpagina ───────────────────────────
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

            # Fallback: JSON-LD
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

            print(f"  → Prijs gevonden: {resultaat['prijs']}")

            # ── Verzendkosten via winkelwagen ─────────────────────────────
            verzend = await haal_verzendkosten(page, url)
            resultaat["verzendkosten"] = verzend
            print(f"  → Verzendkosten: {verzend}")

            # ── Totaalprijs ───────────────────────────────────────────────
            if resultaat["prijs"]:
                verzend_val = parse_prijs(verzend or "")
                gratis = verzend and re.search(r"gratis|free|0[,.]?00", verzend, re.IGNORECASE)
                if verzend_val and verzend_val > 0:
                    resultaat["totaalprijs"] = round(resultaat["prijs"] + verzend_val, 2)
                elif gratis:
                    resultaat["totaalprijs"] = resultaat["prijs"]
                else:
                    resultaat["totaalprijs"] = resultaat["prijs"]

        except PlaywrightTimeout:
            resultaat["fout"] = "Timeout"
        except Exception as e:
            resultaat["fout"] = str(e)[:200]
        finally:
            await browser.close()

    return resultaat


async def haal_verzendkosten(page, product_url: str) -> Optional[str]:
    """Voeg product toe aan winkelwagen en lees verzendkosten uit checkout."""
    try:
        # Stap 1: Voeg toe aan winkelwagen
        add_selectors = [
            "button:has-text('In winkelwagen')",
            "button:has-text('Toevoegen aan winkelwagen')",
            "button:has-text('Add to cart')",
            "button:has-text('Toevoegen')",
            "[id*='add-to-cart']",
            "button[class*='add-to-cart']",
            "button[class*='cart']",
            ".btn-cart",
        ]

        toegevoegd = False
        for sel in add_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    toegevoegd = True
                    print(f"  → Toegevoegd aan winkelwagen via: {sel}")
                    break
            except Exception:
                continue

        if not toegevoegd:
            print("  → Kon niet toevoegen aan winkelwagen")
            return None

        # Stap 2: Ga naar checkout/winkelwagen pagina
        basis_url = product_url.split("/p/")[0] if "/p/" in product_url else "/".join(product_url.split("/")[:3])

        checkout_urls = [
            f"{basis_url}/checkout",
            f"{basis_url}/winkelwagen",
            f"{basis_url}/cart",
            f"{basis_url}/checkout/cart",
        ]

        for checkout_url in checkout_urls:
            try:
                await page.goto(checkout_url, wait_until="networkidle", timeout=20000)
                await page.wait_for_timeout(2000)

                # Stap 3: Zoek verzendkosten op checkout pagina
                verzend_selectors = [
                    "[class*='shipping'] [class*='price']",
                    "[class*='shipping-cost']",
                    "[class*='delivery-cost']",
                    "[class*='verzend'] [class*='prijs']",
                    "td:has-text('Verzending') + td",
                    "td:has-text('Shipping') + td",
                    "td:has-text('Levering') + td",
                    "[class*='totals'] [class*='shipping']",
                ]

                for sel in verzend_selectors:
                    try:
                        el = page.locator(sel).first
                        if await el.count() > 0:
                            tekst = (await el.text_content() or "").strip()
                            if tekst and len(tekst) < 50:
                                return tekst
                    except Exception:
                        continue

                # Zoek in paginatekst
                body = await page.locator("body").text_content()
                patterns = [
                    r"(gratis verzend\w*)",
                    r"(free shipping)",
                    r"verzend(?:kosten)?[:\s]+([\d€,.\s]+)",
                    r"levering[:\s]+([\d€,.\s]+)",
                    r"shipping[:\s]+([\d€,.\s]+)",
                ]
                for pattern in patterns:
                    m = re.search(pattern, body or "", re.IGNORECASE)
                    if m:
                        return m.group(1).strip() if m.lastindex else m.group(0).strip()

                break
            except Exception:
                continue

    except Exception as e:
        print(f"  → Fout bij verzendkosten: {e}")

    return None
