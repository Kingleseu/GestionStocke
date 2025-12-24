# Railway PostgreSQL Setup Guide

## 🚨 Problème Actuel

Votre application utilise **SQLite** au lieu de **PostgreSQL** sur Railway. C'est pourquoi vous voyez :
```
'ENGINE': 'django.db.backends.sqlite3'
```

## ✅ Solution : Ajouter PostgreSQL sur Railway

### Étape 1 : Ajouter PostgreSQL à votre Projet

1. Allez sur [railway.app](https://railway.app)
2. Ouvrez votre projet `GestionStocke`
3. Cliquez sur **"+ New"**
4. Sélectionnez **"Database"** → **"Add PostgreSQL"**
5. Railway créera automatiquement la base de données

### Étape 2 : Lier PostgreSQL à votre Service Web

1. Cliquez sur votre service web (celui qui exécute Django)
2. Allez dans l'onglet **"Variables"**
3. Vous devriez voir `DATABASE_URL` apparaître automatiquement
4. Si ce n'est pas le cas :
   - Cliquez sur **"New Variable"** → **"Add Reference"**
   - Sélectionnez votre base PostgreSQL
   - Choisissez `DATABASE_URL`

### Étape 3 : Redéployer

Une fois `DATABASE_URL` configuré, redéployez :

1. Dans Railway, cliquez sur votre service web
2. Allez dans **"Deployments"**
3. Cliquez sur **"Redeploy"** (ou poussez un nouveau commit)

Le script `railway.sh` exécutera automatiquement :
- Les migrations sur PostgreSQL
- La création du superutilisateur
- La collecte des fichiers statiques

## 🔍 Vérification

Après le redéploiement, vérifiez dans les logs que vous voyez :

```
✅ Database connection successful!
🔄 Running database migrations...
  Operations to perform:
    Apply all migrations: admin, auth, contenttypes, sessions, accounts, products, sales...
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
👤 Creating superuser if needed...
✅ Superuser created: username=admin, password=admin123
```

## 📊 Vérifier la Base de Données Utilisée

Dans les logs de démarrage, vous devriez voir :
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # ✅ PostgreSQL
        'NAME': 'railway',
        'HOST': 'xxxxx.railway.app',
        ...
    }
}
```

Au lieu de :
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # ❌ SQLite
        ...
    }
}
```

## 🐛 Problèmes Résolus

### 1. IntegrityError: UNIQUE constraint failed

✅ **Corrigé** dans `accounts/views.py` :
- La vue `signup_view` utilise maintenant le profil créé par le signal
- La vue `register_cashier_view` fait de même
- Plus de conflit de création de profil

### 2. SQLite au lieu de PostgreSQL

✅ **Solution** : Ajouter PostgreSQL sur Railway
- Railway configurera automatiquement `DATABASE_URL`
- L'application détectera PostgreSQL et l'utilisera

## 📝 Variables d'Environnement Requises

Assurez-vous d'avoir ces variables dans Railway :

```bash
# Automatique (fourni par Railway quand vous ajoutez PostgreSQL)
DATABASE_URL=postgresql://...

# À configurer manuellement
SECRET_KEY=<votre-clé-secrète>
DEBUG=False
```

## 🎯 Prochaines Étapes

1. ✅ Pousser les corrections de code
2. ✅ Ajouter PostgreSQL sur Railway
3. ✅ Vérifier que `DATABASE_URL` est configuré
4. ✅ Redéployer
5. ✅ Tester l'inscription

```bash
git add .
git commit -m "fix: Resolve UserProfile UNIQUE constraint error"
git push origin main
```

Ensuite, ajoutez PostgreSQL sur Railway et redéployez !
