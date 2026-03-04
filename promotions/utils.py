"""
Utilitaires pour la gestion des promotions.
Contient la logique métier pour le calcul des prix et l'application des promos.
"""
from django.utils import timezone
from decimal import Decimal
from .models import Promotion


def get_active_promotions(product_id=None, at_datetime=None):
    """
    Récupère toutes les promotions actuellement actives.
    
    Args:
        product_id: ID du produit (optionnel) pour filtrer par produit
        at_datetime: DateTimeField pour vérifier à un instant spécifique
        
    Returns:
        QuerySet de Promotion actives
    """
    if at_datetime is None:
        at_datetime = timezone.now()
    
    promotions = Promotion.objects.filter(
        is_active=True,
        start_date__lte=at_datetime,
        end_date__gte=at_datetime
    )
    
    if product_id:
        # Filtrer par produit
        from django.db.models import Q
        promotions = promotions.filter(
            Q(scope='all_products') |
            (Q(scope='specific_products') & Q(products__id=product_id)) |
            (Q(scope='specific_categories') & Q(categories__products__id=product_id))
        ).distinct()
    
    return promotions


def calculate_product_price(product, base_price=None, at_datetime=None):
    """
    Calcule le prix final d'un produit en tenant compte des promotions actives.
    
    Args:
        product: Instance du modèle Product
        base_price: Prix de base (utilise product.selling_price si None)
        at_datetime: DateTimeField pour vérifier à un instant spécifique
        
    Returns:
        dict: {
            'original_price': Decimal,
            'discounted_price': Decimal,
            'discount_amount': Decimal,
            'discount_percent': Decimal,
            'has_promotion': bool,
            'promotion': Promotion ou None,
            'savings': str (pour affichage)
        }
    """
    if base_price is None:
        base_price = product.selling_price
    
    base_price = Decimal(str(base_price))
    
    # Récupérer les promotions actives pour ce produit
    promotions = get_active_promotions(product_id=product.id, at_datetime=at_datetime)
    
    if not promotions.exists():
        return {
            'original_price': base_price,
            'discounted_price': base_price,
            'discount_amount': Decimal('0.00'),
            'discount_percent': Decimal('0.00'),
            'has_promotion': False,
            'promotion': None,
            'savings': '$0.00',
        }
    
    # Utiliser la première (meilleure) promotion
    promotion = promotions.first()
    discounted_price = promotion.calculate_discounted_price(base_price)
    discount_amount = base_price - discounted_price
    
    # Calculer le pourcentage de réduction
    if base_price > 0:
        discount_percent = (discount_amount / base_price) * 100
    else:
        discount_percent = Decimal('0.00')
    
    return {
        'original_price': base_price,
        'discounted_price': discounted_price,
        'discount_amount': discount_amount,
        'discount_percent': discount_percent,
        'has_promotion': True,
        'promotion': promotion,
        'savings': f"{discount_amount:.2f}€",
    }


def update_promotion_status():
    """
    Met à jour le statut des promotions :
    - Active les promotions dont start_date est passée
    - Désactive les promotions dont end_date est passée
    - À utiliser dans un cron job ou scheduler
    """
    from .models import PromotionLog
    
    now = timezone.now()
    
    # Activer les promotions
    to_activate = Promotion.objects.filter(
        start_date__lte=now,
        end_date__gte=now,
        is_active=False
    )
    
    count_activated = 0
    for promo in to_activate:
        promo.is_active = True
        promo.save()
        
        PromotionLog.objects.create(
            promotion=promo,
            action='started',
            details={'auto_activated': True}
        )
        count_activated += 1
    
    # Désactiver les promotions expirées
    to_deactivate = Promotion.objects.filter(
        end_date__lt=now,
        is_active=True
    )
    
    count_deactivated = 0
    for promo in to_deactivate:
        promo.is_active = False
        promo.save()
        
        PromotionLog.objects.create(
            promotion=promo,
            action='ended',
            details={'auto_deactivated': True}
        )
        count_deactivated += 1
    
    return {
        'activated': count_activated,
        'deactivated': count_deactivated,
        'timestamp': now
    }


def get_promotion_stats(promotion):
    """
    Récupère les statistiques d'une promotion.
    
    Args:
        promotion: Instance de Promotion
        
    Returns:
        dict: Statistiques de la promotion
    """
    applicable_products = promotion.get_applicable_products()
    
    return {
        'promotion': promotion.name,
        'total_products': applicable_products.count(),
        'discount': f"{promotion.discount_value}{('%' if promotion.discount_type == 'percentage' else '€')}",
        'is_active': promotion.is_active,
        'status': promotion.status,
        'started': promotion.start_date,
        'ends': promotion.end_date,
        'time_remaining': (promotion.end_date - timezone.now()).total_seconds() if not promotion.is_expired else 0,
    }
