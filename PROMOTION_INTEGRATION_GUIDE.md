# 🎉 Intégration des Promotions au Store/Frontend

## 📋 Guide d'intégration du système de promotions

Ce guide explique comment intégrer le système de promotions au frontend (store) pour afficher les prix réduits et les badges.

---

## 1️⃣ Intégration dans les templates produits

### A. Store - Liste de produits (`store/templates/store/product_list.html`)

```html
{% load static %}

{% for product in products %}
<div class="product-card">
    <!-- Image -->
    <div class="product-image">
        <img src="{{ product.image.url }}" alt="{{ product.name }}">
        
        <!-- Badge promo si applicable -->
        {% with pricing=product.get_pricing %}
            {% if pricing.has_promotion %}
            <div class="promotion-badge" style="background-color: #E63946;">
                {{ pricing.promotion.get_badge_text }}
            </div>
            {% endif %}
        {% endwith %}
    </div>
    
    <!-- Infos produit -->
    <div class="product-info">
        <h3>{{ product.name }}</h3>
        
        <!-- Prix -->
        <div class="price-section">
            {% with pricing=product.get_pricing %}
                {% if pricing.has_promotion %}
                    <span class="price-original" style="text-decoration: line-through; color: #999;">
                        {{ pricing.original_price }}€
                    </span>
                    <span class="price-current" style="color: #E63946; font-weight: bold; font-size: 1.2em;">
                        {{ pricing.discounted_price }}€
                    </span>
                {% else %}
                    <span class="price-current" style="font-weight: bold; font-size: 1.2em;">
                        {{ pricing.original_price }}€
                    </span>
                {% endif %}
            {% endwith %}
        </div>
        
        <!-- Bouton -->
        <a href="{% url 'store:product_detail' product.slug %}" class="btn-view">
            Voir détails →
        </a>
    </div>
</div>
{% endfor %}
```

### B. Store - Détail produit (`store/templates/store/product_detail.html`)

```html
<!-- Section Prix -->
<div class="price-section">
    {% with pricing=product.get_pricing %}
        <div class="price-display">
            {% if pricing.has_promotion %}
                <!-- Bannière promo -->
                <div class="promo-banner" style="background: linear-gradient(135deg, #E63946, #B1242F); color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    🎉 <strong>{{ pricing.promotion.name }}</strong>
                    <p style="margin: 5px 0 0 0; font-size: 0.9em;">{{ pricing.promotion.banner_message }}</p>
                </div>
                
                <!-- Prix -->
                <div style="display: flex; align-items: center; gap: 15px; margin: 20px 0;">
                    <span class="price-original" style="text-decoration: line-through; color: #999; font-size: 1.2em;">
                        {{ pricing.original_price }}€
                    </span>
                    <span class="promotion-badge" style="background: #E63946; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">
                        -{{ pricing.discount_percent|floatformat:0 }}%
                    </span>
                </div>
                
                <!-- Prix réduit -->
                <div style="font-size: 2em; font-weight: bold; color: #2ecc71; margin: 10px 0;">
                    {{ pricing.discounted_price }}€
                </div>
                
                <!-- Économie -->
                <p style="color: #666; font-size: 0.9em; margin: 5px 0;">
                    <strong>Vous économisez:</strong> {{ pricing.savings }}
                </p>
            {% else %}
                <!-- Prix normal -->
                <div style="font-size: 2.5em; font-weight: bold; color: #1A1A1A;">
                    {{ pricing.original_price }}€
                </div>
            {% endif %}
        </div>
    {% endwith %}
</div>
```

---

## 2️⃣ Ajouter la méthode `get_pricing` au modèle Product

Ajoutez cette méthode au modèle `Product` dans `products/models.py`:

```python
from promotions.utils import calculate_product_price

class Product(models.Model):
    # ... champs existants ...
    
    def get_pricing(self):
        """
        Retourne le pricing avec promotions appliquées.
        À utiliser dans les templates.
        """
        return calculate_product_price(self)
```

---

## 3️⃣ Bannière promotionnelle (Page d'accueil)

Créez un nouveau contexte dans votre view d'accueil:

```python
# store/views.py
from promotions.models import Promotion
from django.utils import timezone

def store_home(request):
    now = timezone.now()
    active_promotions = Promotion.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now,
        display_badge=True
    )
    
    context = {
        'active_promotions': active_promotions,
        'products': Product.objects.filter(is_active=True)[:12],
    }
    return render(request, 'store/home.html', context)
```

Template d'accueil:

