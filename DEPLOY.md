# 🚀 Guide de déploiement sur Render.com

## Prérequis
- Compte GitHub avec le code pushé
- Compte Render.com (gratuit)

## Étapes

### 1. Connecter votre repo GitHub
1. Aller sur [render.com](https://render.com)
2. Cliquer sur **"Sign Up"** (ou "Log In")
3. Se connecter avec GitHub

### 2. Créer un Web Service
1. Cliquer sur **"New +"** → **"Web Service"**
2. Cliquer sur **"Configure account"** si première fois
3. Sélectionner le repo `outilprospection`
4. Cliquer sur **"Connect"**

### 3. Configurer le service
Remplir les champs :
- **Name** : `outil-prospection` (ou ce que vous voulez)
- **Region** : `Frankfurt (EU Central)` (plus proche de vous)
- **Branch** : `main`
- **Root Directory** : (vide, laisser par défaut)
- **Environment** : `Python 3`
- **Build Command** : `pip install -r requirements.txt`
- **Start Command** : `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### 4. Plan et déploiement
- **Instance Type** : `Free` (suffisant pour commencer)
- Cliquer sur **"Create Web Service"**

Render va automatiquement :
1. Cloner votre repo
2. Installer les dépendances
3. Lancer l'application
4. Vous donner une URL publique

### 5. Accéder à votre application
L'URL sera du type :
```
https://outil-prospection.onrender.com
```

---

## ⚠️ Limitations du plan gratuit

- Le serveur se met en veille après 15 min d'inactivité
- Le premier chargement peut prendre 30-60s (cold start)
- 750 heures/mois gratuites (suffisant pour usage personnel)

## 💡 Variables d'environnement (optionnel)

Si vous voulez configurer Reddit :
1. Aller dans **"Environment"** dans le dashboard Render
2. Ajouter :
   - `REDDIT_CLIENT_ID` : votre client ID
   - `REDDIT_CLIENT_SECRET` : votre client secret
   - `REDDIT_ENABLED` : `True`

---

## 🔄 Mises à jour automatiques

Render redéploie automatiquement quand vous push sur `main`.

```bash
git add .
git commit -m "Amélioration: ..."
git push origin main
```

→ Votre app est mise à jour en 2-3 minutes !

---

## 🆘 Dépannage

### L'app ne démarre pas
Vérifier les logs dans le dashboard Render → "Logs"

### Erreur de dépendances
```bash
# En local, tester d'abord
pip install -r requirements.txt
python app.py
```

### Timeout pendant le scraping
Le scraping peut prendre du temps. Augmenter le timeout dans Procfile :
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300
```

---

## 🎉 C'est tout !

Votre outil de prospection est maintenant en ligne et accessible 24/7.
