import json

from django import template
import pprint

from django.forms import BoundField
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.urls import NoReverseMatch, reverse
from django.forms.widgets import Select


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
def add_class(element, class_name):
    # if isinstance(element, BoundField):
    #     print("prout")
    #     element = element.field

    if hasattr(element, "field"):
        # For form fields
        css_classes = element.field.widget.attrs.get("class", "")
        classes = f"{css_classes} {class_name}".strip()
        return element.as_widget(attrs={"class": classes})
    else:
        # For SafeString objects (already rendered HTML)
        classes = element.split('class="')
        if len(classes) > 1:
            existing_classes = classes[1].split('"')[0]
            new_classes = f"{existing_classes} {class_name}".strip()
            return mark_safe(
                element.replace(f'class="{existing_classes}"', f'class="{new_classes}"')
            )
        return mark_safe(element.replace(">", f' class="{class_name}">', 1))


@register.filter
def is_select(field):
    return isinstance(field.field.widget, Select)


@register.filter
def js(obj):
    return json.dumps(obj)


@register.simple_tag
def check_url(*args, **kwargs):
    try:
        return reverse(*args, **kwargs)
    except NoReverseMatch:
        return ""
