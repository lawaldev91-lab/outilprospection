"""
Classificateur — associe chaque post à une ou plusieurs catégories
et calcule un score de pertinence (0-10).

Logique stricte : seul un post avec un signal CLAIR de demande de prestataire
peut atteindre le seuil minimal. Un article ou une offre d'emploi salarié
est éliminé dès la première passe.
"""
import re
from config import CATEGORIES, INTENT_KEYWORDS_FR, RELEVANCE_THRESHOLD

# ── LISTE NOIRE : articles, guides, offres d'emploi CDI ─────────────────────
# Si le TITRE matche l'un de ces patterns → score = 0, ignoré
NEGATIVE_TITLE_PATTERNS = [
    # Articles / tutoriels
    r"^how to\b", r"^guide\b", r"^tutorial\b", r"^tips\b", r"^tip:\b",
    r"^the (complete|ultimate|best|top|minimum|definitive|essential)\b",
    r"^(top|best) \d+\b", r"^\d+ (tips|ways|steps|mistakes|tools|reasons)\b",
    r"^i built\b", r"^i made\b", r"^i created\b", r"^i wrote\b",
    r"^introducing\b", r"^announcing\b", r"^released?\b",
    r"how i (built|made|created|learned|use|manage)",
    r"^(lessons|things) (learned|i learned|to know)\b",
    r"^building (better|a|an|your|my)\b",
    r"^seeking feedback\b", r"^show hn:\b", r"^ask hn: how\b",
    r"^understanding\b", r"^exploring\b", r"^getting started\b",
    r"^why (you|i|we)\b", r"^what (is|are|i|you)\b",
    # Offres d'emploi salarié (on cherche un employé, pas un prestataire)
    r"(senior|junior|lead|staff|principal)\s+(php|rails|devops|java|python|ruby|engineer|developer|designer)",
    r"is hiring (a|an|our|its)\s+(senior|junior|first|new|remote)\b",
    r"full[- ]?time (position|role|job|engineer|developer|designer)",
    r"\b(salary|compensation|equity|pto|benefits|health insurance|401k)\b",
    r"years? of experience (required|preferred|needed)",
    r"(apply|application) (here|now|below|at|via|through)",
    # Contenu non pertinent
    r"expense track", r"financial guide", r"billable hours",
    r"freelance (finance|tax|contract|invoice|rate|pricing) guide",
    r"^the minimum viable\b",
]

# ── SIGNAUX FORTS : vraie demande de prestataire / projet ───────────────────
# Au moins UN de ces patterns doit matcher pour qu'un post soit considéré
MUST_HAVE_ONE_OF = [
    # Français — demandes explicites
    r"je cherche (un|une|des|quelqu)",
    r"nous cherchons (un|une|des)",
    r"cherche (un|une) (développeur|dev|freelance|prestataire|graphiste|monteur|community)",
    r"besoin d.un (développeur|dev|freelance|prestataire|site|chatbot|bot|script|automatisation|monteur|graphiste)",
    r"besoin d.aide (pour|sur|avec)",
    r"recherche (un|une) (développeur|dev|freelance|prestataire|graphiste|monteur|community)",
    r"qui (peut|pourrait|saurait) (créer|développer|réaliser|faire|coder|monter|gérer)",
    r"faire (réaliser|créer|développer|coder|monter|gérer) (un|une|mon|ma|notre)",
    r"projet (à réaliser|en cours|disponible|urgent|rémunéré)",
    r"budget (prévu|disponible|alloué|de|:)\s*[\d€]",
    r"devis (souhaité|demandé|pour|urgent)",
    r"rémunération (prévue|proposée|:)",
    r"mission (freelance|disponible|urgente|courte|longue)",
    r"offre (de mission|de projet|freelance)",
    r"contact(ez|e)[- ]moi",
    r"envoyez[- ](moi|votre|un)",
    r"dm (moi|me)\b",
    # Anglais — fils de recrutement freelance reconnus
    r"who is hiring",
    r"freelancer\? seeking freelancer",
    r"looking for (a |an )?(freelancer|contractor|developer|designer|editor|manager)",
    r"need (someone|a person|a dev|a developer|a freelancer) to (build|create|make|develop|edit|manage)",
    r"want to (hire|contract|outsource)",
    r"looking to (hire|outsource|contract)",
    r"\[hiring\]", r"\[h\]\b",
    r"budget[:$€]?\s*\$?[\d,]{2,}",
    r"dm (me|us)\b",
    r"reach out",
    r"send (me|us) (your|a|an)",
    r"open to (offers|proposals|bids|quotes)",
]


def classify_and_score(post: dict) -> dict:
    """
    Analyse et score un post. Seuls les posts avec un signal CLAIR
    de demande prestataire passent le seuil.
    """
    text = post.get("raw_text", "").lower()
    title = post.get("title", "").lower()

    # ── 1. ÉLIMINATION IMMÉDIATE ────────────────────────────────────────────
    # Titre = article / guide / offre CDI → score 0
    for pattern in NEGATIVE_TITLE_PATTERNS:
        if re.search(pattern, title):
            post["categories"] = [{"name": "Non classifié", "icon": "❓", "keyword_hits": 0}]
            post["score"] = 0
            return post

    # ── 2. CONDITION NÉCESSAIRE : au moins un signal fort ──────────────────
    # Sans signal explicite de demande → max score = 2 (en dessous du seuil)
    has_strong_signal = any(re.search(p, text) for p in MUST_HAVE_ONE_OF)
    has_strong_in_title = any(re.search(p, title) for p in MUST_HAVE_ONE_OF)

    if not has_strong_signal and not has_strong_in_title:
        post["categories"] = [{"name": "Non classifié", "icon": "❓", "keyword_hits": 0}]
        post["score"] = 1  # Trop bas pour passer le seuil
        return post

    # ── 3. CALCUL DU SCORE (post avec signal fort) ─────────────────────────
    score = 4  # Base pour tout post ayant passé les deux filtres

    # +2 si le signal fort est dans le titre (très explicite)
    if has_strong_in_title:
        score += 2

    # +1 par mot-clé d'intention supplémentaire (max +2)
    intent_hits = sum(1 for kw in INTENT_KEYWORDS_FR if kw in text)
    score += min(intent_hits, 2)

    # +1 si budget / montant mentionné explicitement
    if re.search(r"\b(budget|€|\$|eur|devis|tarif|prix|rémunér)\b", text):
        score += 1

    # +1 si email de contact visible
    if post.get("contact"):
        score += 1

    # ── 4. DÉTECTION DES CATÉGORIES ────────────────────────────────────────
    detected = []
    for cat_name, cat_info in CATEGORIES.items():
        hits = sum(
            1 for kw in cat_info["keywords"]
            if f" {kw} " in f" {text} " or title.startswith(kw) or f" {kw}" in title
        )
        if hits > 0:
            detected.append({
                "name": cat_name,
                "icon": cat_info["icon"],
                "keyword_hits": hits,
            })

    detected.sort(key=lambda c: c["keyword_hits"], reverse=True)
    detected = detected[:3]  # max 3 catégories par post

    if not detected:
        detected = [{"name": "Non classifié", "icon": "❓", "keyword_hits": 0}]

    post["categories"] = detected
    post["score"] = min(score, 10)
    return post


def filter_relevant(posts: list[dict]) -> list[dict]:
    """Filtre, enrichit et trie les posts par score décroissant."""
    enriched = [classify_and_score(p) for p in posts]
    filtered = [p for p in enriched if p["score"] >= RELEVANCE_THRESHOLD]
    return sorted(filtered, key=lambda p: p["score"], reverse=True)
