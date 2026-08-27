# ============================================================
#  CONFIGURATION — Outil de Prospection
#  Modifiez ce fichier pour personnaliser l'outil
# ============================================================

# ------------------------------------------------------------
#  REDDIT — Renseignez vos identifiants d'application Reddit
#  Tutoriel : https://www.reddit.com/prefs/apps
# ------------------------------------------------------------
REDDIT_CLIENT_ID = "VOTRE_CLIENT_ID"          # Chaîne courte sous le nom de l'app
REDDIT_CLIENT_SECRET = "VOTRE_CLIENT_SECRET"  # Champ "secret"
REDDIT_USER_AGENT = "ProspectionTool/1.0 by local_user"

# Mettre False pour désactiver Reddit sans supprimer les credentials
REDDIT_ENABLED = True

# ------------------------------------------------------------
#  SOURCES — Activez/désactivez chaque source
# ------------------------------------------------------------
SOURCES = {
    "hackernews":    True,   # API Algolia publique — threads "Who is hiring"
    "devto":         False,  # Blog platform — désactivé (trop d'articles, pas de demandes)
    "reddit":        REDDIT_ENABLED,
    "malt":          False,  # ⚠️ Désactivé — bloqué par Cloudflare (HTTP 403)
    "alsacreations": True,   # Forum français — section emplois/projets
    "freework":      True,   # Free-work.com — missions freelance françaises publiques
    "indiehackers":  False,  # Désactivé (peu de contenu français)
    "remotive":      True,   # Remotive.com — API publique, jobs remote internationaux
    "remoteok":      True,   # RemoteOK — API publique, jobs remote internationaux
    "himalayas":     True,   # Himalayas.app — API publique, jobs remote
}

# ------------------------------------------------------------
#  SUBREDDITS à surveiller (si Reddit activé)
# ------------------------------------------------------------
REDDIT_SUBREDDITS = [
    # Subreddits de recrutement freelance (anglais)
    "forhire",
    "hiring",
    # Subreddits entrepreneurs / startups
    "Entrepreneur",
    "startups",
    "smallbusiness",
    # Subreddits français
    "EntrepreneursFR",
    "france",
    "webdev",
    # Subreddits catégories
    "socialmedia",
    "videography",
    "3Dmodeling",
    "blender",
    "ChatbotDevelopment",
    "learnprogramming",
]

# Nombre de posts récents à analyser par subreddit
REDDIT_POST_LIMIT = 50

# ------------------------------------------------------------
#  MOTS-CLÉS DE DÉTECTION — Indicateurs de demande prestataire
# ------------------------------------------------------------
INTENT_KEYWORDS_FR = [
    "cherche", "recherche", "besoin", "recrute", "recrutement",
    "projet", "devis", "budget", "freelance", "prestataire",
    "développeur", "agence", "réaliser", "créer", "faire réaliser",
    "qui peut", "quelqu'un pour", "mission", "embauche", "sous-traitance",
    "collaborer", "partenaire", "aide", "offre", "proposition",
    # Anglais — pour sources internationales (HN, dev.to, IndieHackers)
    "looking for", "hiring", "hire", "seeking", "need a",
    "need someone", "who is hiring", "want to build",
    "budget", "freelancer", "developer wanted", "remote job",
]

# Score minimum (0-10) pour inclure un résultat dans le rapport
# Avec la logique stricte du classifier, seuls les vrais posts de demande
# atteignent ce seuil (score de base = 4 dès qu'un signal fort est détecté)
RELEVANCE_THRESHOLD = 4

# ------------------------------------------------------------
#  6 CATÉGORIES avec leurs mots-clés associés
# ------------------------------------------------------------
CATEGORIES = {
    "Site Web": {
        "icon": "🌐",
        "keywords": [
            "site web", "site internet", "siteweb", "website", "landing page",
            "page web", "vitrine", "e-commerce", "ecommerce", "boutique en ligne",
            "wordpress", "shopify", "wix", "webflow", "refonte", "portfolio",
            "développement web", "front-end", "frontend", "html", "css",
        ],
    },
    "Chatbot": {
        "icon": "🤖",
        "keywords": [
            "chatbot", "chat bot", "bot", "assistant", "assistant virtuel",
            "agent conversationnel", "assistant ia", "llm", "gpt",
            "automatiser les réponses", "répondre automatiquement",
            "intelligence artificielle", "ia", "support automatique",
            "voicebot", "callbot",
        ],
    },
    "Automatisation": {
        "icon": "⚙️",
        "keywords": [
            "automatisation", "automatiser", "automation", "script", "workflow",
            "no-code", "nocode", "zapier", "make", "n8n", "integromat",
            "processus", "tâches répétitives", "gain de temps", "scraping",
            "api", "intégration", "synchronisation", "pipeline", "python",
            "excel automatique", "macro",
        ],
    },
    "Modélisation 3D": {
        "icon": "🧊",
        "keywords": [
            "3d", "modélisation", "modele 3d", "modèle 3d", "blender",
            "cinema 4d", "3ds max", "maya", "cao", "conception 3d",
            "rendu 3d", "animation 3d", "impression 3d", "objet 3d",
            "visualisation", "architecture 3d", "vue 3d", "texture",
        ],
    },
    "Montage Vidéo": {
        "icon": "🎬",
        "keywords": [
            "montage vidéo", "montage", "vidéo", "video", "editing",
            "motion design", "motion graphic", "after effects", "premiere pro",
            "davinci resolve", "final cut", "sous-titrage", "sous-titres",
            "générique", "animation vidéo", "reel", "teaser", "clip",
            "youtube", "reels", "tiktok", "court-métrage",
        ],
    },
    "Réseaux Sociaux": {
        "icon": "📱",
        "keywords": [
            "réseaux sociaux", "social media", "community manager", "cm",
            "instagram", "linkedin", "facebook", "twitter", "tiktok",
            "gestion compte", "gestion de compte", "contenu", "posts",
            "publication", "stratégie social media", "calendrier éditorial",
            "influenceur", "marketing digital", "community management",
            "identité numérique", "personal branding",
        ],
    },
}

# ------------------------------------------------------------
#  PARAMÈTRES HACKER NEWS
# ------------------------------------------------------------
HN_MAX_RESULTS = 50       # Nombre max de posts HN à analyser par requête
HN_DAYS_BACK = 7          # Chercher dans les X derniers jours

# ------------------------------------------------------------
#  PARAMÈTRES DEV.TO
# ------------------------------------------------------------
DEVTO_MAX_ARTICLES = 30   # Nombre max d'articles dev.to à analyser

# ------------------------------------------------------------
#  PARAMÈTRES GÉNÉRAUX
# ------------------------------------------------------------
RESULTS_DIR = "results"   # Dossier de sauvegarde des rapports
REQUEST_DELAY = 1.0       # Délai en secondes entre les requêtes (bonne pratique)
REQUEST_TIMEOUT = 15      # Timeout HTTP en secondes
