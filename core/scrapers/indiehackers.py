"""
Scraper IndieHackers — scraping HTML public du forum
"""
import requests
import re
import time
from bs4 import BeautifulSoup
from core.config import REQUEST_TIMEOUT, REQUEST_DELAY, INTENT_KEYWORDS_FR

BASE_URL = "https://www.indiehackers.com"
FORUM_URLS = [
    f"{BASE_URL}/forum",
    f"{BASE_URL}/group/new",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def fetch() -> list[dict]:
    """Scrape les posts publics du forum IndieHackers."""
    results = []
    seen_ids = set()

    for url in FORUM_URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                print(f"  [IndieHackers] HTTP {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Posts du forum
            posts = soup.find_all(["div", "article"], class_=re.compile(
                r"(post|thread|story|content|feed-item)", re.I
            ))

            for post in posts[:30]:
                text_content = post.get_text(" ", strip=True)
                text_lower = text_content.lower()

                if not any(kw in text_lower for kw in INTENT_KEYWORDS_FR):
                    continue

                link = post.find("a", href=re.compile(r"^/post|^/forum|^/group"))
                href = ""
                if link:
                    href = link["href"]
                    if href.startswith("/"):
                        href = BASE_URL + href

                if href in seen_ids or not href:
                    continue
                seen_ids.add(href)

                title_tag = post.find(["h1", "h2", "h3"])
                title = title_tag.get_text(strip=True) if title_tag else text_content[:80]

                results.append({
                    "id": f"ih_{hash(href)}",
                    "title": title,
                    "body": text_content[:400],
                    "url": href,
                    "source": "IndieHackers",
                    "date": "",
                    "contact": _extract_contact(text_content),
                    "raw_text": text_lower,
                })

            time.sleep(REQUEST_DELAY)

        except requests.RequestException as e:
            print(f"  [IndieHackers] Erreur: {e}")

    return results


def _extract_contact(text: str) -> str:
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        return email_match.group(0)
    return ""
