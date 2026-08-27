# 🔗 Scraping d'URL Personnalisée — Guide d'utilisation

## 🎯 Fonctionnalité

Le **Custom URL Scraper** vous permet d'analyser **n'importe quelle URL** pour y détecter automatiquement des opportunités de prospection (missions freelance, offres d'emploi, demandes de prestataires).

---

##  Comment ça marche

### 1. **Détection automatique du type de page**
L'outil analyse la structure HTML pour déterminer :
- Page d'offre unique
- Page de liste (job board)
- Article de blog
- Page inconnue

### 2. **Multi-stratégies d'extraction**
Selon le type détecté :
- Extraction des cartes d'offres
- Analyse des liens internes pertinents
- Parsing du contenu textuel
- Détection de contacts (email, téléphone)

### 3. **Filtrage intelligent**
- **Mode strict** : applique le classificateur français (100% FR uniquement)
- **Mode flexible** : accepte tout contenu potentiellement pertinent

### 4. **Gestion robuste des erreurs**
- Retries automatiques (2 tentatives)
- Timeouts configurables
- Respect du rate limiting
- Logging détaillé

---

## 🚀 Utilisation

### Via l'interface web

1. Ouvrez l'application : `python3 app.py`
2. Allez sur `http://localhost:5000`
3. Section **" Scraping d'URL personnalisée"**
4. Entrez vos URLs (une par ligne, max 10)
5. Cochez/décochez **"Filtrage strict"**
6. Cliquez **"🔍 Analyser les URLs"**
7. Les résultats apparaissent instantanément

### Via l'API REST

```bash
# Single URL
curl -X POST http://localhost:5000/api/custom-scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://exemple.com/offres"], "strict": true}'

# Multiple URLs
curl -X POST http://localhost:5000/api/custom-scrape \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://job-board.com/missions",
      "https://forum.com/demandes",
      "https://site.fr/offres-freelance"
    ],
    "strict": false
  }'
```

### Réponse API

```json
{
  "success": true,
  "opportunities": [
    {
      "id": "custom_123456",
      "title": "Développeur Full Stack Python",
      "body": "Mission freelance 6 mois...",
      "url": "https://...",
      "source": "Custom URL",
      "date": "2026-08-27",
      "contact": "contact@exemple.com",
      "raw_text": "...",
      "score": 8,
      "categories": [
        {"name": "Site Web", "icon": "🌐", "keyword_hits": 3}
      ]
    }
  ],
  "page_type": "list_page",
  "page_title": "Offres d'emploi tech",
  "total_links": 45,
  "pages_scanned": 1,
  "total_opportunities": 1,
  "errors": []
}
```

---

## 📋 Exemples d'URLs supportées

### ✅ Fonctionnent bien
- Job boards : `https://jobs.example.com/offres`
- Pages de missions : `https://freelance-platform.com/missions`
- Forums d'emploi : `https://forum.com/section-offres`
- Pages carrière : `https://entreprise.com/careers`

### ⚠️ Limitations connues
- **Sites 100% JavaScript (SPA React/Angular)** : nécessitent un navigateur headless (Selenium/Playwright)
- **Sites avec Cloudflare strict** : peuvent bloquer le scraping
- **Sites avec CAPTCHA** : non supportés
- **PDF, Word, Excel** : formats non supportés

---

##  Configuration

Dans `core/custom_scraper.py` :

```python
REQUEST_TIMEOUT = 15       # Timeout HTTP (secondes)
MAX_RETRIES = 2            # Tentatives en cas d'erreur
RETRY_DELAY = 2            # Délai entre retries (secondes)
MAX_BODY_LENGTH = 2000     # Longueur max du corps extrait
MAX_RESULTS_PER_PAGE = 20  # Max opportunités par page
```

---

## 🎯 Meilleures pratiques

### 1. **Validez vos URLs**
- Utilisez des URLs complètes avec `https://`
- Vérifiez que la page est accessible dans votre navigateur
- Évitez les URLs avec paramètres de session

### 2. **Choisissez le bon mode**
- **Strict** : pour des résultats 100% français et pertinents
- **Flexible** : pour explorer et voir tout ce qui est détecté

### 3. **Limitez le nombre d'URLs**
- Maximum 10 URLs par requête
- Pour plus d'URLs, faites plusieurs appels

### 4. **Analysez les erreurs**
- Si `success: false`, lisez le message `error`
- Les erreurs partielles sont dans le tableau `errors`

---

## 🐛 Dépannage

### "Aucune opportunité trouvée"
- Essayez avec `strict: false`
- Vérifiez que la page contient bien des offres d'emploi
- Certains sites JavaScript ne peuvent pas être scrapés

### "Accès refusé (403)"
- Le site bloque le scraping
- Essayez un User-Agent différent dans `HEADERS`
- Utilisez un proxy si nécessaire

### "Timeout après 15s"
- Le site est lent ou inaccessible
- Augmentez `REQUEST_TIMEOUT` dans la config
- Vérifiez votre connexion internet

### "Contenu non-HTML reçu"
- L'URL pointe vers un fichier (PDF, image, etc.)
- Vérifiez que l'URL est bien une page web

---

## 📊 Statistiques

L'outil retourne des métriques utiles :
- **pages_scanned** : nombre de pages analysées
- **total_opportunities** : opportunités trouvées
- **total_links** : liens trouvés sur la page
- **page_type** : type de page détecté

---

## 🔐 Sécurité

- **Rate limiting** : délais entre les requêtes
- **Timeouts** : protection contre les pages lentes
- **Validation** : vérification des URLs et extensions
- **Logging** : traçabilité des actions

---

## 🎓 Exemples concrets

### Exemple 1 : Job board français
```
URL : https://www.welcometothejungle.com/fr/companies/techcorp/jobs
Type détecté : list_page
Résultats : 15 offres d'emploi
```

### Exemple 2 : Page carrière entreprise
```
URL : https://startup.fr/carrieres
Type détecté : single_opportunity
Résultats : 1 offre détaillée
```

### Exemple 3 : Forum freelance
```
URL : https://forum-freelance.com/demandes
Type détecté : article
Résultats : 8 demandes de missions
```

---

##  Intégration avec le reste de l'outil

Les résultats du custom scraper sont **compatibles** avec :
- ✅ Le classificateur (`core/classifier.py`)
- ✅ L'historique (`core/history.py`)
- ✅ Les notifications email (`core/notifier.py`)
- ✅ L'export CSV

Vous pouvez donc :
1. Scanner des URLs personnalisées
2. Sauvegarder dans l'historique
3. Recevoir les résultats par email
4. Exporter en CSV

---

## 📈 Roadmap

Améliorations prévues :
- [ ] Support des sites JavaScript (Selenium/Playwright)
- [ ] Scraping de PDF et documents
- [ ] Détection automatique de la langue
- [ ] Extraction de données structurées (schema.org)
- [ ] Cache intelligent pour éviter les re-scrapings

---

## 📝 Licence

MIT — Utilisation libre personnelle et commerciale.
