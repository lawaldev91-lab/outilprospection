"""
Scraper RemoteOK — API publique (sans authentification)
https://remoteok.com/api
"""
import requests
import re
import time
from core.config import REQUEST_TIMEOUT, INTENT_KEYWORDS_FR

REMOTEOK_API_URL = "https://remoteok.com/api"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def fetch() -> list[dict]:
    """Récupère les jobs RemoteOK via l'API publique."""
    results = []
    seen_ids = set()

    try:
        resp = requests.get(
            REMOTEOK_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()

        # L'API retourne une liste où le premier élément est une pub, on le skip
        jobs = data[1:] if len(data) > 1 and isinstance(data[0], str) else data

        for job in jobs:
            if not isinstance(job, dict):
                continue

            job_id = job.get("id") or job.get("slug", "")
            if job_id in seen_ids:
                continue
            seen_ids.add(str(job_id))

            title = job.get("position", "") or ""
            description = job.get("description", "") or ""
            # Nettoyer le HTML
            clean_desc = re.sub(r"<[^>]+>", " ", description)
            clean_desc = re.sub(r"\s+", " ", clean_desc).strip()

            text = f"{title} {clean_desc}".lower()

            # Filtre : doit contenir un mot-clé d'intention ou être dans nos domaines
            domain_keywords = [
                "web", "website", "chatbot", "bot", "automation",
                "3d", "modeling", "video", "editing", "social media",
                "community", "marketing", "design", "freelance",
                "contract", "developer", "designer", "python", "javascript"
            ]
            has_domain = any(kw in text for kw in domain_keywords)
            has_intent = any(kw in text for kw in INTENT_KEYWORDS_FR)

            if not has_domain and not has_intent:
                continue

            company = job.get("company", "") or ""
            url = job.get("url", "") or ""
            if url and not url.startswith("http"):
                url = f"https://remoteok.com{url}"

            date_str = job.get("date", "") or ""
            if date_str:
                # RemoteOK dates are in ISO format
                date_str = date_str[:10]

            tags = job.get("tags", []) or []
            min_salary = job.get("salary_min", "")
            max_salary = job.get("salary_max", "")

            body = clean_desc[:500]
            if min_salary and max_salary:
                body = f"💰 {min_salary}–{max_salary} — {body}"

            results.append({
                "id": f"remoteok_{job_id}",
                "title": f"{title} — {company}" if company else title,
                "body": body,
                "url": url,
                "source": "RemoteOK",
                "date": date_str,
                "contact": _extract_contact(clean_desc),
                "raw_text": text,
            })

            if len(results) >= 50:
                break

    except requests.RequestException as e:
        print(f"  [RemoteOK] Erreur: {e}")

    return results


def _extract_contact(text: str) -> str:
    if not text:
        return ""
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        return email_match.group(0)
    return ""
