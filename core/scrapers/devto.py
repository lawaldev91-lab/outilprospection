"""
Scraper dev.to — utilise l'API JSON publique (sans authentification)
"""
import requests
import re
import time
from core.config import DEVTO_MAX_ARTICLES, REQUEST_TIMEOUT, INTENT_KEYWORDS_FR

DEVTO_API_URL = "https://dev.to/api/articles"

DEVTO_TAGS = [
    "freelance", "hiring", "webdev", "chatbot", "automation",
    "3d", "javascript", "python", "beginners", "productivity",
    "discuss", "career", "community",
]


def fetch() -> list[dict]:
    """Récupère les articles dev.to récents pertinents."""
    results = []
    seen_ids = set()

    for tag in DEVTO_TAGS:
        try:
            params = {
                "tag": tag,
                "per_page": min(DEVTO_MAX_ARTICLES, 30),
                "top": 7,
            }
            resp = requests.get(
                DEVTO_API_URL, params=params, timeout=REQUEST_TIMEOUT,
                headers={"Accept": "application/vnd.forem.api-v1+json"}
            )
            resp.raise_for_status()
            articles = resp.json()

            for art in articles:
                art_id = art.get("id")
                if art_id in seen_ids:
                    continue
                seen_ids.add(art_id)

                title = art.get("title", "") or ""
                description = art.get("description", "") or ""
                body_snippet = art.get("body_markdown", "")[:300] if art.get("body_markdown") else ""
                text = f"{title} {description} {body_snippet}".lower()

                if not any(kw in text for kw in INTENT_KEYWORDS_FR):
                    continue

                date_str = (art.get("published_at", "") or "")[:10]
                url = art.get("url", "")

                results.append({
                    "id": f"devto_{art_id}",
                    "title": title,
                    "body": description,
                    "url": url,
                    "source": "dev.to",
                    "date": date_str,
                    "contact": _extract_contact(description),
                    "raw_text": text,
                })

            time.sleep(0.5)

        except requests.RequestException as e:
            print(f"  [dev.to] Erreur sur tag '{tag}': {e}")

    return results


def _extract_contact(text: str) -> str:
    if not text:
        return ""
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        return email_match.group(0)
    return ""
