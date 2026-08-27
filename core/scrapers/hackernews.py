"""
Scraper Hacker News — utilise l'API publique Algolia (sans authentification)
"""
import requests
import time
from datetime import datetime, timedelta, timezone
from core.config import HN_MAX_RESULTS, HN_DAYS_BACK, REQUEST_TIMEOUT, INTENT_KEYWORDS_FR


HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"


def _build_queries():
    """Requêtes ciblant les demandes de prestataire sur HN (anglais)."""
    return [
        "who is hiring",
        "looking for freelancer",
        "hiring developer",
        "need a developer website",
        "chatbot development hire",
        "automation freelancer needed",
        "3d modeling freelance",
        "video editing hire",
        "social media manager hire",
        "seeking freelancer project",
        "web developer needed",
        "build chatbot hire",
    ]


def fetch() -> list[dict]:
    """Récupère les posts HN pertinents via l'API Algolia."""
    results = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=HN_DAYS_BACK)
    cutoff_ts = int(cutoff.timestamp())

    for query in _build_queries():
        try:
            params = {
                "query": query,
                "tags": "(story,ask_hn,show_hn)",
                "numericFilters": f"created_at_i>{cutoff_ts}",
                "hitsPerPage": min(HN_MAX_RESULTS, 50),
            }
            resp = requests.get(
                HN_ALGOLIA_URL, params=params, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()

            for hit in data.get("hits", []):
                obj_id = hit.get("objectID")
                title = hit.get("title", "") or ""
                body = hit.get("story_text", "") or ""
                text = f"{title} {body}".lower()

                # Filtre rapide : doit contenir un mot-clé d'intention
                if not any(kw in text for kw in INTENT_KEYWORDS_FR):
                    continue

                created = hit.get("created_at", "")
                results.append({
                    "id": f"hn_{obj_id}",
                    "title": title,
                    "body": body[:500],
                    "url": f"https://news.ycombinator.com/item?id={obj_id}",
                    "source": "Hacker News",
                    "date": created[:10] if created else "",
                    "contact": _extract_contact(body),
                    "raw_text": text,
                })

            time.sleep(0.5)  # Respect du rate limit Algolia

        except requests.RequestException as e:
            print(f"  [HN] Erreur sur '{query}': {e}")

    # Dédoublonnage par ID
    seen = set()
    unique = []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)

    return unique


def _extract_contact(text: str) -> str:
    """Extrait un email ou lien de contact si présent dans le texte."""
    import re
    if not text:
        return ""
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        return email_match.group(0)
    return ""
