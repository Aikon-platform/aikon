from django import template
from django.contrib.auth.models import User

register = template.Library()


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
