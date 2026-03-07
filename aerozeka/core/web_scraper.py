# -*- coding: utf-8 -*-
"""
Web Scraper: Uçuş numarası ile uçuş durumu sitelerinden kalkış/varış havalimanı kodlarını kazır.
JavaScript render ve bot koruması için Playwright kullanır; hata toleranslı (çökme yok).
"""

import re
from typing import Optional

# Playwright opsiyonel; yoksa veya hata olursa scraper devre dışı
_PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright = None

# Gerçek tarayıcı gibi User-Agent (Chrome)
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Arama için kullanılacak uçuş durumu sayfası (yapı değişirse try-except ile güvende)
_FLIGHT_STATUS_URL = "https://www.turkishairlines.com/en-int/flights/flight-status/"

# Timeout (ms)
_NAVIGATE_TIMEOUT = 20000
_WAIT_AFTER_SUBMIT = 5000

# IATA kodu: 3 büyük harf
_IATA_PATTERN = re.compile(r"\b([A-Z]{3})\b")


def scrape_flight_route(flight_number: str) -> Optional[dict]:
    """
    Uçuş numarası (örn: TK1938) ile uçuş durumu sayfasından kalkış/varış IATA kodlarını kazır.
    Mesafe hesaplanmaz; sadece origin_iata, dest_iata (ve isimler) döner.
    Hata/bot/yarı yapı değişikliğinde None döner, uygulama çökmez.

    Returns:
        {"origin_iata": "BRU", "dest_iata": "IST", "origin_name": "...", "dest_name": "..."}
        veya None
    """
    if not _PLAYWRIGHT_AVAILABLE or not sync_playwright:
        return None
    raw = (flight_number or "").strip().upper()
    if not raw:
        return None
    # Sadece rakam kısmı veya TK1234 formatı
    number_part = "".join(c for c in raw if c.isalnum())
    if len(number_part) < 3:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    user_agent=_USER_AGENT,
                    viewport={"width": 1280, "height": 720},
                    ignore_https_errors=True,
                )
                page = context.new_page()
                page.set_default_timeout(_NAVIGATE_TIMEOUT)
                page.goto(_FLIGHT_STATUS_URL, wait_until="domcontentloaded", timeout=_NAVIGATE_TIMEOUT)
                page.wait_for_timeout(2000)

                # Arama kutusu: placeholder / name / id ile dene
                search_selector = (
                    'input[placeholder*="flight" i], input[placeholder*="Flight" i], '
                    'input[name*="flight" i], input[id*="flight" i], '
                    'input[type="text"]'
                )
                search_input = page.query_selector(search_selector)
                if not search_input:
                    return None
                search_input.fill(raw)
                page.wait_for_timeout(500)

                # Arama butonu / submit
                submit_selector = (
                    'button[type="submit"], button:has-text("Search"), button:has-text("Ara"), '
                    'input[type="submit"], [data-testid*="search" i], a:has-text("Search")'
                )
                submit = page.query_selector(submit_selector)
                if submit:
                    submit.click()
                else:
                    page.keyboard.press("Enter")
                page.wait_for_timeout(_WAIT_AFTER_SUBMIT)

                # Sayfa içeriğinden IATA kodlarını topla (3 harf); sadece bilinen havalimanları
                content = page.content()
                iata_codes = list(dict.fromkeys(_IATA_PATTERN.findall(content)))
                common = {
                    "IST", "SAW", "ESB", "ADB", "AYT", "GZT", "ADA", "TZX", "VAN",
                    "JFK", "LAX", "SFO", "ORD", "MIA", "ATL", "LHR", "BRU", "CDG", "FRA",
                    "AMS", "MUC", "ZRH", "VIE", "BCN", "MAD", "FCO", "LIS", "DXB",
                    "SVO", "DME", "NRT", "HKG", "SIN", "CPT",
                }
                candidates = [c for c in iata_codes if c in common]
                if len(candidates) >= 2:
                    # İlk iki farklı kod genelde kalkış-varış sırasında geçer
                    origin_iata = candidates[0]
                    dest_iata = candidates[1]
                    if origin_iata == dest_iata and len(candidates) > 2:
                        dest_iata = candidates[2]
                    return {
                        "origin_iata": origin_iata,
                        "dest_iata": dest_iata,
                        "origin_name": origin_iata,
                        "dest_name": dest_iata,
                    }

                # Alternatif: route metninde ORIG-DEST veya "from X to Y" ara
                text = page.inner_text("body") or ""
                route_match = re.search(r"([A-Z]{3})\s*[-–—]\s*([A-Z]{3})", text)
                if route_match:
                    return {
                        "origin_iata": route_match.group(1),
                        "dest_iata": route_match.group(2),
                        "origin_name": route_match.group(1),
                        "dest_name": route_match.group(2),
                    }
                return None
            finally:
                browser.close()
    except Exception:
        return None
