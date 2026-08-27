"""
Classificateur STRICT — résultats 100% français et pertinents uniquement.

Logique renforcée :
1. Élimine tout contenu principalement en anglais
2. Élimine les offres d'emploi salarié (CDI classiques)
3. Élimine les tutoriels, articles, annonces non liées à la prospection
4. Ne garde QUE les vraies demandes de prestataires / missions freelance
"""
import re
import unicodedata
from core.config import CATEGORIES, INTENT_KEYWORDS_FR, RELEVANCE_THRESHOLD


# ── PATTERNS D'EXCLUSION IMMÉDIATE ────────────────────────────────────────
# Si le titre contient un de ces patterns → score = 0
EXCLUSION_PATTERNS = [
    # Contenu anglais générique (on veut du FR uniquement)
    r"^how to\b", r"^guide\b", r"^tutorial\b", r"^introducing\b",
    r"^announcing\b", r"^released?\b", r"^show hn:", r"^ask hn: how",
    r"^i built\b", r"^i made\b", r"^i created\b",
    r"^(top|best) \d+\b", r"^the (complete|ultimate|best|definitive)\b",
    # Offres d'emploi salarié classique
    r"\b(cd[iI]|cdd)\b.*\b(senior|junior|confirmé|débutant)\b",
    r"\b(salary|compensation|equity|benefits|health insurance|401k)\b",
    r"\b(years? of experience|required|preferred)\b",
    # Publications personnelles / annonces produit
    r"^(lessons|things) (learned|i learned)\b",
    r"^building (better|a|an|your|my)\b",
    r"^understanding\b", r"^exploring\b", r"^getting started\b",
    r"^why (you|i|we)\b", r"^what (is|are|i|you)\b",
]

# ── PATTERNS DE DÉTECTION FRANÇAISE ──────────────────────────────────────
# Pour vérifier qu'un texte est bien en français
FRENCH_MARKERS = [
    "le", "la", "les", "un", "une", "des", "de", "du",
    "est", "sont", "a", "ont", "nous", "vous", "je", "il",
    "pour", "dans", "sur", "avec", "par", "en", "au", "aux",
    "qui", "que", "quoi", "dont", "où", "ce", "cette", "ces",
    "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
    "cherche", "recherche", "besoin", "projet", "mission",
    "développeur", "entreprise", "société", "freelance",
]

# ── SIGNAUX FORTS : demandes de prestataires FR ──────────────────────────
STRONG_SIGNALS_FR = [
    r"je cherche (un|une|des|quelqu)",
    r"nous cherchons (un|une|des)",
    r"cherche (un|une) (développeur|dev|freelance|prestataire|graphiste|monteur|community)",
    r"besoin d.un (développeur|dev|freelance|prestataire|site|chatbot|bot|script|automatisation|monteur|graphiste)",
    r"besoin d.aide (pour|sur|avec)",
    r"recherche (un|une) (développeur|dev|freelance|prestataire|graphiste|monteur|community)",
    r"qui (peut|pourrait|saurait) (créer|développer|réaliser|faire|coder|monter|gérer)",
    r"faire (réaliser|créer|développer|coder|monter|gérer) (un|une|mon|ma|notre)",
    r"projet (à réaliser|en cours|urgent|rémunéré)",
    r"budget (prévu|disponible|alloué|de|:)\s*[\d€]",
    r"devis (souhaité|demandé|pour|urgent)",
    r"rémunération (prévue|proposée|:)",
    r"mission (freelance|disponible|urgente|courte|longue)",
    r"offre (de mission|de projet|freelance)",
    r"contact(ez|e)[- ]moi",
    r"envoyez[- ](moi|votre|un)",
    r"dm (moi|me)\b",
    r"mission freelance",
    r"recherche prestataire",
    r"cherche freelance",
    r"appels? d.offres?",
    r"cahier des charges",
    r"besoin d.un site",
    r"création (d.un|de) site",
    r"refonte (d.un|de) site",
    r"création (d.un|de) chatbot",
    r"automatisation (des|de) (processus|tâches)",
    r"community manager (recherché|demandé|besoin)",
    r"monteur vidéo (recherché|demandé|besoin)",
    r"graphiste (recherché|demandé|besoin)",
]

# Signaux anglais acceptés uniquement pour sources internationales
STRONG_SIGNALS_EN = [
    r"who is hiring",
    r"looking for (a |an )?(freelancer|contractor|developer|designer|editor|manager)",
    r"need (someone|a person|a dev|a developer|a freelancer) to (build|create|make|develop|edit|manage)",
    r"want to (hire|contract|outsource)",
    r"looking to (hire|outsource|contract)",
    r"\[hiring\]",
    r"budget[:$€]?\s*\$?[\d,]{2,}",
    r"dm (me|us)\b",
    r"reach out",
    r"send (me|us) (your|a|an)",
    r"open to (offers|proposals|bids|quotes)",
]

# Sources françaises (filtrage plus strict)
FRENCH_SOURCES = ["Free-work", "Alsacréations", "Malt.fr"]

# Sources internationales (filtrage anglais autorisé)
INTL_SOURCES = ["Hacker News", "Reddit", "Remotive", "RemoteOK", "Himalayas", "dev.to"]


