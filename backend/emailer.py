"""
Email module - Verstuurt prijsalerts via Resend
"""

import os
import httpx
from datetime import datetime


async def stuur_prijs_alerts(emails: list[str], wijzigingen: list[dict]):
    """Stuur een email alert naar alle opgegeven adressen."""
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "prijsmonitor@jouwdomein.com")

    if not api_key:
        print("⚠ RESEND_API_KEY niet ingesteld, email overgeslagen")
        return

    onderwerp = f"💰 PrijsMonitor: {len(wijzigingen)} prijswijziging(en) gevonden"
    html = _bouw_email_html(wijzigingen)

    async with httpx.AsyncClient() as client:
        for email in emails:
            try:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": from_email,
                        "to": [email],
                        "subject": onderwerp,
                        "html": html,
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    print(f"  ✓ Email verstuurd naar {email}")
                else:
                    print(f"  ⚠ Email mislukt voor {email}: {resp.text}")
            except Exception as e:
                print(f"  ⚠ Email fout voor {email}: {e}")


def _bouw_email_html(wijzigingen: list[dict]) -> str:
    """Bouw de HTML email op."""
    rijen = ""
    for w in wijzigingen:
        oude = f"€ {float(w['oude_prijs']):.2f}" if w.get("oude_prijs") else "?"
        nieuwe = f"€ {float(w['nieuwe_prijs']):.2f}" if w.get("nieuwe_prijs") else "?"

        # Bereken verschil
        try:
            verschil = float(w["nieuwe_prijs"]) - float(w["oude_prijs"])
            kleur = "#e53e3e" if verschil > 0 else "#38a169"
            pijl = "↑" if verschil > 0 else "↓"
            verschil_str = f'<span style="color:{kleur}">{pijl} € {abs(verschil):.2f}</span>'
        except Exception:
            verschil_str = "-"

        rijen += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; font-weight: 500;">
                <a href="{w['url']}" style="color: #2b6cb0; text-decoration: none;">{w['naam']}</a>
            </td>
            <td style="padding: 12px; text-align: right; color: #718096;">{oude}</td>
            <td style="padding: 12px; text-align: right; font-weight: 600;">{nieuwe}</td>
            <td style="padding: 12px; text-align: right;">{verschil_str}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #2d3748;">

        <div style="background: #1a202c; padding: 24px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; color: white; font-size: 20px;">
                💰 PrijsMonitor Alert
            </h1>
            <p style="margin: 8px 0 0; color: #a0aec0; font-size: 14px;">
                {datetime.now().strftime("%d/%m/%Y om %H:%M")} — {len(wijzigingen)} wijziging(en) gevonden
            </p>
        </div>

        <div style="border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 8px 8px; overflow: hidden;">
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                    <tr style="background: #f7fafc;">
                        <th style="padding: 12px; text-align: left; color: #718096; font-weight: 500;">Product</th>
                        <th style="padding: 12px; text-align: right; color: #718096; font-weight: 500;">Vorige prijs</th>
                        <th style="padding: 12px; text-align: right; color: #718096; font-weight: 500;">Nieuwe prijs</th>
                        <th style="padding: 12px; text-align: right; color: #718096; font-weight: 500;">Verschil</th>
                    </tr>
                </thead>
                <tbody>
                    {rijen}
                </tbody>
            </table>
        </div>

        <p style="margin-top: 24px; font-size: 12px; color: #a0aec0; text-align: center;">
            PrijsMonitor — automatisch verstuurd elke maandag
        </p>
    </body>
    </html>
    """
