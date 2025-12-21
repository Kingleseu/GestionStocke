from django import template
from products.models import Category

register = template.Library()


@register.simple_tag
def get_active_categories():
    """
    Returns active categories if the field exists, otherwise all categories.
    Keeps dropdowns/filters populated even if view context is missing categories.
    """
    qs = Category.objects.all()
    if hasattr(Category, 'is_active'):
        qs = qs.filter(is_active=True)
    return qs
@register.filter
def split(value, arg):
    """Splits a string by a given separator"""
    return value.split(arg)
