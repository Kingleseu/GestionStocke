from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from accounts.models import Shop

from .models import FooterConfig


def build_store_absolute_uri(request, path):
    public_app_url = getattr(settings, 'PUBLIC_APP_URL', '')
    if public_app_url:
        return urljoin(f'{public_app_url}/', path.lstrip('/'))
    return request.build_absolute_uri(path)


def get_store_branding():
    shop = Shop.objects.order_by('id').first()
    footer = FooterConfig.objects.order_by('id').first()
    return {
        'shop_name': shop.name if shop else 'Votre boutique',
        'shop_address': shop.address if shop and shop.address else '',
        'shop_phone': shop.phone if shop and shop.phone else (footer.phone if footer else ''),
        'shop_email': shop.email if shop and shop.email else (footer.email if footer else ''),
    }


def send_order_confirmation_email(order, request):
    if not order.email:
        return False

    order_url = build_store_absolute_uri(request, order.get_customer_order_url())
    context = {
        'order': order,
        'order_url': order_url,
        'branding': get_store_branding(),
    }

    subject = f"Commande {order.tracking_reference} - confirmation"
    text_body = render_to_string('store/emails/order_confirmation.txt', context)
    html_body = render_to_string('store/emails/order_confirmation.html', context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )
    email.attach_alternative(html_body, 'text/html')
    email.send(fail_silently=False)
    return True
