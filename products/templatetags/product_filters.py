from django import template

register = template.Library()

@register.filter
def equals(value, arg):
    """Check if value equals arg"""
    return value == arg