def _is_french(text: str) -> bool:
    """Détermine si un texte est principalement en français."""
    text_lower = text.lower()
    words = text_lower.split()
    if len(words) < 3:
        return False
    
    french_count = sum(1 for w in words if w in FRENCH_MARKERS)
    ratio = french_count / len(words)
    
    # Considéré français si au moins 8% des mots sont des marqueurs FR
    return ratio >= 0.08


def _has_strong_signal_fr(text: str, title: str) -> bool:
    """Vérifie la présence d'un signal fort de demande prestataire FR."""
    combined = f"{title} {text}".lower()
    return any(re.search(p, combined) for p in STRONG_SIGNALS_FR)


def _has_strong_signal_en(text: str, title: str) -> bool:
    """Vérifie la présence d'un signal fort de demande prestataire EN."""
    combined = f"{title} {text}".lower()
    return any(re.search(p, combined) for p in STRONG_SIGNALS_EN)


def classify_and_score(post: dict) -> dict:
    """
    Analyse et score un post avec filtrage strict.
    Ne garde que les posts FR avec un signal clair de demande prestataire.
    """
    text = post.get("raw_text", "").lower()
    title = post.get("title", "").lower()
    source = post.get("source", "")
    
    # ── 1. ÉLIMINATION PAR PATTERNS D'EXCLUSION ──────────────────────────
    for pattern in EXCLUSION_PATTERNS:
        if re.search(pattern, title):
            post["categories"] = [{"name": "Non classifié", "icon": "❓", "keyword_hits": 0}]
            post["score"] = 0
            return post
    
    # ── 2. VÉRIFICATION LANGUE ────────────────────────────────────────────
    is_french = _is_french(f"{title} {text}")
    is_french_source = any(fs in source for fs in FRENCH_SOURCES)
    
    # Pour les sources françaises : texte DOIT être en français
    if is_french_source and not is_french:
        post["categories"] = [{"name": "Non classifié", "icon": "❓", "keyword_hits": 0}]
        post["score"] = 0
        return post
    
    # ── 3. SIGNAUX FORTS ─────────────────────────────────────────────────
    has_strong_fr = _has_strong_signal_fr(text, title)
    has_strong_en = _has_strong_signal_en(text, title)
    
    # Sources FR : signal FR obligatoire
    if is_french_source and not has_strong_fr:
        # Exception : les plateformes de freelance ont un signal implicite
        # car ce sont des plateformes de missions
        if "freelance" not in text and "mission" not in text:
            post["categories"] = [{"name": "Non classifié", "icon": "❓", "keyword_hits": 0}]
            post["score"] = 1
            return post
    
    # Sources internationales : signal FR ou EN
    if not is_french_source:
        if not has_strong_fr and not has_strong_en:
            post["categories"] = [{"name": "Non classifié", "icon": "❓", "keyword_hits": 0}]
            post["score"] = 1
            return post
        
        # Pour sources intl, on privilégie le contenu FR
        # Si le contenu est en anglais sans rapport FR → score réduit
        if not is_french and has_strong_en and not has_strong_fr:
            # Signal anglais uniquement = score plafonné à 3
            post["categories"] = [{"name": "Non classifié", "icon": "❓", "keyword_hits": 0}]
            post["score"] = 3
            return post
    
    # ── 4. CALCUL DU SCORE ────────────────────────────────────────────────
    score = 4  # Base pour signal fort détecté
    
    # Signal fort dans le titre = +2
    if has_strong_fr and any(re.search(p, title) for p in STRONG_SIGNALS_FR):
        score += 2
    elif has_strong_en and any(re.search(p, title) for p in STRONG_SIGNALS_EN):
        score += 2
    
    # Mots-clés d'intention supplémentaires (max +2)
    intent_hits = sum(1 for kw in INTENT_KEYWORDS_FR if kw in text)
    score += min(intent_hits, 2)
    
    # Budget / montant (max +1)
    if re.search(r"\b(budget|€|\$|eur|devis|tarif|prix|rémunér|ht|jour)\b", text):
        score += 1
    
    # Contact visible (max +1)
    if post.get("contact"):
        score += 1
    
    # Bonus source française
    if is_french_source or is_french:
        score += 1
    
    # ── 5. DÉTECTION DES CATÉGORIES ───────────────────────────────────────
    detected = []
    combined_text = f"{title} {text}"
    
    for cat_name, cat_info in CATEGORIES.items():
        hits = sum(
            1 for kw in cat_info["keywords"]
            if f" {kw} " in f" {combined_text} " or combined_text.startswith(kw) or f" {kw}" in combined_text
        )
        if hits > 0:
            detected.append({
                "name": cat_name,
                "icon": cat_info["icon"],
                "keyword_hits": hits,
            })
    
    detected.sort(key=lambda c: c["keyword_hits"], reverse=True)
    detected = detected[:3]
    
    if not detected:
        detected = [{"name": "Non classifié", "icon": "❓", "keyword_hits": 0}]
    
    post["categories"] = detected
    post["score"] = min(score, 10)
    return post


def filter_relevant(posts: list) -> list:
    """Filtre, enrichit et trie les posts par score décroissant."""
    enriched = [classify_and_score(p) for p in posts]
    filtered = [p for p in enriched if p["score"] >= RELEVANCE_THRESHOLD]
    return sorted(filtered, key=lambda p: p["score"], reverse=True)
