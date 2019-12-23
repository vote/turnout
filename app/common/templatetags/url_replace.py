# from urllib import urlencode
from django import template

# pylint: disable=invalid-name
register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """Templatetag to handle GET arguments on links"""
    query = context["request"].GET.dict()
    query.update(kwargs)
    return "hy"
    # return urlencode(query)
