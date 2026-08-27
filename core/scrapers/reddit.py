"""
Scraper Reddit — utilise l'API officielle via PRAW (OAuth2 avec app script)
"""
import time
import re
from core.config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    REDDIT_SUBREDDITS, REDDIT_POST_LIMIT, INTENT_KEYWORDS_FR
)


def fetch() -> list[dict]:
    """Récupère les posts Reddit récents des subreddits configurés."""
    try:
        import praw
    except ImportError:
        print("  [Reddit] praw non installé. Lancez: pip install praw")
        return []

    if REDDIT_CLIENT_ID == "VOTRE_CLIENT_ID":
        print("  [Reddit] ⚠️  Credentials non configurés dans config.py — source ignorée.")
        return []

    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            # Mode lecture seule (pas besoin de compte utilisateur)
            read_only=True,
        )
    except Exception as e:
        print(f"  [Reddit] Erreur d'authentification: {e}")
        return []

    results = []
    seen_ids = set()

    for subreddit_name in REDDIT_SUBREDDITS:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            for post in subreddit.new(limit=REDDIT_POST_LIMIT):
                if post.id in seen_ids:
                    continue
                seen_ids.add(post.id)

                title = post.title or ""
                body = post.selftext or ""
                text = f"{title} {body}".lower()

                # Filtre : doit contenir un indicateur d'intention
                if not any(kw in text for kw in INTENT_KEYWORDS_FR):
                    # Inclure quand même si le subreddit est très ciblé
                    if subreddit_name not in ["forhire", "hiring"]:
                        continue

                from datetime import datetime, timezone
                date_str = datetime.fromtimestamp(
                    post.created_utc, tz=timezone.utc
                ).strftime("%Y-%m-%d")

                results.append({
                    "id": f"reddit_{post.id}",
                    "title": title,
                    "body": body[:500],
                    "url": f"https://reddit.com{post.permalink}",
                    "source": f"Reddit r/{subreddit_name}",
                    "date": date_str,
                    "contact": _extract_contact(body),
                    "raw_text": text,
                })

            time.sleep(0.5)

        except Exception as e:
            print(f"  [Reddit] Erreur sur r/{subreddit_name}: {e}")

    return results


def _extract_contact(text: str) -> str:
    if not text:
        return ""
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        return email_match.group(0)
    return ""
