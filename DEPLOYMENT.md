# Guide de Déploiement sur Render

## Problème Résolu

Ce guide vous aide à résoudre l'erreur `django.db.utils.ProgrammingError: relation "auth_user" does not exist` qui se produit lorsque les migrations Django n'ont pas été exécutées sur la base de données PostgreSQL de Render.

## Prérequis

- Un compte Render.com
- Une base de données PostgreSQL créée sur Render
- Variables d'environnement configurées

## Étapes de Déploiement

### 1. Configuration des Variables d'Environnement sur Render

Assurez-vous que ces variables sont définies dans votre service Render :

```
SECRET_KEY=<généré automatiquement par Render>
DEBUG=False
ALLOWED_HOSTS=gestionstocke.onrender.com,.onrender.com
DATABASE_URL=<fourni automatiquement par Render depuis la base de données>
CSRF_TRUSTED_ORIGINS=https://gestionstocke.onrender.com,https://*.onrender.com
```

### 2. Déploiement Initial

1. **Connectez votre dépôt GitHub à Render**
2. **Créez un nouveau Web Service**
   - Build Command: `./build.sh`
   - Start Command: `gunicorn redpos.wsgi:application`
   - Environment: Python 3

3. **Créez une base de données PostgreSQL**
   - Dans Render, créez une nouvelle base de données PostgreSQL
   - Liez-la à votre web service via la variable `DATABASE_URL`

4. **Déployez l'application**
   - Render exécutera automatiquement `build.sh`
   - Vérifiez les logs de build pour confirmer que les migrations s'exécutent

### 3. Vérification du Build

Dans les logs de build, vous devriez voir :

```
====================================
Starting Build Process for Render
====================================
📦 Installing dependencies...
📁 Collecting static files...
🔍 Verifying database connection...
📊 Checking migration status...
🔄 Running database migrations...
👤 Creating superuser if needed...
====================================
✅ Build completed successfully!
====================================
```

### 4. Si les Migrations Échouent Pendant le Build

Si les migrations ne s'exécutent pas pendant le build, vous pouvez les exécuter manuellement :

#### Option A : Via le Shell Render

1. Dans votre service Render, allez dans l'onglet "Shell"
2. Exécutez les commandes suivantes :

```bash
# Vérifier la connexion à la base de données
python manage.py check --database default

# Voir l'état des migrations
python manage.py showmigrations

# Exécuter les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser
```

#### Option B : Via un Job Render

1. Créez un nouveau "Job" dans Render
2. Utilisez la même base de données
3. Commande : `python manage.py migrate`

### 5. Créer un Superutilisateur

Le script `build.sh` crée automatiquement un superutilisateur :
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@example.com`

⚠️ **IMPORTANT** : Changez ce mot de passe immédiatement après la première connexion !

Pour créer un superutilisateur manuellement :

```bash
python manage.py createsuperuser
```

### 6. Vérification Post-Déploiement

1. **Accédez à votre application** : `https://gestionstocke.onrender.com`
2. **Testez la page de connexion** : `https://gestionstocke.onrender.com/accounts/login/`
3. **Accédez à l'admin Django** : `https://gestionstocke.onrender.com/admin/`

## Résolution des Problèmes Courants

### Erreur : "relation 'auth_user' does not exist"

**Cause** : Les migrations n'ont pas été exécutées

**Solution** :
1. Vérifiez les logs de build pour voir si les migrations ont échoué
2. Exécutez manuellement les migrations via le Shell Render
3. Vérifiez que `DATABASE_URL` est correctement configurée

### Erreur : "could not connect to server"

**Cause** : Problème de connexion à la base de données

**Solution** :
1. Vérifiez que la base de données PostgreSQL est active
2. Vérifiez que `DATABASE_URL` est correctement liée
3. Vérifiez les paramètres SSL dans `settings.py`

### Erreur : "DisallowedHost"

**Cause** : Le domaine n'est pas dans `ALLOWED_HOSTS`

**Solution** :
1. Ajoutez votre domaine Render à la variable d'environnement `ALLOWED_HOSTS`
2. Format : `gestionstocke.onrender.com,.onrender.com`

### Les fichiers statiques ne se chargent pas

**Cause** : WhiteNoise n'est pas correctement configuré

**Solution** :
1. Vérifiez que `whitenoise` est dans `requirements.txt`
2. Vérifiez que `WhiteNoiseMiddleware` est dans `MIDDLEWARE`
3. Exécutez `python manage.py collectstatic`

## Commandes Utiles

### Vérifier l'état de la base de données
```bash
python manage.py check --database default
```

### Voir toutes les migrations
```bash
python manage.py showmigrations
```

### Exécuter les migrations
```bash
python manage.py migrate --verbosity 2
```

### Créer un superutilisateur
```bash
python manage.py createsuperuser
```

### Collecter les fichiers statiques
```bash
python manage.py collectstatic --no-input
```

### Accéder au shell Django
```bash
python manage.py shell
```

## Maintenance

### Redéploiement

Pour redéployer après des modifications :

1. Poussez vos changements sur GitHub
2. Render redéploiera automatiquement
3. Le script `build.sh` s'exécutera à nouveau

### Sauvegardes de Base de Données

Render effectue des sauvegardes automatiques de votre base de données PostgreSQL. Vous pouvez également créer des sauvegardes manuelles via le tableau de bord Render.

### Mise à Jour des Dépendances

1. Mettez à jour `requirements.txt`
2. Poussez sur GitHub
3. Render réinstallera les dépendances lors du prochain déploiement

## Support

Si vous rencontrez des problèmes :

1. Consultez les logs de build et de runtime dans Render
2. Vérifiez les variables d'environnement
3. Testez localement avec PostgreSQL avant de déployer
4. Consultez la documentation Render : https://render.com/docs

## Checklist de Déploiement

- [ ] Base de données PostgreSQL créée sur Render
- [ ] Variables d'environnement configurées
- [ ] `build.sh` exécutable (`chmod +x build.sh`)
- [ ] Dépôt GitHub connecté à Render
- [ ] Build réussi avec migrations exécutées
- [ ] Superutilisateur créé
- [ ] Page de connexion accessible
- [ ] Admin Django accessible
- [ ] Fichiers statiques chargés correctement
- [ ] Mot de passe admin changé
