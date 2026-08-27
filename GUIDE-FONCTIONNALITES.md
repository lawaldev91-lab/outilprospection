# 📧 📈 Guide des nouvelles fonctionnalités

## 📧 Notifications Email

### Configuration (5 minutes)

#### Option 1 : Gmail (recommandé, gratuit)

1. **Activez la vérification en 2 étapes** sur votre compte Google :
   - Allez sur https://myaccount.google.com/security
   - Activez "Validation en 2 étapes"

2. **Générez un mot de passe d'application** :
   - Allez sur https://myaccount.google.com/apppasswords
   - Connectez-vous si nécessaire
   - Sélectionnez "Mail" et "Autre appareil"
   - Nommez-le "Outil Prospection"
   - Cliquez "Générer"
   - **Copiez le mot de passe en 16 caractères** (ex: `abcd efgh ijkl mnop`)

3. **Configurez le fichier .env** :
   ```bash
   # Copiez le fichier exemple
   cd ~/Desktop/Outil-prospection
   cp .env.example .env
   
   # Éditez .env
   nano .env
   ```
   
   Remplissez :
   ```env
   EMAIL_NOTIFICATIONS=true
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=votre-email@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop
   NOTIFICATION_EMAIL=votre-email@gmail.com
   ```

4. **Testez** :
   - Lancez un scraping depuis l'interface
   - Vous recevrez un email avec les résultats !

#### Option 2 : Autre serveur SMTP

Adaptez les variables dans `.env` :
```env
SMTP_SERVER=smtp.votre-fournisseur.com
SMTP_PORT=587
SMTP_USER=votre-login
SMTP_PASSWORD=votre-password
NOTIFICATION_EMAIL=destinataire@exemple.com
```

### Format de l'email

L'email contient :
- 📊 **Header** avec date et nombre de résultats
- 🏆 **Top 10** des opportunités avec liens directs
- 📈 **Statistiques** par source
- 🎨 **Design professionnel** HTML responsive

---

## 📈 Historique & Analyses

### Accès

Depuis le dashboard principal, cliquez sur **"📈 Historique"** dans le menu.

### Fonctionnalités

#### 1. **Période d'analyse**
Choisissez la période : 7, 14, 30 ou 90 jours

#### 2. **Statistiques globales**
- **Sessions** : nombre de scrapings effectués
- **Total résultats** : somme de tous les résultats
- **Moyenne / session** : moyenne de résultats par scraping
- **Meilleur jour** : date avec le plus de résultats

#### 3. **Graphiques interactifs**

**📈 Évolution des résultats**
- Graphique en ligne montrant le nombre de résultats jour après jour
- Identifiez les tendances et pics

**📡 Répartition par source**
- Graphique circulaire (donut)
- Visualisez quelle source apporte le plus de résultats

**🎯 Catégories détectées**
- Graphique en barres
- Voyez quelles catégories reviennent le plus souvent

**⚡ Performance moyenne par source**
- Graphique en barres horizontales
- Comparez l'efficacité de chaque source

#### 4. **Historique détaillé**
Tableau avec pour chaque session :
- Date
- Nombre de résultats
- Durée
- Sources actives
- Top catégories

### Fonctionnement technique

- **Base de données** : SQLite (`results/history.db`)
- **Persistance** : les données sont conservées même après redémarrage
- **Sauvegarde automatique** : chaque scraping est enregistré
- **Nettoyage** : les sessions de plus de 90 jours sont supprimées automatiquement

### API endpoints

```
GET /api/history?days=30          # Historique des 30 derniers jours
GET /api/history/comparison?days=7 # Comparaison sur 7 jours
GET /api/history/sources?days=30   # Stats par source
```

---

## 🚀 Workflow recommandé

### Quotidien
1. Ouvrez l'application : `python3 app.py`
2. Cliquez **"▶️ Démarrer"**
3. Attendez 10-15 secondes
4. Consultez les résultats
5. Exportez en CSV si besoin

### Hebdomadaire
1. Consultez la page **"📈 Historique"**
2. Analysez les tendances
3. Identifiez les sources les plus productives
4. Ajustez la configuration si nécessaire

### Mensuel
1. Revoyez les statistiques globales
2. Comparez les performances sur 30 jours
3. Identifiez les catégories les plus fréquentes
4. Adaptez votre stratégie de prospection

---

## 💡 Conseils d'utilisation

### Notifications email
- ✅ Activez-les si vous voulez un suivi passif
- ✅ Utilisez un email dédié pour éviter le spam
- ✅ Consultez les emails le matin pour voir les résultats de la veille

### Historique
- ✅ Consultez l'historique régulièrement pour identifier les tendances
- ✅ Comparez les performances des sources
- ✅ Utilisez les données pour optimiser votre stratégie

### Sources
- **Free-work** : Très bon pour les missions freelance FR
- **Alsacréations** : Bon pour le web/webdesign FR
- **Remotive/RemoteOK** : Jobs internationaux (souvent en anglais)
- **Himalayas** : Jobs remote variés
- **Hacker News** : Discussions tech (nécessite filtrage)

---

## 🔧 Dépannage

### Notifications email ne fonctionnent pas

1. Vérifiez que `EMAIL_NOTIFICATIONS=true` dans `.env`
2. Vérifiez vos credentials SMTP
3. Pour Gmail, vérifiez que vous utilisez un **mot de passe d'application** (pas votre mot de passe Gmail)
4. Consultez les logs dans le terminal pour voir les erreurs

### Historique vide

1. Lancez au moins un scraping
2. Vérifiez que le fichier `results/history.db` existe
3. Rechargez la page

### Graphiques ne s'affichent pas

1. Vérifiez votre connexion internet (Chart.js est chargé depuis CDN)
2. Videz le cache du navigateur (Ctrl+Shift+R)
3. Essayez un autre navigateur

---

## 🎉 Félicitations !

Votre outil de prospection est maintenant **complet et professionnel** :

✅ Interface web moderne  
✅ Scraping automatique  
✅ Boutons Start/Stop  
✅ Filtrage strict 100% français  
✅ Notifications email  
✅ Historique comparatif  
✅ Graphiques interactifs  
✅ Export CSV  
✅ Prêt pour déploiement  

**Prochaine étape** : Déployez sur Render.com pour un accès 24/7 !

Voir `DEPLOY.md` pour les instructions de déploiement.
