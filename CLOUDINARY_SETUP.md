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

## 💡 Pourquoi Cloudinary ?
- **Gratuit** : Très large quota pour les petits projets.
- **Rapide** : Les images sont compressées automatiquement pour charger plus vite.
- **Fiable** : Vos fichiers sont en sécurité, même si Render redémarre l'application.
