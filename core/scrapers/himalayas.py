"""
Scraper Himalayas — API publique (sans authentification)
https://himalayas.app/jobs/api
"""
import requests
import re
import time
from core.config import REQUEST_TIMEOUT, INTENT_KEYWORDS_FR

HIMALAYAS_API_URL = "https://himalayas.app/jobs/api"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# Catégories Himalayas pertinentes
CATEGORIES = [
    "web-development",
    "software-development",
    "design",
    "marketing",
    "devops-and-sysadmin",
    "content",
]


def fetch() -> list[dict]:
    """Récupère les jobs Himalayas via l'API publique."""
    results = []
    seen_ids = set()

    for category in CATEGORIES:
        try:
            params = {
                "category": category,
                "limit": 20,
            }
            resp = requests.get(
                HIMALAYAS_API_URL, params=params,
                headers=HEADERS, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()

            # L'API retourne {"jobs": [...], "totalCount": ...}
            jobs = data.get("jobs", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

            for job in jobs:
                if not isinstance(job, dict):
                    continue

                # L'identifiant unique est "guid"
                job_guid = job.get("guid", "") or job.get("id", "") or job.get("title", "")
                if str(job_guid) in seen_ids:
                    continue
                seen_ids.add(str(job_guid))

                title = job.get("title", "") or ""
                description = job.get("description", "") or ""
                excerpt = job.get("excerpt", "") or ""
                # Nettoyer le HTML
                clean_desc = re.sub(r"<[^>]+>", " ", description or excerpt)
                clean_desc = re.sub(r"\s+", " ", clean_desc).strip()

                text = f"{title} {clean_desc}".lower()

                # Filtre : domaines pertinents
                domain_keywords = [
                    "web", "website", "chatbot", "bot", "automation",
                    "3d", "video", "social media", "community",
                    "developer", "designer", "freelance", "contract",
                    "contractor", "python", "javascript", "react", "node",
                    "frontend", "backend", "full-stack", "fullstack",
                    "cms", "wordpress", "shopify", "landing page",
                    "motion design", "content creat",
                ]
                has_domain = any(kw in text for kw in domain_keywords)
                has_intent = any(kw in text for kw in INTENT_KEYWORDS_FR)

                # Vérifier aussi le type d'emploi
                employment = (job.get("employmentType", "") or "").lower()
                is_contract = any(t in employment for t in ["contract", "freelance", "part-time"])

                if not has_domain and not has_intent and not is_contract:
                    continue

                company = job.get("companyName", "") or ""
                company_slug = job.get("companySlug", "") or ""

                # Construire l'URL
                job_slug = job_guid
                if company_slug and job_slug:
                    url = f"https://himalayas.app/companies/{company_slug}/jobs/{job_slug}"
                elif job_slug:
                    url = f"https://himalayas.app/jobs/{job_slug}"
                else:
                    url = "https://himalayas.app/jobs"

                date_str = job.get("pubDate", "") or ""
                if date_str:
                    if isinstance(date_str, int):
                        # Timestamp Unix en millisecondes ou secondes
                        import datetime
                        try:
                            if date_str > 1e12:  # millisecondes
                                date_str = datetime.datetime.fromtimestamp(date_str / 1000).strftime("%Y-%m-%d")
                            else:  # secondes
                                date_str = datetime.datetime.fromtimestamp(date_str).strftime("%Y-%m-%d")
                        except Exception:
                            date_str = ""
                    else:
                        date_str = str(date_str)[:10]

                # Info salaire
                salary_info = ""
                min_sal = job.get("minSalary")
                max_sal = job.get("maxSalary")
                currency = job.get("currency", "USD")
                if min_sal and max_sal:
                    salary_info = f"{currency} {min_sal:,}–{max_sal:,}"

                body = clean_desc[:500]
                if salary_info:
                    body = f"💰 {salary_info} — {body}"

                results.append({
                    "id": f"himalayas_{job_guid}",
                    "title": f"{title} — {company}" if company else title,
                    "body": body,
                    "url": url,
                    "source": "Himalayas",
                    "date": date_str,
                    "contact": _extract_contact(clean_desc),
                    "raw_text": text,
                })

            time.sleep(0.5)

        except requests.RequestException as e:
            print(f"  [Himalayas] Erreur sur catégorie '{category}': {e}")

    return results


def _extract_contact(text: str) -> str:
    if not text:
        return ""
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        return email_match.group(0)
    return ""
