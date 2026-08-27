"""
Scraper Remotive — API publique (sans authentification)
https://remotive.com/api/remote-jobs
"""
import requests
import re
import time
from core.config import REQUEST_TIMEOUT, INTENT_KEYWORDS_FR

REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"

# Catégories Remotive qui correspondent à nos catégories
CATEGORIES_TO_SEARCH = [
    "software-dev",      # Développement web
    "design",            # Design / UI / 3D
    "marketing",         # Marketing / Réseaux sociaux
    "devops",            # Automatisation / Infrastructure
    "customer-support",  # Support
    "all",               # Toutes
]

SEARCH_QUERIES = [
    "website development",
    "chatbot",
    "automation",
    "3d modeling",
    "video editing",
    "social media",
    "freelance",
    "web developer",
    "front-end",
]


def fetch() -> list[dict]:
    """Récupère les jobs Remotive via l'API publique."""
    results = []
    seen_ids = set()

    # Requête par catégorie
    for category in CATEGORIES_TO_SEARCH:
        try:
            params = {
                "limit": 20,
                "category": category,
            }
            resp = requests.get(
                REMOTIVE_API_URL, params=params, timeout=REQUEST_TIMEOUT,
                headers={"Accept": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()

            for job in data.get("jobs", []):
                job_id = job.get("id")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                title = job.get("title", "") or ""
                description = job.get("description", "") or ""
                # Nettoyer le HTML de la description
                clean_desc = re.sub(r"<[^>]+>", " ", description)
                clean_desc = re.sub(r"\s+", " ", clean_desc).strip()
                
                text = f"{title} {clean_desc}".lower()

                # Filtre : doit contenir un mot-clé d'intention
                if not any(kw in text for kw in INTENT_KEYWORDS_FR):
                    # Inclure quand même si mots-clés anglais de demande
                    english_intent = any(
                        kw in text for kw in [
                            "looking for", "hiring", "need", "seeking",
                            "freelance", "contract", "remote", "build",
                            "developer", "designer"
                        ]
                    )
                    if not english_intent:
                        continue

                company = job.get("company_name", "") or ""
                url = job.get("url", "") or ""
                publication = job.get("publication_date", "") or ""
                date_str = publication[:10] if publication else ""
                tags = job.get("tags", []) or []

                results.append({
                    "id": f"remotive_{job_id}",
                    "title": f"{title} — {company}" if company else title,
                    "body": clean_desc[:500],
                    "url": url,
                    "source": "Remotive",
                    "date": date_str,
                    "contact": _extract_contact(clean_desc),
                    "raw_text": text,
                })

            time.sleep(0.5)

        except requests.RequestException as e:
            print(f"  [Remotive] Erreur sur catégorie '{category}': {e}")

    # Requête par mot-clé de recherche
    for query in SEARCH_QUERIES:
        try:
            params = {
                "search": query,
                "limit": 10,
            }
            resp = requests.get(
                REMOTIVE_API_URL, params=params, timeout=REQUEST_TIMEOUT,
                headers={"Accept": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()

            for job in data.get("jobs", []):
                job_id = job.get("id")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                title = job.get("title", "") or ""
                description = job.get("description", "") or ""
                clean_desc = re.sub(r"<[^>]+>", " ", description)
                clean_desc = re.sub(r"\s+", " ", clean_desc).strip()
                text = f"{title} {clean_desc}".lower()

                company = job.get("company_name", "") or ""
                url = job.get("url", "") or ""
                publication = job.get("publication_date", "") or ""
                date_str = publication[:10] if publication else ""

                results.append({
                    "id": f"remotive_{job_id}",
                    "title": f"{title} — {company}" if company else title,
                    "body": clean_desc[:500],
                    "url": url,
                    "source": "Remotive",
                    "date": date_str,
                    "contact": _extract_contact(clean_desc),
                    "raw_text": text,
                })

            time.sleep(0.5)

        except requests.RequestException as e:
            print(f"  [Remotive] Erreur sur recherche '{query}': {e}")

    return results


def _extract_contact(text: str) -> str:
    if not text:
        return ""
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        return email_match.group(0)
    return ""
