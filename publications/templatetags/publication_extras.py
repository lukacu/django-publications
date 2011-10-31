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

