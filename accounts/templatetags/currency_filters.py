from django import template
from django.conf import settings

register = template.Library()

@register.filter(name='currency')
def currency(value, user=None):
    """
    Formate un montant selon la devise de l'utilisateur
    Usage: {{ amount|currency:request.user }}
    """
    try:
        amount = float(value)
    except (ValueError, TypeError):
        return value
    
    # Récupérer la devise de l'utilisateur
    currency_code = settings.DEFAULT_CURRENCY
    if user and hasattr(user, 'profile'):
        currency_code = user.profile.currency
    elif user and hasattr(user, 'is_authenticated') and user.is_authenticated:
        # Créer le profil s'il n'existe pas
        from accounts.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        currency_code = profile.currency
    
    # Récupérer les informations de la devise
    currency_info = settings.CURRENCIES.get(currency_code, settings.CURRENCIES.get('CDF', {'symbol': 'FC'}))
    symbol = currency_info['symbol']
    
    # Formater selon la devise
    if currency_code == 'USD':
        # Format: $1,234.56
        formatted = f"{symbol}{amount:,.2f}"
    else:
        # Format: 1 234,56 FC (Standard CDF format)
        # Using space as thousand separator and comma as decimal separator
        formatted = f"{amount:,.2f} {symbol}"
        # We can fine-tune the format if requested, but standard Python format for now
        # Actually, let's make it look like 1 234.56 FC or similar
        formatted = f"{amount:,.2f} {symbol}".replace(',', ' ')
    
    return formatted


@register.simple_tag(takes_context=True)
def get_currency_symbol(context):
    """
    Retourne le symbole de la devise de l'utilisateur
    Usage: {% get_currency_symbol %}
    """
    user = context.get('user')
    currency_code = settings.DEFAULT_CURRENCY
    
    if user and hasattr(user, 'profile'):
        currency_code = user.profile.currency
    elif user and hasattr(user, 'is_authenticated') and user.is_authenticated:
        from accounts.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        currency_code = profile.currency
    
    currency_info = settings.CURRENCIES.get(currency_code, settings.CURRENCIES[settings.DEFAULT_CURRENCY])
    return currency_info['symbol']
