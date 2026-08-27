"""
Scraper Malt.fr — scraping HTML public de la page projets
"""
import requests
import re
import time
from bs4 import BeautifulSoup
from core.config import REQUEST_TIMEOUT, REQUEST_DELAY, INTENT_KEYWORDS_FR

MALT_URLS = [
    "https://www.malt.fr/search?q=site+web",
    "https://www.malt.fr/search?q=chatbot",
    "https://www.malt.fr/search?q=automatisation",
    "https://www.malt.fr/search?q=modelisation+3D",
    "https://www.malt.fr/search?q=montage+video",
    "https://www.malt.fr/search?q=community+manager",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def fetch() -> list[dict]:
    """Scrape les projets publics listés sur Malt."""
    results = []
    seen_urls = set()

    for url in MALT_URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                print(f"  [Malt] HTTP {resp.status_code} sur {url}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Extraction des cartes de profils/projets visibles publiquement
            cards = soup.find_all(
                ["article", "div"],
                class_=re.compile(r"(profile|project|card|result|item)", re.I),
            )

            for card in cards[:20]:
                text_content = card.get_text(" ", strip=True)
                text_lower = text_content.lower()

                if not any(kw in text_lower for kw in INTENT_KEYWORDS_FR):
                    continue

                # Recherche d'un lien dans la carte
                link = card.find("a", href=True)
                href = ""
                if link:
                    href = link["href"]
                    if href.startswith("/"):
                        href = "https://www.malt.fr" + href

                if href in seen_urls or not href:
                    continue
                seen_urls.add(href)

                title = card.find(["h1", "h2", "h3", "h4"])
                title_text = title.get_text(strip=True) if title else text_content[:80]

                results.append({
                    "id": f"malt_{hash(href)}",
                    "title": title_text,
                    "body": text_content[:400],
                    "url": href,
                    "source": "Malt.fr",
                    "date": "",
                    "contact": _extract_contact(text_content),
                    "raw_text": text_lower,
                })

            time.sleep(REQUEST_DELAY)

        except requests.RequestException as e:
            print(f"  [Malt] Erreur: {e}")

    return results


def _extract_contact(text: str) -> str:
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        return email_match.group(0)
    return ""
