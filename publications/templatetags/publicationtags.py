# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-
__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Luka Cehovin <luka.cehovin@gmail.com>'
__docformat__ = 'epytext'

import urlparse
from django.template.defaulttags import URLNode, url
from django.contrib.sites.models import Site
from django.conf import settings
from django.template import Library, Node, Context, RequestContext
from django.template.loader import get_template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.template import loader
from django import template
from django.core.exceptions import ObjectDoesNotExist
from publications.models import Publication, Group

register = Library()

class UrlNode(template.Node):
  def __init__(self, path=None):
    self.variable = template.Variable(path)

  def render(self, context):
    try:
      path = self.variable.resolve(context)
    except template.VariableDoesNotExist:
      return ''
    protocol = getattr(settings, "PROTOCOL", "http")
    domain = Site.objects.get_current().domain
    port = getattr(settings, "PORT", "")
    if port:
        assert port.startswith(":"), "The PORT setting must have a preceeding ':'."
    return "%s://%s%s%s" % (protocol, domain, port, path)

@register.tag
def absolute_url(parser, token):
  path = None
  bits = token.split_contents()
  if len(bits) >= 2:
    path = bits[1]
  return UrlNode(path)

class RenderPublicationInline(template.Node):
  def __init__(self, entry, templ = 'publication'):
    self.variable = template.Variable(entry)
    self.template = templ

  def render(self, context):
    try:
      entry = self.variable.resolve(context)
      ft = entry.type.identifier
      tt = self.template
      try:
        return loader.render_to_string("publications/inline_%s_%s.html" % (tt, ft), {'publication' : entry}, context)
      except loader.TemplateDoesNotExist:
        try:
          return loader.render_to_string("publications/inline_%s.html" % tt, {'publication' : entry}, context)
        except loader.TemplateDoesNotExist:
          return loader.render_to_string("publications/inline.html", {'publication' : entry}, context)
    except template.VariableDoesNotExist:
      return ''

@register.tag
def publication_inline(parser, token):
  try:
    tag_name, variable, templ = token.split_contents()
    return RenderPublicationInline(variable, templ)
  except ValueError:
    try:
      tag_name, variable = token.split_contents()
      return RenderPublicationInline(variable)
    except ValueError:
      raise template.TemplateSyntaxError, "%r tag requires at least one argument argument" % token.contents.split()[0]

class RenderRecentPublicationsInline(template.Node):
  def __init__(self, group = None, count = 10):
    self.group = group
    self.count = count

  def render(self, context):
    try:
      group = None
      if self.group:
        try:
          group = template.Variable(self.group).resolve(context)
          group = Group.objects.get(identifier__iexact=group)
        except ObjectDoesNotExist:
          return ""

      candidates = Publication.objects.filter(public=True).order_by('-year', '-month', '-id')

      if group:
        candidates = candidates.filter(groups=group)

      return loader.render_to_string("publications/list_inline.html", {'publications' : candidates[0:self.count]}, context)
    except template.VariableDoesNotExist:
      return ''

@register.tag
def recent_publications(parser, token):
  try:
    tag_name, group, count = token.split_contents()
    return RenderRecentPublicationsInline(group, count)
  except ValueError:
    try:
      tag_name, group = token.split_contents()
      return RenderRecentPublicationsInline(group)
    except ValueError:
      return RenderRecentPublicationsInline()

# Returns bibtex for one or more publications
def to_bibtex(publications):

  from publications.bibtex import BibTeXFormatter
  bibtex_keys = set()

  import collections

  if not isinstance(publications, collections.Iterable):
    publications = [publications]

  formatter = BibTeXFormatter()
  output = []

  for publication in publications:
    if not publication.type.bibtex_type:
      continue

    entry = publication.to_dictionary()
    entry["@type"] = publication.type.bibtex_type

    first_author = publication.first_author()
    if first_author:
      author_identifier = first_author.identifier()
    else:
      author_identifier = "UNCREDITED"
    key_base = author_identifier + str(publication.year)

    char = ord('a')
    bibtex_key = key_base + chr(char)
    while bibtex_key in bibtex_keys:
      char = char + 1
      bibtex_key = key_base + chr(char)

    bibtex_keys.add(bibtex_key)
    entry["@key"] = bibtex_key

    output.append(formatter.format(entry))

  return "\n".join(output)

register.simple_tag(to_bibtex)

