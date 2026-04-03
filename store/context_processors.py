from django.db.utils import OperationalError, ProgrammingError

from accounts.decorators import is_manager

from .models import AdminNotification


def order_notifications(request):
    if not request.user.is_authenticated or not is_manager(request.user):
        return {
            'notifications_enabled': False,
            'notification_items': [],
            'notification_unread_count': 0,
        }

    try:
        base_queryset = AdminNotification.objects.filter(recipient=request.user)
        notification_items = list(
            base_queryset.select_related('order').order_by('-created_at')[:8]
        )
        unread_count = base_queryset.filter(is_read=False).count()
    except (OperationalError, ProgrammingError):
        notification_items = []
        unread_count = 0

    return {
        'notifications_enabled': True,
        'notification_items': notification_items,
        'notification_unread_count': unread_count,
    }
