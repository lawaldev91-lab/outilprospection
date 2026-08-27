# 🔍 Outil de Prospection v2.0

Application web de veille automatique qui recherche des demandes de prestataires sur des sources publiques, dans 6 catégories : **Site Web · Chatbot · Automatisation · Modélisation 3D · Montage Vidéo · Réseaux Sociaux**.

---

## 🖥️ Interface Web

![Dashboard](https://img.shields.io/badge/UI-Flask%20%2B%20TailwindCSS-blue)

- ✅ Interface moderne avec toggle **Dark/Light mode**
- ✅ Boutons **Démarrer / Arrêter** le scraping
- ✅ **Progression en temps réel** par source
- ✅ **Filtrage** par catégorie et recherche textuelle
- ✅ **Export CSV** en un clic
- ✅ **100% français** — filtrage strict des résultats

## 🔗 Scraping d'URL Personnalisée

Analysez **n'importe quel lien** pour y trouver des opportunités.

- ✅ **Détection automatique** du type de page (job board, article, liste)
- ✅ **Multi-stratégies** d'extraction (cartes, liens, contenu)
- ✅ **Filtrage intelligent** (strict ou flexible)
- ✅ **Gestion robuste** des erreurs avec retries
- ✅ **Max 10 URLs** par analyse

**Utilisation :**
```bash
# Via l'interface web
# Section "Scraping d'URL personnalisée" dans le dashboard

# Via l'API
curl -X POST http://localhost:5000/api/custom-scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://exemple.com/offres"], "strict": true}'
```

**Limitations :**
-  Sites 100% JavaScript (SPA) — nécessitent Selenium/Playwright
-  Sites avec Cloudflare strict ou CAPTCHA
- ✅ Voir `CUSTOM-SCRAPER-GUIDE.md` pour le guide complet

## 📧 Notifications Email

Recevez automatiquement les résultats par email après chaque scraping.

- ✅ Support **Gmail SMTP** (gratuit)
- ✅ Email HTML professionnel avec top 10 des résultats
- ✅ Configuration via fichier `.env`
- ✅ Optionnel — activez quand vous voulez

**Configuration :**
```bash
# Copiez le fichier exemple
cp .env.example .env

# Éditez .env avec vos informations
EMAIL_NOTIFICATIONS=true
SMTP_USER=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-application
NOTIFICATION_EMAIL=votre-email@gmail.com
```

Voir `.env.example` pour les instructions complètes.

## 📈 Historique & Analyses

Suivez les performances jour après jour avec des graphiques interactifs.

- ✅ **Base de données SQLite** pour la persistance
- ✅ **4 graphiques interactifs** (Chart.js) :
  - Évolution des résultats dans le temps
  - Répartition par source
  - Catégories détectées
  - Performance moyenne par source
- ✅ **Statistiques globales** : sessions, total, moyenne, meilleur jour
- ✅ **Historique détaillé** avec tableau complet
- ✅ **Comparaison sur période** : 7, 14, 30, 90 jours

**Accès :** Cliquez sur "📈 Historique" dans le menu principal

---

## 📡 Sources de données

| Source | Type | Status |
|---|---|---|
| **Free-work** | Scraping HTML | ✅ Actif |
| **Alsacréations** | Scraping HTML | ✅ Actif |
| **Remotive** | API publique | ✅ Actif |
| **RemoteOK** | API publique | ✅ Actif |
| **Himalayas** | API publique | ✅ Actif |
| **Hacker News** | API Algolia | ✅ Actif |
| **Reddit** | API OAuth2 | ⚙️ À configurer |
| **Malt.fr** | Scraping HTML | ❌ Bloqué (Cloudflare) |

---

## ⚡ Installation locale

### 1. Cloner le repo
```bash
git clone https://github.com/lawaldev91-lab/outilprospection.git
cd outilprospection
```

### 2. Installer les dépendances
```bash
python3 -m pip install -r requirements.txt
```

### 3. Configurer Reddit (optionnel)
1. Aller sur https://www.reddit.com/prefs/apps
2. Créer une app de type "script"
3. Remplir les credentials dans `core/config.py`

### 4. Lancer l'application
```bash
python app.py
```

Ouvrir http://localhost:5000 dans votre navigateur.

---

## 🚀 Déploiement sur Render.com

### Étape 1 : Créer un compte
1. Aller sur [render.com](https://render.com)
2. Se connecter avec GitHub

### Étape 2 : Nouveau Web Service
1. Cliquer sur **"New +"** → **"Web Service"**
2. Connecter le repo GitHub `outilprospection`
3. Configurer :
   - **Name** : `outil-prospection`
   - **Environment** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. Plan : **Free** (suffisant pour tester)
5. Cliquer sur **"Create Web Service"**

### Étape 3 : C'est déployé !
Render va automatiquement :
- Builder l'application
- La déployer
- Vous donner une URL du type `outil-prospection.onrender.com`

⚠️ **Note** : Le plan gratuit de Render met le serveur en veille après 15 min d'inactivité. Le premier chargement peut prendre 30-60s.

---

## 📁 Structure du projet

```
Outil-prospection/
├── app.py                  ← Point d'entrée Flask
├── core/
│   ├── engine.py           ← Moteur de scraping (start/stop)
│   ├── classifier.py       ← Classification + filtrage strict FR
│   ├── config.py           ← Configuration générale
│   ├── report.py           ← Générateur de rapport HTML
│   └── scrapers/           ← Scrapers individuels
│       ├── hackernews.py
│       ├── reddit.py
│       ├── devto.py
│       ├── freework.py
│       ├── alsacreations.py
│       ├── remotive.py
│       ├── remoteok.py
│       ├── himalayas.py
│       └── indiehackers.py
├── web/
│   └── templates/
│       └── index.html      ← Interface web (TailwindCSS)
├── results/                ← Historique des scans
├── requirements.txt
├── Procfile                ← Pour Render/Heroku
├── runtime.txt             ← Version Python
├── Dockerfile              ← Pour Docker
└── README.md
```

---

## ⚙️ Configuration (`core/config.py`)

| Paramètre | Rôle |
|---|---|
| `SOURCES` | Activer/désactiver chaque source |
| `RELEVANCE_THRESHOLD` | Score minimum (défaut: 4) |
| `REDDIT_CLIENT_ID` | Credentials Reddit API |
| `INTENT_KEYWORDS_FR` | Mots-clés de détection d'intention |
| `CATEGORIES` | Catégories et mots-clés associés |

---

## 🔒 Légalité

- ✅ Sources publiques (sans login)
- ✅ API officielles respectées
- ✅ Scraping respectueux (throttling)
- ✅ robots.txt respecté

---

## 📝 Licence

MIT — Utilisation libre personnelle et commerciale.
