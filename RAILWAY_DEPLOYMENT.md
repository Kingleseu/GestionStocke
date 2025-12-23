# Guide de Déploiement sur Railway

## 🚂 Pourquoi Railway ?

Railway offre une expérience de déploiement supérieure pour Django avec PostgreSQL :

- ✅ **PostgreSQL automatique** : Base de données provisionnée en un clic
- ✅ **DATABASE_URL auto-configuré** : Pas de configuration manuelle
- ✅ **Migrations automatiques** : Exécutées à chaque déploiement
- ✅ **Interface intuitive** : Dashboard simple et clair
- ✅ **Logs en temps réel** : Debugging facile
- ✅ **Déploiement Git** : Push et déploiement automatique

## 📋 Prérequis

1. Un compte Railway.app (gratuit pour commencer)
2. Votre code sur GitHub
3. Ce projet Django configuré

## 🚀 Déploiement Étape par Étape

### Étape 1 : Créer un Projet Railway

1. Allez sur [railway.app](https://railway.app)
2. Cliquez sur **"New Project"**
3. Sélectionnez **"Deploy from GitHub repo"**
4. Autorisez Railway à accéder à votre GitHub
5. Sélectionnez le dépôt `GestionStocke`

### Étape 2 : Ajouter PostgreSQL

1. Dans votre projet Railway, cliquez sur **"+ New"**
2. Sélectionnez **"Database"** → **"Add PostgreSQL"**
3. Railway créera automatiquement la base de données
4. La variable `DATABASE_URL` sera automatiquement ajoutée à votre service

### Étape 3 : Configurer les Variables d'Environnement

Dans votre service Railway, allez dans **"Variables"** et ajoutez :

```bash
# Obligatoires
SECRET_KEY=<générez une clé secrète forte>
DEBUG=False

# Optionnelles (déjà configurées par défaut)
ALLOWED_HOSTS=.railway.app,.up.railway.app
CSRF_TRUSTED_ORIGINS=https://*.railway.app,https://*.up.railway.app
```

**Pour générer une SECRET_KEY** :
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Étape 4 : Déployer

1. Railway détectera automatiquement votre projet Django
2. Le build commencera automatiquement
3. Suivez les logs en temps réel dans l'onglet **"Deployments"**

### Étape 5 : Vérifier le Déploiement

Dans les logs, vous devriez voir :

```
======================================
🚂 Railway Deployment Starting
======================================
⏳ Waiting for database...
✅ Database connection successful!
🔄 Running database migrations...
📁 Collecting static files...
👤 Creating superuser if needed...
✅ Superuser created: username=admin, password=admin123
======================================
✅ Deployment setup complete!
🚀 Starting Gunicorn server...
======================================
```

### Étape 6 : Accéder à l'Application

1. Railway vous fournira une URL (ex: `https://gestionstocke-production.up.railway.app`)
2. Cliquez sur l'URL ou allez dans **"Settings"** → **"Domains"**
3. Connectez-vous avec :
   - **Username** : `admin`
   - **Password** : `admin123`

⚠️ **IMPORTANT** : Changez immédiatement ce mot de passe !

## 🔧 Configuration des Fichiers

Votre projet est maintenant configuré avec :

### 1. `railway.json`
Configuration Railway avec healthcheck et workers optimisés.

### 2. `nixpacks.toml`
Spécifie Python 3.13 et les phases de build.

### 3. `railway.sh`
Script de démarrage qui :
- Attend que la base de données soit prête
- Exécute les migrations
- Collecte les fichiers statiques
- Crée un superutilisateur
- Lance Gunicorn

### 4. `Procfile`
Définit les commandes web et release.

### 5. `settings.py`
Configuré pour détecter automatiquement Railway :
- `DATABASE_URL` automatique
- `ALLOWED_HOSTS` pour Railway
- SQLite en développement, PostgreSQL en production

## 🎯 Domaine Personnalisé (Optionnel)

Pour utiliser votre propre domaine :

1. Allez dans **"Settings"** → **"Domains"**
2. Cliquez sur **"Custom Domain"**
3. Ajoutez votre domaine (ex: `gestionstocke.com`)
4. Configurez les DNS selon les instructions Railway
5. Mettez à jour `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` :

```bash
ALLOWED_HOSTS=.railway.app,.up.railway.app,gestionstocke.com,www.gestionstocke.com
CSRF_TRUSTED_ORIGINS=https://*.railway.app,https://*.up.railway.app,https://gestionstocke.com,https://www.gestionstocke.com
```

## 🐛 Résolution des Problèmes

### Erreur : "relation 'auth_user' does not exist"

**Cause** : Les migrations n'ont pas été exécutées

**Solution** :
1. Vérifiez les logs de déploiement
2. Assurez-vous que PostgreSQL est bien ajouté au projet
3. Redéployez manuellement si nécessaire

### Erreur : "could not connect to server"

**Cause** : La base de données n'est pas prête

**Solution** :
- Le script `railway.sh` attend automatiquement la base de données
- Si le problème persiste, vérifiez que PostgreSQL est bien provisionné

### Erreur : "DisallowedHost"

**Cause** : Le domaine n'est pas dans `ALLOWED_HOSTS`

**Solution** :
1. Vérifiez votre URL Railway
2. Ajoutez-la à la variable d'environnement `ALLOWED_HOSTS`

### Les fichiers statiques ne se chargent pas

**Cause** : WhiteNoise ou collectstatic

**Solution** :
1. Vérifiez que `whitenoise` est dans `requirements.txt`
2. Les fichiers statiques sont collectés automatiquement par `railway.sh`
3. Redéployez si nécessaire

### Voir les logs en temps réel

```bash
# Dans le dashboard Railway
Cliquez sur votre service → Onglet "Deployments" → Cliquez sur le déploiement actif
```

## 💻 Commandes Utiles

### Accéder au Shell Railway

Railway ne fournit pas de shell interactif direct, mais vous pouvez :

1. **Utiliser Railway CLI** :
```bash
# Installer Railway CLI
npm i -g @railway/cli

# Se connecter
railway login

# Lier au projet
railway link

# Exécuter des commandes
railway run python manage.py shell
railway run python manage.py createsuperuser
railway run python manage.py migrate
```

2. **Ajouter un Job One-Off** :
   - Dans Railway, créez un nouveau service
   - Utilisez le même repo
   - Commande : `python manage.py <votre_commande>`

### Commandes Django Utiles

```bash
# Créer un superutilisateur
railway run python manage.py createsuperuser

# Voir l'état des migrations
railway run python manage.py showmigrations

# Exécuter les migrations
railway run python manage.py migrate

# Collecter les fichiers statiques
railway run python manage.py collectstatic

# Accéder au shell Django
railway run python manage.py shell
```

## 🔄 Redéploiement

Pour redéployer après des modifications :

```bash
git add .
git commit -m "Votre message"
git push origin main
```

Railway redéploiera automatiquement !

## 💾 Base de Données

### Sauvegardes

Railway effectue des sauvegardes automatiques de votre PostgreSQL.

Pour créer une sauvegarde manuelle :
1. Allez dans votre service PostgreSQL
2. Onglet **"Data"**
3. Cliquez sur **"Backup"**

### Accéder à la Base de Données

```bash
# Via Railway CLI
railway connect postgres

# Ou utilisez les credentials dans l'onglet "Connect"
```

### Variables de Connexion

Railway fournit automatiquement :
- `DATABASE_URL` : URL complète de connexion
- `PGHOST` : Hôte PostgreSQL
- `PGPORT` : Port
- `PGUSER` : Utilisateur
- `PGPASSWORD` : Mot de passe
- `PGDATABASE` : Nom de la base

## 🔐 Sécurité

### Checklist de Sécurité

- [ ] `DEBUG=False` en production
- [ ] `SECRET_KEY` forte et unique
- [ ] Mot de passe admin changé
- [ ] `ALLOWED_HOSTS` configuré correctement
- [ ] `CSRF_TRUSTED_ORIGINS` configuré
- [ ] HTTPS activé (automatique sur Railway)

### Changer le Mot de Passe Admin

```bash
railway run python manage.py changepassword admin
```

Ou via l'interface admin Django : `/admin/`

## 📊 Monitoring

### Voir les Métriques

Dans Railway :
1. Cliquez sur votre service
2. Onglet **"Metrics"**
3. Visualisez :
   - CPU usage
   - Memory usage
   - Network traffic
   - Request count

### Logs

Les logs sont disponibles en temps réel dans l'onglet **"Deployments"**.

## 💰 Coûts

Railway offre :
- **Plan Gratuit** : $5 de crédit gratuit par mois
- **Plan Hobby** : $5/mois pour usage personnel
- **Plan Pro** : À partir de $20/mois pour production

Votre application Django + PostgreSQL devrait tenir dans le plan gratuit pour commencer.

## 🆘 Support

- **Documentation Railway** : [docs.railway.app](https://docs.railway.app)
- **Discord Railway** : [discord.gg/railway](https://discord.gg/railway)
- **Status** : [status.railway.app](https://status.railway.app)

## ✅ Checklist Finale

- [ ] Projet créé sur Railway
- [ ] PostgreSQL ajouté au projet
- [ ] Variables d'environnement configurées
- [ ] Code poussé sur GitHub
- [ ] Déploiement réussi
- [ ] Migrations exécutées (vérifier les logs)
- [ ] Superutilisateur créé
- [ ] Application accessible via l'URL Railway
- [ ] Connexion admin fonctionnelle
- [ ] Mot de passe admin changé
- [ ] Fichiers statiques chargés
- [ ] Tests de base effectués

## 🎉 Félicitations !

Votre application Django est maintenant déployée sur Railway avec PostgreSQL !

**URL de votre application** : Disponible dans Railway Dashboard

**Prochaines étapes** :
1. Testez toutes les fonctionnalités
2. Configurez un domaine personnalisé (optionnel)
3. Créez vos utilisateurs managers et caissiers
4. Commencez à utiliser votre système de gestion !

---

**Besoin d'aide ?** Consultez les logs Railway ou la documentation officielle.
