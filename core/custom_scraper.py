"""
Custom URL Scraper — Scraping intelligent sur n'importe quel lien.
Extrait automatiquement les opportunités de prospection.

Stratégies d'extraction :
1. Détection automatique du type de site (job board, blog, forum, etc.)
2. Multi-extracteurs selon la structure HTML
3. Filtrage strict via le classificateur existant
4. Gestion robuste des erreurs avec retries

Limitations connues :
- Les sites 100% JavaScript (SPA React/Angular) ne peuvent pas être scrapés
  sans un navigateur headless (Selenium/Playwright)
- Les sites avec Cloudflare strict ou CAPTCHA seront bloqués
- Respect du robots.txt et throttling
"""
import re
import time
import logging
import socket
from urllib.parse import urlparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── CONFIGURATION ────────────────────────────────────────────────────────────
REQUEST_TIMEOUT = 15       # Timeout HTTP en secondes
MAX_RETRIES = 2            # Nombre de tentatives en cas d'erreur
RETRY_DELAY = 2            # Délai entre retries en secondes
MAX_BODY_LENGTH = 2000     # Longueur max du corps extrait
MAX_RESULTS_PER_PAGE = 20  # Max d'opportunités extraites par page

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Patterns pour détecter si un lien est une opportunité potentielle
OPPORTUNITY_PATTERNS = re.compile(
    r"(freelance|mission|offre|emploi|job|recrute|cherche|hiring|"
    r"prestataire|projet|développeur|designer|monteur|graphiste|"
    r"community|chatbot|automatisation|site web|vidéo|3d)",
    re.IGNORECASE
)

# Extensions de fichiers à ignorer
SKIP_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.rar', '.tar', '.gz', '.mp4', '.mp3', '.avi',
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'
}

# Sélecteurs CSS courants pour les cartes d'articles/offres
CARD_SELECTORS = [
    # Job boards génériques
    'article',
    'div.job-card', 'div.job-item', 'div.job-listing', 'div.job',
    'div.career-card', 'div.career-item',
    # Annonces génériques
    'div.post', 'div.post-item', 'div.post-card',
    'div.listing', 'div.listing-item', 'div.listing-card',
    'div.offer', 'div.offer-item', 'div.offer-card',
    # Blog / forums
    'div.entry', 'div.blog-post', 'div.forum-post',
    # Liens dans des listes
    'li.job', 'li.post', 'li.listing',
]

# Sélecteurs pour trouver des liens internes
LINK_SELECTORS = [
    'a[href]',
]

# Mots-clés qui indiquent qu'un lien est pertinent (page d'offre)
LINK_OPPORTUNITY_HINTS = [
    'job', 'career', 'offre', 'emploi', 'mission', 'freelance',
    'poste', 'recrutement', 'hiring', 'position', 'role'
]


# ── EXCEPTIONS PERSONNALISÉES ───────────────────────────────────────────────
class CustomScraperError(Exception):
    """Erreur de base du custom scraper."""
    pass

class InvalidURLError(CustomScraperError):
    """URL invalide ou non supportée."""
    pass

class FetchError(CustomScraperError):
    """Erreur lors du fetching de la page."""
    pass

class ParsingError(CustomScraperError):
    """Erreur lors du parsing du contenu."""
    pass


# ── VALIDATION ─────────────────────────────────────────────────────────────
def validate_url(url: str) -> str:
    """
    Valide et normalise une URL.
    
    Returns:
        URL normalisée
        
    Raises:
        InvalidURLError si l'URL est invalide
    """
    if not url or not url.strip():
        raise InvalidURLError("URL vide")
    
    url = url.strip()
    
    # Ajout du protocole si manquant
    if not re.match(r'^https?://', url):
        url = 'https://' + url
    
    # Validation de la structure
    try:
        parsed = urlparse(url)
    except Exception:
        raise InvalidURLError(f"URL mal formée: {url}")
    
    if not parsed.netloc:
        raise InvalidURLError(f"Domaine manquant dans l'URL: {url}")
    
    if not parsed.scheme in ('http', 'https'):
        raise InvalidURLError(f"Protocole non supporté: {parsed.scheme}")
    
    # Vérifier l'extension du fichier
    path = parsed.path.lower()
    for ext in SKIP_EXTENSIONS:
        if path.endswith(ext):
            raise InvalidURLError(f"Type de fichier non supporté: {ext}")
    
    return url


def is_domain_accessible(domain: str, timeout: int = 5) -> bool:
    """Vérifie rapidement si un domaine est accessible."""
    try:
        socket.getaddrinfo(domain, 443)
        return True
    except socket.gaierror:
        return False


