# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-
__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Luka Cehovin <luka.cehovin@gmail.com>'
__docformat__ = 'epytext'

from django.template import Library, Node, Context, RequestContext
from django.template.loader import get_template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.template import loader
from django import template
from publications.models import Publication
from re import sub

register = Library()

class RenderPublication(template.Node):
  def __init__(self, entry, templ = 'publication'):
    self.variable = template.Variable(entry)
    self.template = templ

  def render(self, context):
    try:
      entry = self.variable.resolve(context)
      ft = entry.type.pk
      tt = self.template
      try:
        return loader.render_to_string("publications/%s_%s.html" % (tt, ft), {'publication' : entry}, context)
      except loader.TemplateDoesNotExist:
        try:
          return loader.render_to_string("publications/%s.html" % tt, {'publication' : entry}, context)
        except loader.TemplateDoesNotExist:
          return loader.render_to_string("publications/publication.html", {'publication' : entry}, context)
    except template.VariableDoesNotExist:
      return ''

@register.tag
def render_publication(parser, token):
  try:
    tag_name, variable, templ = token.split_contents()
  except ValueError:
    raise template.TemplateSyntaxError, "%r tag requires two arguments argument" % token.contents.split()[0]

  return RenderPublication(variable, templ)

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

