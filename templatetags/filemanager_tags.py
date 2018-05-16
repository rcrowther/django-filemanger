from django import template

register = template.Library()

from filemanager.db import DB
from django.conf import settings
from django.templatetags import static
from django.utils.safestring import mark_safe

#? cache the DB? And/or collection?

@register.tag('bucketdb_static')
def do_static(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
         tag_name, path_str = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a 'path' argument" % token.contents.split()[0]
        )
    if not (path_str[0] == path_str[-1] and path_str[0] in ('"', "'")):
          raise template.TemplateSyntaxError(
              "%r tag's 'path' argument should be in quotes" % tag_name
          )
    token.contents = "{} {}".format(tag_name, path_str)
    return static.do_static(parser, token)
    
@register.tag('bucketdb_collection_static')
def do_static(parser, token):
    db = DB(settings.UPLOAD_ROOT)
    try:
        # split_contents() knows not to split quoted strings.
         tag_name, coll_str, id_str = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a 'collection' then 'id' argument" % token.contents.split()[0]
        )
    if not (coll_str[0] == coll_str[-1] and coll_str[0] in ('"', "'")):
          raise template.TemplateSyntaxError(
              "%r tag's 'coll' argument should be in quotes" % tag_name
          )
    coll = db(coll_str[1:-1])
    try:
        id = int(id_str)
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag's 'id' argument will not convert to int" % token.contents.split()[0]
        )
    path = coll.document_relpath(id)
    token.contents = "{} '{}'".format(tag_name, path)
    return static.do_static(parser, token)