# ── FETCHING ROBUSTE ────────────────────────────────────────────────────────
def fetch_page(url: str) -> Tuple[str, str]:
    """
    Récupère le contenu HTML d'une page avec retries.
    
    Returns:
        Tuple (html_content, final_url)
        
    Raises:
        FetchError si impossible de récupérer la page
    """
    last_error = None
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            
            # Vérifier le statut HTTP
            if response.status_code == 403:
                raise FetchError(
                    "Accès refusé (403). Le site bloque le scraping."
                )
            elif response.status_code == 404:
                raise FetchError("Page non trouvée (404).")
            elif response.status_code >= 400:
                raise FetchError(
                    f"Erreur HTTP {response.status_code}"
                )
            
            # Vérifier le content-type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type and 'html' not in content_type:
                # Certains sites ne renvoient pas le bon content-type
                # On continue quand même si le contenu ressemble à du HTML
                if not response.text.strip().startswith('<'):
                    raise FetchError(
                        f"Contenu non-HTML reçu (content-type: {content_type})"
                    )
            
            return response.text, response.url
            
        except requests.exceptions.Timeout:
            last_error = FetchError(f"Timeout après {REQUEST_TIMEOUT}s")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
        except requests.exceptions.ConnectionError as e:
            last_error = FetchError(f"Erreur de connexion: {str(e)[:100]}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
        except requests.exceptions.RequestException as e:
            last_error = FetchError(f"Erreur réseau: {str(e)[:100]}")
            break
    
    raise last_error or FetchError("Impossible de récupérer la page")


# ── DÉTECTION DU TYPE DE SITE ───────────────────────────────────────────────
def detect_page_type(soup: BeautifulSoup, url: str) -> str:
    """
    Détecte le type de page pour adapter l'extraction.
    
    Returns:
        'single_opportunity', 'list_page', 'article', 'unknown'
    """
    url_lower = url.lower()
    
    # Page d'offre unique (URL contient des indices)
    if any(hint in url_lower for hint in ['offre-', 'job-', 'mission-', '/jobs/', '/career/']):
        title_tag = soup.find('title')
        if title_tag and any(hint in title_tag.get_text().lower() for hint in ['offre', 'emploi', 'job']):
            return 'single_opportunity'
    
    # Page de liste (job board)
    for selector in CARD_SELECTORS:
        if soup.select(selector):
            return 'list_page'
    
    # Blog / article
    if soup.find('article') or soup.find(class_=re.compile(r'post|article|entry', re.I)):
        return 'article'
    
    return 'unknown'


# ── EXTRACTEURS ─────────────────────────────────────────────────────────────
def extract_single_opportunity(soup: BeautifulSoup, url: str) -> Optional[Dict]:
    """Extrait une opportunité d'une page unique."""
    # Titre
    title = None
    title_tag = soup.find('h1')
    if title_tag:
        title = title_tag.get_text(strip=True)
    
    if not title:
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
    
    if not title:
        return None
    
    # Description
    body = ""
    for meta_name in ['description', 'og:description']:
        meta = soup.find('meta', attrs={'name': meta_name}) or soup.find('meta', attrs={'property': f'og:{meta_name}'})
        if meta and meta.get('content'):
            body = meta['content']
            break
    
    if not body:
        # Chercher le premier paragraphe significatif
        paragraphs = soup.find_all('p')
        for p in paragraphs[:5]:
            text = p.get_text(strip=True)
            if len(text) > 50:
                body = text
                break
    
    # Contact
    contact = extract_contact_info(soup)
    
    # Date
    date = extract_date(soup)
    
    # Texte complet pour analyse
    raw_text = f"{title} {body}".lower()
    
    # Vérifier si c'est vraiment une opportunité
    if not OPPORTUNITY_PATTERNS.search(raw_text):
        return None
    
    return {
        "id": f"custom_{hash(url)}",
        "title": title[:200],
        "body": body[:500],
        "url": url,
        "source": "Custom URL",
        "date": date,
        "contact": contact,
        "raw_text": raw_text,
    }


def extract_from_list_page(soup: BeautifulSoup, base_url: str) -> List[Dict]:
    """Extrait les opportunités d'une page de liste."""
    results = []
    parsed_base = urlparse(base_url)
    seen_urls = set()
    
    # Trouver les cartes d'offres
    cards = []
    for selector in CARD_SELECTORS:
        found = soup.select(selector)
        if found:
            cards = found
            break
    
    # Si pas de cartes, chercher les liens dans des listes
    if not cards:
        cards = soup.find_all(['li', 'div'], class_=re.compile(
            r'(job|offer|listing|post|entry|card|item)', re.I
        ))
    
    for card in cards[:MAX_RESULTS_PER_PAGE]:
        # Trouver le lien principal
        link = card.find('a', href=True)
        if not link:
            continue
        
        href = link['href']
        # Normaliser l'URL
        if href.startswith('/'):
            href = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
        elif not href.startswith('http'):
            continue
        
        if href in seen_urls:
            continue
        seen_urls.add(href)
        
        # Extraire les infos
        title = link.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        
        # Description dans la carte
        body = ""
        desc_tag = card.find(['p', 'span', 'div'], class_=re.compile(
            r'(desc|summary|excerpt|detail|meta)', re.I
        ))
        if desc_tag:
            body = desc_tag.get_text(strip=True)
        
        if not body:
            # Prendre le texte de la carte sauf le lien
            texts = []
            for child in card.children:
                if hasattr(child, 'get_text') and child != link:
                    text = child.get_text(strip=True)
                    if text:
                        texts.append(text)
            body = ' '.join(texts)[:200]
        
        raw_text = f"{title} {body}".lower()
        
        # Filtrer les liens non pertinents
        if not OPPORTUNITY_PATTERNS.search(raw_text):
            # Accepter si le lien contient des indices d'opportunité
            if not any(hint in href.lower() for hint in LINK_OPPORTUNITY_HINTS):
                continue
        
        results.append({
            "id": f"custom_{hash(href)}",
            "title": title[:200],
            "body": body[:500],
            "url": href,
            "source": "Custom URL",
            "date": extract_date_from_text(raw_text),
            "contact": extract_contact_from_text(raw_text),
            "raw_text": raw_text,
        })
    
    return results


def extract_from_links(soup: BeautifulSoup, base_url: str) -> List[Dict]:
    """Fallback : extrait les opportunités depuis tous les liens de la page."""
    results = []
    parsed_base = urlparse(base_url)
    seen_urls = set()
    
    links = soup.find_all('a', href=True)
    
    for link in links[:50]:  # Limiter pour la performance
        href = link['href']
        
        # Normaliser
        if href.startswith('/'):
            href = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
        elif not href.startswith('http'):
            continue
        
        # Ignorer les liens externes évidents
        if urlparse(href).netloc != parsed_base.netloc:
            continue
        
        # Éviter les duplicatas
        if href in seen_urls:
            continue
        
        # Filtrer les extensions
        path = urlparse(href).path.lower()
        if any(path.endswith(ext) for ext in SKIP_EXTENSIONS):
            continue
        
        # Filtrer les ancres et pages système
        if href.endswith('#') or any(skip in href.lower() for skip in [
            'login', 'signin', 'register', 'signup', 'cart', 'checkout',
            'account', 'profile', 'settings'
        ]):
            continue
        
        seen_urls.add(href)
        
        title = link.get_text(strip=True)
        if not title or len(title) < 3:
            continue
        
        raw_text = title.lower()
        
        # Vérifier si ça ressemble à une opportunité
        if not OPPORTUNITY_PATTERNS.search(raw_text):
            if not any(hint in href.lower() for hint in LINK_OPPORTUNITY_HINTS):
                continue
        
        results.append({
            "id": f"custom_{hash(href)}",
            "title": title[:200],
            "body": "",
            "url": href,
            "source": "Custom URL",
            "date": "",
            "contact": "",
            "raw_text": raw_text,
        })
        
        if len(results) >= MAX_RESULTS_PER_PAGE:
            break
    
    return results


# ── HELPERS ────────────────────────────────────────────────────────────────
def extract_contact_info(soup: BeautifulSoup) -> str:
    """Extrait les informations de contact de la page."""
    # Email
    email_match = None
    for text in [soup.get_text(), str(soup)]:
        match = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
        if match:
            email_match = match.group(0)
            break
    
    if email_match:
        return email_match
    
    # Téléphone
    phone_match = re.search(
        r'(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{2,4}',
        soup.get_text()
    )
    if phone_match:
        return f"Tel: {phone_match.group(0)}"
    
    return ""


def extract_contact_from_text(text: str) -> str:
    """Extrait un contact depuis du texte brut."""
    match = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else ""


def extract_date(soup: BeautifulSoup) -> str:
    """Extrait la date de publication de la page."""
    # Balise meta
    for attr in ['article:published_time', 'datePublished', 'date']:
        meta = soup.find('meta', attrs={'property': attr}) or soup.find('meta', attrs={'name': attr})
        if meta and meta.get('content'):
            return meta['content'][:10]
    
    # Time tag
    time_tag = soup.find('time', attrs={'datetime': True})
    if time_tag:
        return time_tag['datetime'][:10]
    
    # Chercher dans le texte
    return extract_date_from_text(soup.get_text())


def extract_date_from_text(text: str) -> str:
    """Extrait une date depuis du texte."""
    # Format ISO
    match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    if match:
        return match.group(1)
    
    # Format FR
    match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
    if match:
        return match.group(1)
    
    # "il y a X jours/mois"
    match = re.search(r'il y a\s+\d+\s+(jour|mois|an|heure)s?', text)
    if match:
        return match.group(0)[:20]
    
    return ""


# ── FONCTION PRINCIPALE ────────────────────────────────────────────────────
def scrape_url(url: str, strict: bool = True) -> Dict:
    """
    Scrape une URL personnalisée et extrait les opportunités.
    
    Args:
        url: URL à scraper
        strict: Si True, applique le filtrage strict du classificateur
        
    Returns:
        Dictionnaire avec:
        - success: bool
        - opportunities: list[dict]
        - page_type: str
        - page_title: str
        - total_links: int
        - error: str (si échec)
    """
    result = {
        'success': False,
        'opportunities': [],
        'page_type': 'unknown',
        'page_title': '',
        'total_links': 0,
        'error': None,
    }
    
    try:
        # 1. Validation
        url = validate_url(url)
        logger.info(f"Scraping URL: {url}")
        
        # 2. Fetching
        html, final_url = fetch_page(url)
        
        # 3. Parsing
        soup = BeautifulSoup(html, 'html.parser')
        
        # Titre de la page
        title_tag = soup.find('title')
        result['page_title'] = title_tag.get_text(strip=True)[:100] if title_tag else ''
        
        # Nombre de liens
        result['total_links'] = len(soup.find_all('a', href=True))
        
        # 4. Détection du type
        page_type = detect_page_type(soup, final_url)
        result['page_type'] = page_type
        
        # 5. Extraction selon le type
        if page_type == 'single_opportunity':
            opp = extract_single_opportunity(soup, final_url)
            if opp:
                result['opportunities'].append(opp)
        
        elif page_type == 'list_page':
            result['opportunities'] = extract_from_list_page(soup, final_url)
        
        elif page_type == 'article':
            opp = extract_single_opportunity(soup, final_url)
            if opp:
                result['opportunities'].append(opp)
            # Aussi extraire les liens internes pertinents
            if len(result['opportunities']) == 0:
                result['opportunities'] = extract_from_links(soup, final_url)
        
        else:
            # Inconnu : essayer les deux stratégies
            result['opportunities'] = extract_from_list_page(soup, final_url)
            if len(result['opportunities']) == 0:
                result['opportunities'] = extract_from_links(soup, final_url)
            if len(result['opportunities']) == 0:
                opp = extract_single_opportunity(soup, final_url)
                if opp:
                    result['opportunities'].append(opp)
        
        # 6. Filtrage strict si demandé
        if strict and result['opportunities']:
            try:
                from core.classifier import filter_relevant
                result['opportunities'] = filter_relevant(result['opportunities'])
            except Exception as e:
                logger.warning(f"Filtrage désactivé: {e}")
        
        result['success'] = True
        logger.info(
            f"Scraping terminé: {len(result['opportunities'])} opportunités "
            f"trouvées sur {result['total_links']} liens"
        )
        
    except InvalidURLError as e:
        result['error'] = str(e)
        logger.warning(f"URL invalide: {e}")
    except FetchError as e:
        result['error'] = str(e)
        logger.error(f"Erreur de fetching: {e}")
    except ParsingError as e:
        result['error'] = f"Erreur de parsing: {e}"
        logger.error(f"Erreur de parsing: {e}")
    except Exception as e:
        result['error'] = f"Erreur inattendue: {str(e)[:200]}"
        logger.exception(f"Erreur inattendue lors du scraping de {url}")
    
    return result


def scrape_multiple_urls(urls: List[str], strict: bool = True) -> Dict:
    """
    Scrape plusieurs URLs et combine les résultats.
    
    Args:
        urls: Liste d'URLs à scraper
        strict: Filtrage strict
        
    Returns:
        Dictionnaire avec résultats combinés
    """
    all_opportunities = []
    errors = []
    pages_scanned = 0
    
    for url in urls:
        try:
            result = scrape_url(url, strict=strict)
            if result['success']:
                all_opportunities.extend(result['opportunities'])
                pages_scanned += 1
            else:
                errors.append({
                    'url': url,
                    'error': result['error']
                })
        except Exception as e:
            errors.append({
                'url': url,
                'error': str(e)
            })
    
    # Déduplication
    seen_ids = set()
    unique_opportunities = []
    for opp in all_opportunities:
        if opp['id'] not in seen_ids:
            seen_ids.add(opp['id'])
            unique_opportunities.append(opp)
    
    return {
        'success': len(unique_opportunities) > 0,
        'opportunities': unique_opportunities,
        'pages_scanned': pages_scanned,
        'total_opportunities': len(unique_opportunities),
        'errors': errors,
    }
