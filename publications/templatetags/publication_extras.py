__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.template import Library, Node, Context
from django.template.loader import get_template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from publications.models import Publication
from re import sub

register = Library()

def get_publication(id):
	pbl = Publication.objects.filter(pk=int(id))

	if len(pbl) < 1:
		return ''
	return get_template('publications/publication.html').render(
		Context({'publication': pbl[0]}))

register.simple_tag(get_publication)

# Returns bibtex for one or more publications
def to_bibtex(publications):

	from publications.bibtex import BibTeXFormatter
	from publications.transcode import unicode_to_ascii
	bibtex_keys = set()

	import collections

	if not isinstance(publications, collections.Iterable):
		publications = [publications]

	formatter = BibTeXFormatter()
	output = []

	for publication in publications:
		entry = publication.to_dictionary()
		entry["@type"] = publication.type

		first_author = publication.first_author()
		if first_author:
			author_identifier = first_author.identifier()
		else:
			author_identifier = "UNCREDITED"
		key_base = unicode_to_ascii(author_identifier).replace("?", "_") + str(publication.year)

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

