from django import template
from django.contrib.auth.models import User
from django.utils.html import escape
from django.utils.safestring import mark_safe

from app.webapp.utils.logger import pprint
import pprint

register = template.Library()


@register.simple_tag(takes_context=True)
def dump(context):
    return mark_safe(f"<pre>{escape(pprint.pformat(vars(context), indent=4))}</pre>")
    # return f'<pre>{pprint(context.flatten())}</pre>'


@register.simple_tag
def define(val=None):
    return val


@register.simple_tag
def is_superuser(user):
    if isinstance(user, User):
        return user.is_superuser
    elif isinstance(user, str):
        try:
            user_obj = User.objects.get(username=user)
            return user_obj.is_superuser
        except User.DoesNotExist:
            return False
    return False


@register.filter
def field_type(obj):
    return obj.field.widget.__class__.__name__


@register.filter
def field_classes(obj):
    classes = obj.field.widget.attrs.get("extra-class", "")
    if type(classes) is list:
        return " ".join(classes)
    return classes


@register.filter
def add_class(element, class_name):
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
    # return field.as_widget(attrs=attrs)


@register.filter
def add_str(arg1, arg2):
    return str(arg1) + str(arg2)


def val_to_list(value):
    if isinstance(value, int):
        return [value]
    if isinstance(value, str):
        return value.split(",") if "," in value else [value]
    if isinstance(value, dict):
        value = value.keys()
    return list(value)


@register.filter
def startswith(text, starts):
    if not isinstance(text, str):
        return False

    starts = val_to_list(starts)
    for start in starts:
        if text.startswith(str(start)):
            return True
    return False


@register.filter
def contains(text, needles):
    if not isinstance(text, str):
        return False

    needles = val_to_list(needles)
    for needle in needles:
        if str(needle) in text:
            return True
    return False


@register.filter
def add_to_list(value, arg):
    return val_to_list(value) + val_to_list(arg)


@register.filter
def remove_from_list(value, arg):
    return [v for v in val_to_list(value) if v not in val_to_list(arg)]
