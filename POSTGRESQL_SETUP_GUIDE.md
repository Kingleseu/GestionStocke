# Guide de Configuration PostgreSQL Local et Production

## 🎯 Objectif

Configurer votre projet pour utiliser PostgreSQL :
- **En local** : Votre base `redpos_db` existante
- **Sur Railway** : Base PostgreSQL persistante

## ✅ Étape 1 : Créer le fichier .env (LOCAL)

Dans le dossier `GestionStocke`, créez un fichier nommé `.env` (sans extension) avec ce contenu :

```env
DATABASE_URL=postgresql://redpos_user:Eben@1999@127.0.0.1:5432/redpos_db
SECRET_KEY=django-insecure-local-dev-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Comment créer le fichier** :
1. Ouvrez VS Code
2. Fichier → Nouveau fichier
3. Enregistrez-le comme `.env` dans `c:\Users\ebenn\Pictures\GestionStocke\`
4. Copiez le contenu ci-dessus

## ✅ Étape 2 : Installer python-dotenv

```bash
python -m pip install python-dotenv
```

## ✅ Étape 3 : Exécuter les Migrations Localement

```bash
cd c:\Users\ebenn\Pictures\GestionStocke
python manage.py migrate
```

Cela créera toutes les tables dans votre base PostgreSQL locale `redpos_db`.

## ✅ Étape 4 : Créer un Superutilisateur Local

```bash
python manage.py createsuperuser
```

Entrez vos informations :
- Username : `admin` (ou ce que vous voulez)
- Email : votre email
- Password : votre mot de passe

## ✅ Étape 5 : Tester Localement

```bash
python manage.py runserver
```

Allez sur `http://localhost:8000` et vérifiez que :
- ✅ Vous pouvez vous connecter
- ✅ Vous pouvez créer des produits/catégories
- ✅ Les données persistent après redémarrage du serveur

## 🚀 Étape 6 : Configurer Railway (PRODUCTION)

### 6.1 Ajouter PostgreSQL sur Railway

1. Allez sur [railway.app](https://railway.app)
2. Ouvrez votre projet `GestionStocke`
3. Cliquez sur **"+ New"**
4. Sélectionnez **"Database"** → **"Add PostgreSQL"**
5. Railway créera la base automatiquement

### 6.2 Vérifier DATABASE_URL

1. Cliquez sur votre service web (Django)
2. Allez dans **"Variables"**
3. Vous devriez voir `DATABASE_URL` automatiquement configuré
4. Si absent, ajoutez-le :
   - Cliquez **"New Variable"** → **"Add Reference"**
   - Sélectionnez votre PostgreSQL
   - Choisissez `DATABASE_URL`

### 6.3 Configurer les Variables Railway

Dans **"Variables"** de votre service web, ajoutez :

```
SECRET_KEY=<générez une clé forte>
DEBUG=False
```

**Pour générer SECRET_KEY** :
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6.4 Déployer

```bash
git add .
git commit -m "feat: Configure PostgreSQL for local and production"
git push origin main
```

Railway redéploiera automatiquement.

## 🔍 Vérification

### Local
```bash
python manage.py check --database default
```

Devrait afficher : `System check identified no issues (0 silenced).`

### Railway (dans les logs)

Vous devriez voir :
```
✅ Database connection successful!
🔄 Running database migrations...
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
👤 Creating superuser if needed...
```

## 📊 Comment ça Fonctionne

### En Local (Développement)
1. Django charge le fichier `.env`
2. Lit `DATABASE_URL=postgresql://redpos_user:...`
3. Se connecte à votre PostgreSQL local
4. Les données sont stockées dans `redpos_db`

### Sur Railway (Production)
1. Railway configure automatiquement `DATABASE_URL`
2. Django utilise cette variable
3. Se connecte au PostgreSQL de Railway
4. Les données persistent entre les déploiements ✅

## 🎉 Résultat

- ✅ **Local** : Données dans PostgreSQL local
- ✅ **Railway** : Données dans PostgreSQL Railway
- ✅ **Plus de perte de données** sur Railway !
- ✅ **Environnement identique** local et production

## 🐛 Dépannage

### Erreur : "relation does not exist"
```bash
python manage.py migrate
```

### Erreur : "could not connect to server"
Vérifiez que PostgreSQL est démarré :
- Windows : Services → PostgreSQL
- Ou redémarrez votre PC

### Railway : SQLite au lieu de PostgreSQL
Vérifiez que `DATABASE_URL` est bien configuré dans Railway Variables.

## 📝 Commandes Utiles

```bash
# Voir l'état des migrations
python manage.py showmigrations

# Créer des migrations après modification de models
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur local
python manage.py runserver
```

## ⚠️ Important

- **NE JAMAIS** commiter le fichier `.env` sur Git
- Il est déjà dans `.gitignore`
- Chaque développeur doit créer son propre `.env`
- Utilisez `.env.example` comme template
