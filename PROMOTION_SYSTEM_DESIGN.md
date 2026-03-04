# 🎯 Système Intelligent de Promotions Programmables

## 📋 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────┐
│           GESTION DE STOCK + BOUTIQUE                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐         ┌──────────────────┐    │
│  │  INVENTAIRE      │         │   PRODUITS       │    │
│  │  (Stock)         │         │   (Détails)      │    │
│  └────────┬─────────┘         └────────┬─────────┘    │
│           │                           │               │
│           └─────────────┬─────────────┘               │
│                         │                             │
│          ┌──────────────▼──────────────┐              │
│          │                             │              │
│          │  🎉 PROMOTIONS [NOUVEAU]   │              │
│          │                             │              │
│          │  • Règles de réduction      │              │
│          │  • Programmation temp       │              │
│          │  • Bannières marketing      │              │
│          │  • Calcul automatique       │              │
│          │                             │              │
│          └──────────────┬──────────────┘              │
│                         │                             │
│         ┌───────────────┴───────────────┐             │
│         │                               │             │
│    ┌────▼────┐                   ┌─────▼────┐        │
│    │  STORE  │                   │  AFFICHAGE│       │
│    │ (Vente) │                   │  (Badges) │       │
│    └─────────┘                   └───────────┘        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture de données

### 1. Modèle `Promotion`

```python
class Promotion(Model):
    # Identité
    name = CharField(max_length=100)  # ex: "Soldes Printemps"
    description = TextField()         # Description détaillée
    
    # Réduction
    discount_type = ChoiceField(['percentage', 'fixed'])
    discount_value = DecimalField()    # % ou montant
    
    # Portée
    scope = ChoiceField(['all_products', 'specific_products'])
    products = ManyToMany(Product, blank=True)
    categories = ManyToMany(Category, blank=True)
    
    # Programmation temporelle
    start_date = DateTimeField()
    end_date = DateTimeField()
    is_active = BooleanField(default=True)
    
    # Marketing visuel
    banner_image = ImageField()
    banner_message = CharField(max_length=200)
    display_badge = BooleanField(default=True)
    
    # Métadonnées
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    created_by = ForeignKey(User)
```

### 2. Modèle `PromotionLog` (Audit)

```python
class PromotionLog(Model):
    promotion = ForeignKey(Promotion)
    action = CharField()  # 'created', 'activated', 'deactivated', 'updated'
    timestamp = DateTimeField(auto_now_add=True)
    details = JSONField()
```

---

## 💰 Logique de calcul des prix

### Fonction: `calculate_promotion_price(product, date=now)`

```
1. Récupérer toutes les promotions actives à cette date
2. Vérifier si le produit est concerné
   - Si scope='all_products' → applicable
   - Si scope='specific_products' → vérifier si produit dans la liste
3. Calculer le prix réduit :
   - Si discount_type='percentage' : 
     prix_reduit = prix * (1 - discount_value/100)
   - Si discount_type='fixed' :
     prix_reduit = prix - discount_value
4. Retourner { original_price, reduced_price, discount_percent, promotion }
```

---

## 🎨 Interface Gestionnaire (Admin)

### Vue de liste des promotions

```
┌─────────────────────────────────────────────────────────┐
│  🎉 PROMOTIONS                           [+ Nouvelle]   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ ☑ │ Nom              │ Réduc │ Produits │ Dates    │   │
│───┼──────────────────┼───────┼──────────┼──────────┤   │
│ ☑ │ Soldes Printemps │ -20%  │ 15 prod  │ Mar1-15  │ 🟢│
│ ☑ │ Black Friday     │ -30%  │ Tous     │ Nov29-3D │ 🟡│
│ ☑ │ Clearance 2024   │ -50%  │ 5 prod   │ Expiré   │ ⚫│
│                                                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Formulaire de création

```
┌────────────────────────────────────────────────────────────┐
│          📝 Nouvelle Promotion                             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 📌 INFORMATIONS GÉNÉRALES                                 │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Nom: ___________________________________          │   │
│ │ Description: _______________________________       │   │
│ └────────────────────────────────────────────────────┘   │
│                                                            │
│ 💰 RÉDUCTION                                              │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Type: (•) Pourcentage  ( ) Montant fixe           │   │
│ │ Valeur: _________                                 │   │
│ │                                                   │   │
│ │ Exemple: -20% = Nouveau prix : 80€ (100€ × 0.8)  │   │
│ └────────────────────────────────────────────────────┘   │
│                                                            │
│ 🎯 PORTÉE                                                 │
│ ┌────────────────────────────────────────────────────┐   │
│ │ ( ) Tous les produits                              │   │
│ │ (•) Produits sélectionnés                          │   │
│ │                                                   │   │
│ │ [Sélectionner les produits] ▼                      │   │
│ │ ☑ Chaise Design                                   │   │
│ │ ☑ Table Basse                                     │   │
│ │ ☑ Lampadaire                                      │   │
│ │                                                   │   │
│ │ Ou sélectionner par catégorie:                     │   │
│ │ ☑ Moibilier  ☑ Éclairage  ☑ Accessoires          │   │
│ └────────────────────────────────────────────────────┘   │
│                                                            │
│ ⏰ PROGRAMMATION                                           │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Début: [01/03/2026] à [00:00] ▼                  │   │
│ │ Fin:   [15/03/2026] à [23:59] ▼                  │   │
│ │                                                   │   │
│ │ ☑ Promotion active                               │   │
│ │                                                   │   │
│ │ Status: 🟢 PROGRAMMÉE (commence dans 5 jours)   │   │
│ └────────────────────────────────────────────────────┘   │
│                                                            │
│ 👁️ MARKETING VISUEL                                      │
│ ┌────────────────────────────────────────────────────┐   │
│ │ Bannière: [Télécharger image] ▼                   │   │
│ │ Message: "🎉 Soldes du Printemps! -20% tout! " │   │
│ │                                                   │   │
│ │ ☑ Afficher un badge sur les produits              │   │
│ │   Exemple de badge: [SOLDES -20%]                │   │
│ └────────────────────────────────────────────────────┘   │
│                                                            │
│ [❌ Annuler]  [✅ Créer Promotion]                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🛍️ Affichage Frontend (Boutique)

