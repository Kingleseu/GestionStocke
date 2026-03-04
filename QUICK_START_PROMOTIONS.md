# 🚀 GUIDE DÉMARRAGE RAPIDE - Promotions

## En 5 minutes: Créez votre première promotion!

---

## ✅ Étape 1: Appliquer les migrations

```bash
python manage.py migrate promotions
```

Résultat attendu:
```
Running migrations:
  Applying promotions.0001_initial... OK
```

---

## ✅ Étape 2: Accéder à l'admin

1. Ouvrez: `http://localhost:8000/admin/`
2. Connectez-vous avec votre compte admin
3. Dans la sidebar gauche, cliquez sur **"Promotions"**

---

## ✅ Étape 3: Créer une promotion

### Via l'interface admin (Plus facile)

1. Cliquez sur **"Ajouter Promotion"** (bouton vert)
2. Remplissez les champs:

| Champ | Exemple |
|-------|---------|
| Nom | "Soldes Printemps" |
| Description | "Réduction spéciale mars 2026" |
| Type de réduction | Pourcentage |
| Valeur | 20 |
| Portée | Tous les produits |
| Début | 15/03/2026 00:00 |
| Fin | 30/03/2026 23:59 |
| Activer | ✅ Cocher |

3. Cliquez **"Sauvegarder"** ✅

### Via Django Shell (Pour les devs)

```python
python manage.py shell

from django.utils import timezone
from datetime import timedelta
from promotions.models import Promotion
from django.contrib.auth.models import User

user = User.objects.first()  # Prendre un utilisateur

Promotion.objects.create(
    name="Black Friday",
    discount_type="percentage",
    discount_value=30,
    scope="all_products",
    start_date=timezone.now(),
    end_date=timezone.now() + timedelta(days=3),
    is_active=True,
    created_by=user
)

exit()
```

---

## ✅ Étape 4: Voir la promotion

Visitez: `http://localhost:8000/promotions/`

Vous verrez votre promotion listée avec:
- Statut (active, programmée, expirée)
- Réduction appliquée
- Dates
- Actions (Voir, Modifier, Supprimer)

---

## ✅ Étape 5 (Optionnel): Afficher au store

Ajoutez à votre template produit (`store/templates/store/product_list.html`):

```html
<!-- Autour de chaque produit -->
{% with pricing=product.get_pricing %}
    
    <!-- Badge si en promo -->
    {% if pricing.has_promotion %}
    <div class="promo-badge">
        {{ pricing.promotion.get_badge_text }}
    </div>
    {% endif %}
    
    <!-- Prix original barré -->
    {% if pricing.has_promotion %}
    <del class="price-original">{{ pricing.original_price }}€</del>
    {% endif %}
    
    <!-- Prix réduit -->
    <strong class="price-current">
        {{ pricing.discounted_price }}€
    </strong>
    
{% endwith %}
```

---

## 🎯 Scénarios courants

### Scénario 1: Veille promotionnelle
**Vous voulez une promo qui démarre demain**

1. Allez dans Admin > Promotions > Ajouter
2. Remplissez tout
3. Mettez **Début = Demain à 08:00**
4. Mettez **is_active = Activé**
5. Sauvegardez

→ La promo sera automatiquement activée demain à 08:00 ✅

### Scénario 2: Promo sur certains produits

1. Admin > Promotions > Ajouter
2. Portée = **"Produits sélectionnés"**
3. Sélectionnez les produits (Chaise, Lampe, etc.)
4. Sauvegardez

→ Seuls ces produits auront la réduction ✅

### Scénario 3: Montant fixe

1. Admin > Promotions > Ajouter
2. Type = **"Montant fixe (€)"**
3. Valeur = **10.00**
4. Sauvegardez

→ Tous les prix baissent de 10€ ✅

### Scénario 4: Bannière marketing

1. Admin > Promotions > Ajouter
2. Descendez à "Marketing visuel"
3. Uploadez une image pour bannière
4. Message = "🎉 SOLDES PRINTEMPS!"
5. Afficher badge = ✅
6. Sauvegardez

→ La bannière s'affichera au store ✅

