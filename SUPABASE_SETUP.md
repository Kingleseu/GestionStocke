# Guide : Connecter Supabase (PostgreSQL) à Render

## Pourquoi utiliser Supabase ?
Render Free PostgreSQL expire après **90 jours**. 
**Supabase** est gratuit, plus puissant, et vos données ne seront pas supprimées.

---

## Étape 1 : Créer votre base de données sur Supabase

1. Allez sur [Supabase.com](https://supabase.com) et créez un compte gratuit.
2. Cliquez sur **"New Project"**.
3. Donnez un nom (ex: `redpos-db`).
4. Choisissez un mot de passe pour la base de données (**Notez-le bien !**).
5. Cliquez sur **"Create new project"**.

## Étape 2 : Récupérer l'URL du "Transaction Pooler" (IMPORTANT)

Sur Render, la connexion échoue car l'adresse par défaut est en **IPv6** (non supporté par Render). Vous devez utiliser le **Pooler Host** :

1. Allez dans **Settings** -> **Database** sur Supabase.
2. Dans **Connection string**, sélectionnez l'onglet **"URI"**.
3. **TRÈS IMPORTANT** : Changez le mode de "Direct Connection" à **"Transaction Pooler"**.
4. L'URL doit changer complètement. 
   - **Direct (ne marche pas)** : `db.zgtfp...supabase.co:5432`
   - **Pooler (à utiliser)** : `aws-0-xxxx.pooler.supabase.com:6543`
5. Copiez cette nouvelle URL (veillez à ce que le mot de passe soit correct).

## Étape 3 : Configurer Render.com

1. Allez sur votre dashboard **Render.com**.
2. Cliquez sur votre service Web **"gestionstocke"**.
3. Allez dans l'onglet **"Environment"**.
4. Cliquez sur **"Add Environment Variable"** :
   - **Key** : `DATABASE_URL`
   - **Value** : Collez l'URL de Supabase récupérée à l'étape 2.
5. Cliquez sur **"Save Changes"**.

---

## Étape 4 : Déployer et Vérifier

1. Render va redéployer votre application automatiquement.
2. Allez dans l'onglet **"Logs"** de votre service web sur Render.
3. Vous devriez voir au début du build :
   `🚀 Using Database: django.db.backends.postgresql`
4. Attendez le message :
   `🔄 Running database migrations... OK`
5. Une fois que c'est **"Live"**, tout fonctionnera parfaitement et vos données ne disparaîtront plus jamais !

---

## 💡 Astuce : Comment savoir si ça marche ?

Si vous voyez une erreur `no such table: auth_user` après avoir mis l'URL Supabase :
- Cela veut dire que l'URL est correcte, mais que les migrations n'ont pas encore tourné.
- Redémarrez le build dans Render (**Manual Deploy** -> **Clear Build Cache & Deploy**).
