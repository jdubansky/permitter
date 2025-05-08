from django import template
import json

register = template.Library()

@register.filter
def json_length(value):
    if value is None:
        return 0
    return len(json.dumps(value)) 