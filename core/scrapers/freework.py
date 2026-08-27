"""
Scraper Free-work.com (freelance-info.fr) — scraping HTML public
Corrigé : extraction individuelle par <fw-carousel-item> au lieu du parent global.
"""
import requests
import re
import time
from bs4 import BeautifulSoup
from core.config import REQUEST_TIMEOUT, REQUEST_DELAY, INTENT_KEYWORDS_FR

URL = "https://www.freelance-info.fr/missions"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def fetch() -> list[dict]:
    """Scrape les missions freelance sur Free-work / Freelance-info."""
    results = []
    seen_urls = set()

    try:
        resp = requests.get(URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            print(f"  [Free-work] HTTP {resp.status_code}")
            return results

        soup = BeautifulSoup(resp.text, "html.parser")

        # Chaque mission est dans un <fw-carousel-item>
        carousel_items = soup.find_all("fw-carousel-item")

        # Fallback : si pas de fw-carousel-item, utiliser les liens directs
        if not carousel_items:
            links = soup.find_all(
                "a", href=re.compile(r"/fr/tech-it/job-mission/|/missions/")
            )
            for link in links:
                href = link["href"]
                if href.startswith("/"):
                    href = "https://www.free-work.com" + href
                if href in seen_urls or not href:
                    continue
                seen_urls.add(href)
                title = link.get_text(strip=True)[:100]
                results.append({
                    "id": f"fw_{hash(href)}",
                    "title": title or "Mission freelance",
                    "body": title,
                    "url": href,
                    "source": "Free-work",
                    "date": "",
                    "contact": "",
                    "raw_text": (title + " mission freelance projet budget devis").lower(),
                })
                if len(results) >= 20:
                    break
            return results

        for item in carousel_items:
            # Extraire le lien de la mission
            link = item.find("a", href=re.compile(r"/fr/.*?/job-mission/|/missions/"))
            if not link:
                continue

            href = link["href"]
            if href.startswith("/"):
                href = "https://www.free-work.com" + href

            if href in seen_urls:
                continue
            seen_urls.add(href)

            # Extraire le titre depuis le lien lui-même (pas le parent global)
            title = link.get_text(" ", strip=True)

            # Nettoyer les préfixes parasites (Freelance, CDI, Offre d'emploi...)
            title = re.sub(
                r"^(Freelance\s*)?(CDI\s*)?(CDD\s*)?(Offre d'?emploi\s*)?(Mission freelance\s*)?",
                "", title, flags=re.IGNORECASE
            ).strip()
            # Nettoyer les espaces multiples
            title = re.sub(r"\s+", " ", title).strip()

            # Extraire le corps : texte de l'item SAUF les autres liens de mission
            body_parts = []
            for child in item.children:
                if hasattr(child, "name") and child.name == "a":
                    child_href = child.get("href", "")
                    if re.search(r"/fr/.*?/job-mission/|/missions/", child_href):
                        continue
                text = child.get_text(strip=True) if hasattr(child, "get_text") else str(child).strip()
                if text:
                    body_parts.append(text)
            body = " ".join(body_parts)[:400]

            text_lower = f"{title} {body}".lower()

            # Extraire la date si présente
            date_match = re.search(r"(\d{2}/\d{2}/\d{4})", f"{title} {body}")
            date_str = date_match.group(1) if date_match else ""

            # Tags / compétences
            tags = [s.get_text(strip=True) for s in item.find_all("span", class_=True)]

            results.append({
                "id": f"fw_{hash(href)}",
                "title": title or "Mission freelance",
                "body": body,
                "url": href,
                "source": "Free-work",
                "date": date_str,
                "contact": _extract_contact(f"{title} {body}"),
                "raw_text": (text_lower + " mission freelance projet budget devis"),
            })

            if len(results) >= 20:
                break

        time.sleep(REQUEST_DELAY)

    except requests.RequestException as e:
        print(f"  [Free-work] Erreur: {e}")

    return results


def _extract_contact(text: str) -> str:
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        return email_match.group(0)
    return ""
