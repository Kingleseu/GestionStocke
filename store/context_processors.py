from django.db.utils import OperationalError, ProgrammingError
from django.templatetags.static import static

from accounts.decorators import is_manager
from accounts.models import Shop

from .models import AdminNotification


def _fallback_shop_logo_context():
    return {
        'active_shop': None,
        'shop_logo_url': static('img/mkaribu_logo.png'),
        'shop_logo_alt': 'MKARIBU',
    }


def shop_branding(request):
    context = _fallback_shop_logo_context()

    try:
        shop = None
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
            except Exception:
                profile = None

            if profile and profile.shop_id:
                shop = profile.shop

        if shop is None:
            shop = Shop.objects.order_by('id').first()

        if shop:
            context['active_shop'] = shop
            context['shop_logo_alt'] = shop.name or context['shop_logo_alt']
            if shop.logo:
                context['shop_logo_url'] = shop.logo.url
    except (OperationalError, ProgrammingError):
        pass

    return context


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
