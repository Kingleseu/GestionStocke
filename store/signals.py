from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AdminNotification, WebOrder


def _get_order_notification_recipients():
    user_model = get_user_model()
    return user_model.objects.filter(
        Q(is_superuser=True) | Q(groups__name='Manager'),
        is_active=True,
    ).distinct()


@receiver(post_save, sender=WebOrder)
def create_new_order_notifications(sender, instance, created, **kwargs):
    if not created:
        return

    customer_name = instance.full_name.strip() if instance.full_name else "Client inconnu"
    notifications = [
        AdminNotification(
            recipient=recipient,
            order=instance,
            notification_type='new_order',
            title="Nouvelle commande reçue",
            message=f"Commande #{instance.id} reçue de {customer_name}. Ouvrez le détail pour la traiter.",
        )
        for recipient in _get_order_notification_recipients()
    ]

    if notifications:
        AdminNotification.objects.bulk_create(notifications)
