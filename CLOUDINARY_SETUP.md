# Guide : Stockage des Images avec Cloudinary

Pour que vos photos de produits ne disparaissent plus à chaque mise à jour, nous allons brancher **Cloudinary**.

---

## Étape 1 : Créer votre compte Cloudinary

1. Allez sur [Cloudinary.com](https://cloudinary.com) et créez un compte gratuit.
2. Une fois connecté, allez sur votre **Dashboard**.
3. Cherchez la ligne **"API Environment variable"**.
4. Elle ressemble à ceci : `cloudinary://123456789:abcdefg@hijk`
5. **Copiez cette URL complète**.

## Étape 2 : Configurer Render.com

1. Allez sur votre dashboard **Render.com**.
2. Cliquez sur votre service Web **"gestionstocke"**.
3. Allez dans l'onglet **"Environment"**.
4. Cliquez sur **"Add Environment Variable"** :
   - **Key** : `CLOUDINARY_URL`
   - **Value** : Collez l'URL de Cloudinary récupérée à l'étape 1.
5. Cliquez sur **"Save Changes"**.

---

## Étape 3 : Appliquer les changements (Côté Code)

J'ai déjà préparé les fichiers nécessaires. Il vous suffit de :

1. Pousser les modifications que j'ai faites vers GitHub.
2. Render va redéployer.
3. Téléchargez une nouvelle image de produit pour tester.
4. Magie ! L'image est maintenant stockée dans le cloud et ne disparaîtra plus.

---

## 📂 Où seront stockées mes photos ?

Une fois configuré, toutes vos photos seront sur votre compte **Cloudinary** :
1. Dans l'onglet **Media Library**.
2. Dans un dossier nommé automatiquement par le système (généralement `django_cloudinary_storage/`).

## 🔄 Comment "déplacer" mes photos actuelles ?

Il y a deux façons de synchroniser vos photos locales vers Cloudinary :

### Option A : La méthode simple (Recommandée)
Comme vous n'avez probablement pas des milliers de produits, le plus sûr est de :
1. Allez sur votre site en ligne (Render).
2. Allez dans l'administration des produits.
3. Cliquez sur un produit, et **téléchargez à nouveau son image**.
4. Django l'enverra directement sur Cloudinary.

### Option B : La méthode automatique (Avancée)
Si vous avez beaucoup d'images, je peux vous créer un script spécial (`migrate_to_cloudinary.py`) que vous lancerez sur votre ordinateur. Cela prendra toutes les images de votre dossier `media` et les enverra d'un coup sur Cloudinary.

---

## ✅ Résumé
- **Nouvelles images** : Automatiquement sur Cloudinary.
- **Images actuelles** : À re-télécharger une fois ou à migrer via script.
- **En local** : Si vous n'avez pas de `CLOUDINARY_URL` dans votre fichier `.env`, vos images resteront sur votre PC. Si vous l'ajoutez, même votre PC enverra les images vers Cloudinary !
