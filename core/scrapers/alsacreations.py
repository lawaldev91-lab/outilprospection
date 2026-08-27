"""
Scraper Alsacréations — scraping HTML public de la section emploi/projets
Corrigé : la structure HTML utilise désormais <li class="offre"> au lieu de <tr>.
"""
import requests
import re
import time
from bs4 import BeautifulSoup
from core.config import REQUEST_TIMEOUT, REQUEST_DELAY, INTENT_KEYWORDS_FR

URL = "https://emploi.alsacreations.com/offres.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}

def fetch() -> list[dict]:
    """Scrape les offres/projets publics sur Alsacréations."""
    results = []
    seen_urls = set()

    try:
        resp = requests.get(URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            print(f"  [Alsacréations] HTTP {resp.status_code}")
            return results

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extraction des offres — <li class="offre"> (nouvelle structure HTML)
        items = soup.find_all("li", class_=re.compile(r"offre"))

        for item in items[:30]:
            text_content = item.get_text(" ", strip=True)
            text_lower = text_content.lower()

            link = item.find("a", href=True)
            href = ""
            if link:
                href = link["href"]
                if href.startswith("/"):
                    href = "https://emploi.alsacreations.com" + href
                elif not href.startswith("http"):
                    href = "https://emploi.alsacreations.com/" + href

            if href in seen_urls or not href:
                continue
            seen_urls.add(href)

            # On vérifie l'intention ou si le mot freelance est mentionné
            is_freelance = "freelance" in text_lower or "indépendant" in text_lower
            if not is_freelance and not any(kw in text_lower for kw in INTENT_KEYWORDS_FR):
                continue

            # Extraction du titre depuis le lien principal
            title_tag = item.find("a")
            title = title_tag.get_text(strip=True) if title_tag else text_content[:80]

            # Extraction de la date / durée si présente
            details_span = item.find("span", class_=re.compile(r"details"))
            if details_span:
                details_text = details_span.get_text(" ", strip=True)
                # Chercher une info de date relative
                date_match = re.search(r"il y a\s+(.+)", details_text)
                date_info = date_match.group(0) if date_match else details_text[:30]
            else:
                date_info = ""

            results.append({
                "id": f"alsa_{hash(href)}",
                "title": title,
                "body": text_content[:400],
                "url": href,
                "source": "Alsacréations",
                "date": date_info[:20] if date_info else "",
                "contact": _extract_contact(text_content),
                "raw_text": text_lower + " besoin d'un développeur freelance projet devis",
            })

        time.sleep(REQUEST_DELAY)

    except requests.RequestException as e:
        print(f"  [Alsacréations] Erreur: {e}")

    return results


def _extract_contact(text: str) -> str:
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        return email_match.group(0)
    return ""
