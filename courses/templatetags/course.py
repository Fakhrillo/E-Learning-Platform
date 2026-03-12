from django import template

register = template.Library()

@register.filter
def model_name(obj):
    try:
        return obj.__class__.__name__.lower()
    except AttributeError:
        return None