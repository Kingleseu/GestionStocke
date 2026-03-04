"""
Signaux Django pour les promotions.
Utilisés pour tracker automatiquement les changements et mettre à jour les logs.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Promotion, PromotionLog


@receiver(post_save, sender=Promotion)
def log_promotion_changes(sender, instance, created, **kwargs):
    """
    Signal pour logger all les changements de promotion.
    """
    try:
        if created:
            # Nouvelle promotion créée
            PromotionLog.objects.create(
                promotion=instance,
                action='created',
                performed_by=getattr(instance, '_created_by', None),
                details={
                    'name': instance.name,
                    'discount': f"{instance.discount_value}{('%' if instance.discount_type == 'percentage' else '€')}",
                    'start_date': instance.start_date.isoformat(),
                    'end_date': instance.end_date.isoformat(),
                }
            )
        else:
            # Promotion modifiée
            PromotionLog.objects.create(
                promotion=instance,
                action='updated',
                performed_by=getattr(instance, '_updated_by', None),
                details={
                    'fields_updated': ['name', 'description', 'discount_type', 'discount_value'],
                    'is_active': instance.is_active,
                }
            )
    except Exception as e:
        print(f"Error logging promotion changes: {e}")


@receiver(post_delete, sender=Promotion)
def log_promotion_deletion(sender, instance, **kwargs):
    """
    Signal pour logger la suppression d'une promotion.
    """
    try:
        PromotionLog.objects.create(
            promotion_id=instance.id,
            action='deleted',
            details={
                'name': instance.name,
                'discount': f"{instance.discount_value}{('%' if instance.discount_type == 'percentage' else '€')}",
            }
        )
    except Exception as e:
        print(f"Error logging promotion deletion: {e}")
