"""
Celery Tasks pour les promotions.
Configure l'automatisation du statut des promotions.
"""
from celery import shared_task
from django.utils import timezone
from .models import Promotion, PromotionLog
from .utils import update_promotion_status


@shared_task
def sync_promotion_status():
    """
    Task Celery pour synchroniser le statut des promotions toutes les 5 minutes.
    Activation/désactivation automatique basées sur start/end dates.
    """
    try:
        stats = update_promotion_status()
        return f"Promotion status synced: {stats['activated']} activated, {stats['deactivated']} deactivated"
    except Exception as e:
        return f"Error syncing promotion status: {str(e)}"


@shared_task
def log_promotion_activity():
    """
    Task Celery pour générer un rapport d'activité des promotions.
    """
    try:
        now = timezone.now()
        active_promos = Promotion.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).count()
        
        return f"Currently {active_promos} active promotion(s)"
    except Exception as e:
        return f"Error logging promotion activity: {str(e)}"


@shared_task
def notify_promotion_ending():
    """
    Task Celery pour envoyer des notifications de fin de promotion.
    À utiliser si vous avez un système d'emails configuré.
    """
    try:
        now = timezone.now()
        # Promos finissant dans 24h
        from datetime import timedelta
        soon = now + timedelta(hours=24)
        
        ending_promos = Promotion.objects.filter(
            is_active=True,
            end_date__lte=soon,
            end_date__gt=now
        )
        
        # Vous pourriez envoyer un email ici
        count = ending_promos.count()
        return f"Found {count} promotion(s) ending soon"
    except Exception as e:
        return f"Error notifying promotion ending: {str(e)}"


# Vous devez ajouter ces tasks dans un fichier de configuration (ex: celerybeat.py ou settings.py)
# CELERY_BEAT_SCHEDULE = {
#     'sync-promotions-every-5-min': {
#         'task': 'promotions.tasks.sync_promotion_status',
#         'schedule': crontab(minute='*/5'),
#     },
# }
