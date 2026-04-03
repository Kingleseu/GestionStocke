from datetime import timedelta
from secrets import randbelow

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from .models import (
    ACCOUNT_SPACE_CUSTOMER,
    ACCOUNT_SPACE_STAFF,
    EmailOTP,
    OTP_PURPOSE_LOGIN,
)


STAFF_GROUP_NAMES = ('Manager', 'Cashier')


def build_unique_username(seed):
    base = slugify(seed or 'client').replace('-', '') or 'client'
    base = base[:24] or 'client'
    candidate = base
    counter = 1

    while User.objects.filter(username__iexact=candidate).exists():
        suffix = str(counter)
        candidate = f"{base[:max(1, 24 - len(suffix))]}{suffix}"
        counter += 1

    return candidate


def is_staff_account(user):
    return user.is_superuser or user.is_staff or user.groups.filter(name__in=STAFF_GROUP_NAMES).exists()


def account_space_for_user(user):
    return ACCOUNT_SPACE_STAFF if is_staff_account(user) else ACCOUNT_SPACE_CUSTOMER


def account_space_label(account_space):
    if account_space == ACCOUNT_SPACE_STAFF:
        return 'personnel boutique'
    return 'client boutique'


def role_label_for_user(user):
    if user.is_superuser:
        return 'Administrateur'
    if user.groups.filter(name='Manager').exists():
        return 'Manager'
    if user.groups.filter(name='Cashier').exists():
        return 'Caissier'
    return 'Client'


def mask_email(email):
    if not email or '@' not in email:
        return email

    local, domain = email.split('@', 1)
    if len(local) <= 2:
        local_masked = f"{local[0]}*" if local else '*'
    else:
        local_masked = f"{local[:2]}{'*' * max(2, len(local) - 2)}"
    return f'{local_masked}@{domain}'


def get_user_by_email_and_space(email, account_space):
    normalized_email = (email or '').strip().lower()
    if not normalized_email:
        return None

    queryset = User.objects.filter(email__iexact=normalized_email).order_by('id')

    if account_space == ACCOUNT_SPACE_STAFF:
        queryset = queryset.filter(
            Q(is_superuser=True) | Q(is_staff=True) | Q(groups__name__in=STAFF_GROUP_NAMES)
        ).distinct()
    else:
        queryset = queryset.exclude(is_superuser=True).exclude(is_staff=True).exclude(
            groups__name__in=STAFF_GROUP_NAMES
        ).distinct()

    return queryset.first()


def roles_for_user(user):
    roles = []
    if user.is_superuser:
        roles.append('Admin')
    if user.groups.filter(name='Manager').exists():
        roles.append('Manager')
    if user.groups.filter(name='Cashier').exists():
        roles.append('Caissier')
    if not roles:
        roles.append('Client')
    return roles


def _default_from_email():
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@mkaribu.local')


def send_staff_invitation_email(invitation, invite_url, shop_name):
    context = {
        'invite_url': invite_url,
        'shop_name': shop_name,
        'role_label': invitation.get_role_display(),
        'first_name': invitation.first_name,
        'last_name': invitation.last_name,
        'expires_at': timezone.localtime(invitation.expires_at).strftime('%d/%m/%Y %H:%M'),
    }
    message = render_to_string('accounts/emails/staff_invitation_email.txt', context)
    send_mail(
        subject=f"Invitation MKARIBU - {invitation.get_role_display()}",
        message=message,
        from_email=_default_from_email(),
        recipient_list=[invitation.email],
        fail_silently=False,
    )
