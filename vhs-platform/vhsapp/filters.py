from django.template import Library

register = Library()


@register.filter
def range_filter(value):
    """
    Generate a range of numbers
    """
    return range(value)


@register.filter
def split(value, sep):
    """
    Split a string by a separator and return a list
    """
    return value.split(sep)


@register.filter
def replace_nth_part_of_url(url, args):
    """
    Replace a specific component of a URL string
    """
    new_part, n = args.split(";")
    n = int(n)
    parts = url.split("/")
    parts[n] = new_part
    return "/".join(parts)
