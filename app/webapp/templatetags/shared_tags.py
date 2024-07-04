import json

from django import template
import pprint

from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.filter("field_type")
def field_type(obj):
    return obj.field.widget.__class__.__name__


@register.simple_tag
def define(val=None):
    return val


@register.simple_tag
def is_superuser(user):
    return user.is_superuser


@register.filter
def add_str(arg1, arg2):
    return str(arg1) + str(arg2)


@register.filter
def model_name(obj):
    return obj.__class__.__name__


@register.filter
def dump(obj):
    return mark_safe(f"<pre>{escape(pprint.pformat(vars(obj), indent=4))}</pre>")


@register.filter
def add_class(field, class_name):
    return field.as_widget(attrs={"class": class_name})


@register.filter
def js(obj):
    return json.dumps(obj)


@register.simple_tag
def check_url(*args, **kwargs):
    try:
        return reverse(*args, **kwargs)
    except NoReverseMatch:
        return ""