---

## 💻 Commandes utiles

### Vérifier les promos en cours

```bash
python manage.py shell

from promotions.models import Promotion
from django.utils import timezone

promos = Promotion.objects.filter(
    is_active=True,
    start_date__lte=timezone.now(),
    end_date__gte=timezone.now()
)

for p in promos:
    print(f"✅ {p.name}: -{p.discount_value}{'%' if p.discount_type == 'percentage' else '€'}")

exit()
```

### Mettre à jour les statuts (Manuel)

```bash
python manage.py check_promotions
```

Résultat:
```
Mise à jour effectuée:
   • 2 promotion(s) activée(s)
   • 1 promotion(s) désactivée(s)
🎉 1 promotion(s) actuellement actif(ve)
```

### Lancer les tests

```bash
python manage.py test promotions
```

---

## ⚙️ Configuration avancée (Optionnel)

### Activer l'automatisation Celery

Si vous avez Celery configuré, ajoutez à `redpos/settings.py`:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'sync-promotions-every-5-min': {
        'task': 'promotions.tasks.sync_promotion_status',
        'schedule': crontab(minute='*/5'),
    },
}
```

Puis:
```bash
celery -A redpos worker -B
```

---

## 🐛 Dépannage

### "Aucune migration appliquée"?

```bash
python manage.py migrate promotions
```

### "Erreur: promotions not found"?

Vérifiez que `'promotions'` est dans `INSTALLED_APPS` dans `settings.py`

### "Les prix réduits ne s'affichent pas"?

1. Créez une promotion
2. Vérifiez qu'elle est active
3. Utilisez `product.get_pricing()` dans vos templates

### Plus d'infos?

Consultez: `PROMOTIONS_README.md`

---

## 📊 Interface admin

### Barre de menu admin

```
Admin Django
└── Promotions
    ├── Promotions (🟢 Active, 🟡 Programmée, ⚫ Expirée)
    └── Journaux (Historique des actions)
```

### Filtres disponibles

- Type de réduction (%, €)
- Portée (Tous/Produits/Catégories)
- Actif/Inactif
- Date de création

### Recherche

Recherchez par:
- Nom de la promotion
- Description
- Message bannière

---

## ✨ Personnalisations

### Changer les couleurs des badges

Modifiez dans le template:

```html
<span class="badge" style="background-color: #3498db;">
    SOLDES
</span>
```

### Ajouter un texte personnalisé

Dans la création de la promo:
- Champ "Texte du badge personnalisé" = "PROMO FLASH"

→ Au lieu de "-20%", le badge affichera "PROMO FLASH"

---

## 🎓 Cas d'usage réels

### Exemple 1: Premiers clients

```
Nom: Réduction premiers clients
Réduction: 10€
Type: Montant fixe
Portée: Tous les produits
Début: Aujourd'hui
Fin: Fin du mois
```

### Exemple 2: Clear Stock

```
Nom: Liquidation stock 2025
Réduction: 50%
Type: Pourcentage
Portée: Produits sélectionnés (Vieux stock)
Début: Demain
Fin: Dans 1 semaine
```

### Exemple 3: Événement spécial

```
Nom: Fête des Mères -20%
Réduction: 20%
Type: Pourcentage
Portée: Catégorie Accessoires
Début: 25/05/2026
Fin: 31/05/2026
Bannière: Image de fleurs
Message: "Fête des Mères! -20% sur tout!"
```

---

## 🎯 Prochaines étapes

1. ✅ Créer votre première promotion
2. ✅ Tester l'interface admin
3. ✅ Intégrer au store (voir PROMOTION_INTEGRATION_GUIDE.md)
4. ✅ Tester les prix réduits
5. ✅ Mettre en production

---

## 📞 Besoin d'aide?

- **Interface admin**: Consultez les tooltips (?) dans l'admin
- **Code**: Lisez les docstrings dans `promotions/`
- **Guides complets**: Voir `PROMOTIONS_README.md`
- **Tests**: Lancez `python manage.py test promotions`

---

**Vous êtes maintenant prêt à gérer des promotions! 🎉**

Bonne chance! 🚀