```html
<!-- store/templates/store/home.html -->
{% extends 'base.html' %}

{% block content %}
<!-- Bannières promotionnelles -->
{% for promo in active_promotions %}
<div class="promo-banner-hero" style="background: linear-gradient(135deg, rgba(230, 57, 70, 0.95), rgba(177, 36, 47, 0.95)); color: white; padding: 40px; text-align: center; margin: 30px 0; border-radius: 10px;">
    {% if promo.banner_image %}
    <img src="{{ promo.banner_image.url }}" alt="{{ promo.name }}" style="max-width: 100%; height: auto; margin-bottom: 20px; border-radius: 8px;">
    {% endif %}
    
    <h2 style="margin: 0 0 15px 0; font-size: 2.5em;">🎉 {{ promo.name }}</h2>
    <p style="margin: 0 0 10px 0; font-size: 1.2em;">{{ promo.banner_message }}</p>
    <p style="margin: 0; opacity: 0.9;">
        Valable jusqu'au {{ promo.end_date|date:"d/m/Y à H:i" }}
    </p>
    <a href="#promotions" style="display: inline-block; margin-top: 20px; background: white; color: #E63946; padding: 12px 30px; border-radius: 5px; font-weight: bold; text-decoration: none;">
        Découvrir les offres →
    </a>
</div>
{% endfor %}

<!-- Section des produits en promotion -->
{% if active_promotions %}
<section id="promotions" style="margin: 50px 0;">
    <h2 style="text-align: center; font-size: 2em; color: #E63946; margin-bottom: 40px;">
        🎁 Produits en promotion
    </h2>
    
    <div class="products-grid">
        {% for product in products %}
            {% with pricing=product.get_pricing %}
                {% if pricing.has_promotion %}
                <!-- Afficher le produit en promo -->
                <div class="product-card">
                    <!-- ... code du produit ... -->
                </div>
                {% endif %}
            {% endwith %}
        {% endfor %}
    </div>
</section>
{% endif %}

<!-- Autres produits -->
<section style="margin: 50px 0;">
    <h2 style="text-align: center;">Tous nos produits</h2>
    <!-- Afficher tous les produits -->
</section>
{% endblock %}
```

---

## 4️⃣ API JSON pour appels asynchrones

Si vous avez besoin d'appels API:

```python
# promotions/views.py - Ajouter

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from products.models import Product
from .utils import calculate_product_price

@api_view(['GET'])
def api_product_pricing(request, product_id):
    """API pour récupérer le pricing d'un produit"""
    try:
        product = Product.objects.get(id=product_id)
        pricing = calculate_product_price(product)
        
        return Response({
            'status': 'success',
            'product_id': product_id,
            'original_price': float(pricing['original_price']),
            'discounted_price': float(pricing['discounted_price']),
            'discount_percent': float(pricing['discount_percent']),
            'has_promotion': pricing['has_promotion'],
            'badge_text': pricing['promotion'].get_badge_text() if pricing['promotion'] else None,
        })
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

# urls.py
path('api/product/<int:product_id>/pricing/', api_product_pricing, name='api_product_pricing'),
```

---

## 5️⃣ CSS pour les badges et prix réduits

Ajoutez à votre CSS global:

```css
/* Badge de promotion */
.promotion-badge {
    background-color: #E63946;
    color: white;
    padding: 6px 12px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 0.9em;
    display: inline-block;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Prix réduit */
.price-original {
    text-decoration: line-through;
    color: #999;
    font-size: 0.9em;
}

.price-current {
    color: #1A1A1A;
    font-weight: bold;
}

/* Bannière promo */
.promo-banner-hero {
    background: linear-gradient(135deg, #E63946 0%, #B1242F 100%);
    color: white;
    padding: 50px 30px;
    border-radius: 12px;
    box-shadow: 0 8px 25px rgba(230, 57, 70, 0.3);
    margin: 30px 0;
    text-align: center;
}

.promo-banner-hero h2 {
    font-size: 2.5em;
    margin: 0 0 20px 0;
}

.promo-banner-hero p {
    font-size: 1.1em;
    margin: 10px 0;
}
```

---

## 6️⃣ Cache pour optimiser les performances

Pour optimiser, implémentez un cache:

```python
# promotions/utils.py - Modifier calculate_product_price

from django.core.cache import cache

def calculate_product_price(product, base_price=None, at_datetime=None):
    """Avec cache"""
    # Générer la clé de cache
    cache_key = f"product_price_{product.id}"
    
    # Vérifier le cache
    cached_price = cache.get(cache_key)
    if cached_price:
        return cached_price
    
    # Calcul (code existant)
    pricing = { ... }
    
    # Mettre en cache pour 5 minutes
    cache.set(cache_key, pricing, 300)
    
    return pricing
```

---

## 7️⃣ Tests en local

Testez la promotion:

```python
# test_promotion.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from products.models import Product
from promotions.models import Promotion
from promotions.utils import calculate_product_price

class PromotionTestCase(TestCase):
    def test_promotion_pricing(self):
        # Créer un produit
        product = Product.objects.create(
            name="Test Product",
            selling_price=100.00
        )
        
        # Créer une promo
        promo = Promotion.objects.create(
            name="Test Promo",
            discount_type='percentage',
            discount_value=20,
            scope='all_products',
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            is_active=True
        )
        
        # Vérifier le prix réduit
        pricing = calculate_product_price(product)
        self.assertTrue(pricing['has_promotion'])
        self.assertEqual(pricing['discounted_price'], 80.00)
        self.assertEqual(pricing['discount_percent'], 20)
```

---

## 📌 Résumé d'intégration

✅ Ajouter méthode `get_pricing()` au modèle Product
✅ Afficher le badge dans les templates produits
✅ Afficher les bannières en page d'accueil
✅ Implémenter le cache pour les perfs
✅ Tester avec des promotions réelles
✅ Configurer Celery pour l'automatisation (optionnel)

---

**Besoin d'aide?** Consultez la documentation du modèle `Promotion` dans l'admin Django!