### Produit Sans Promotion
```
┌──────────────────────┐
│   [Image Produit]    │
│                      │
│  Chaise Design       │
│  ★★★★★ (124 avis)   │
│                      │
│  💰 120€             │
│                      │
│  [Ajouter au panier] │
└──────────────────────┘
```

### Produit Avec Promotion ACTIVE
```
┌──────────────────────┐
│   [Image Produit]    │
│ ┌────────────────┐   │
│ │ 🏷️  -20% OFF   │   │  ← Badge promo
│ └────────────────┘   │
│  Chaise Design       │
│  ★★★★★ (124 avis)   │
│                      │
│  💰 ~~120€~~ 96€     │  ← Prix barré + prix réduit
│     Prix réduit ↑    │
│                      │
│  [Ajouter au panier] │
└──────────────────────┘
```

### Bannière Promotionnelle (Zone Hero)
```
╔════════════════════════════════════════════════════════╗
║                                        ┌──────────────┐║
║  🎉 SOLDES PRINTEMPS!                  │ Jusqu'au 15  ║║
║                                        │ Mars 🔴      ║║
║  Profitez de -20% sur l'ensemble       │ 23:59        ║║
║  de nos meubles de design dans         └──────────────┘║
║  le catalogue printemps.                               ║
║                                                         ║
║  [🛍️ DÉCOUVRIR LES OFFRES]                            ║
║                                                         ║
╚════════════════════════════════════════════════════════╝
```

---

## ⚙️ Fonctionnalités Avancées

### 1. **Tasksplanifiées (Celery/APScheduler)**
```python
# Activation/désactivation automatique
@scheduled_task(cron="*/5 * * * *")  # Toutes les 5 min
def check_and_update_promotions():
    now = timezone.now()
    
    # Activer les promotions dont l'heure est venue
    to_activate = Promotion.objects.filter(
        start_date__lte=now,
        end_date__gte=now,
        is_active=False
    )
    to_activate.update(is_active=True)
    
    # Désactiver les promotions expirées
    to_deactivate = Promotion.objects.filter(
        end_date__lt=now,
        is_active=True
    )
    to_deactivate.update(is_active=False)
```

### 2. **Système de Notifications**
```
- Email au gestionnaire quand une promo commence
- Email au gestionnaire quand une promo finit
- SMS/Pop-up d'alerte pour promo bientôt expirée
```

### 3. **Rapport d'Efficacité**
```
- Nombre de produits affectés
- Réduction de chiffre d'affaires vs hausse des ventes
- Durée d'exécution
- Nombre de clients ayant acheté en promo
```

---

## 🔴 Design Visuel - Palette Couleurs

| Élément | Couleur |
|---------|---------|
| Badge Promotion | 🔴 **#E63946** (Rouge vif) |
| Header/Footer | 🔴 **#B1242F** (Rouge foncé) |
| Accents | 🔵 **#1F77B4** (Bleu) |
| Textes | ⚫ **#1A1A1A** (Noir) |
| Fond badge | 🔴 **#E63946** avec texte blanc |
| Bouton CTA | 🔴 **#E63946** |

### Exemple Badge CSS
```css
.promotion-badge {
    background-color: #E63946;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 12px;
    display: inline-block;
}

.promotion-badge:after {
    content: "% OFF";
    margin-left: 2px;
}
```

---

## 📊 Workflow Complet

```
1. GESTIONNAIRE crée une promotion
   ↓
2. SYSTÈME valide les données
   ↓
3. PROMOTION stockée en DB avec statut "programmée"
   ↓
4. SCHEDULER vérifie toutes les 5 minutes
   ↓
5. À start_date → Activation auto (is_active=True)
   ↓
6. FRONTEND détecte promo active → Affiche badge + prix réduit
   ↓
7. À end_date → Désactivation auto (is_active=False)
   ↓
8. FRONTEND revient à l'affichage normal
```

---

## 📦 Structure des fichiers à créer

```
promotions/
├── __init__.py
├── apps.py
├── models.py              # Modèles Promotion, PromotionLog
├── views.py               # Vues admin et API
├── serializers.py         # Sérializers API
├── admin.py               # Interface admin Django
├── forms.py               # Formulaires
├── utils.py               # Calcul des prix, logique promo
├── tasks.py               # Celery tasks (scheduler)
├── urls.py
├── migrations/
│   └── 0001_initial.py
├── management/
│   └── commands/
│       └── check_promotions.py
└── templates/
    └── promotions/
        ├── promotion_list.html
        ├── promotion_form.html
        └── promotion_detail.html
```

---

## 🎯 Prochaines étapes

1. ✅ Créer l'app `promotions`
2. ✅ Définir les modèles
3. ✅ Créer les migrations
4. ✅ Implémenter le calcul de prix
5. ✅ Créer l'interface admin
6. ✅ Intégrer au frontend (store)
7. ✅ Mettre en place le scheduler
8. ✅ Ajouter les bannières marketing
9. ✅ Tester complètement

---

**Status:** 🟢 Prêt à l'implémentation
