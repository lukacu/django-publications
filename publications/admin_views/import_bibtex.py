__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from publications.bibtex import BibTeXParser, BibTeXProcessor
from publications.models import Publication, Type
from string import split, join

# mapping of months
MONTHS = {
	'jan': 1, 'january': 1,
	'feb': 2, 'february': 2,
	'mar': 3, 'march': 3,
	'apr': 4, 'april': 4,
	'may': 5,
	'jun': 6, 'june': 6,
	'jul': 7, 'july': 7,
	'aug': 8, 'august': 8,
	'sep': 9, 'september': 9,
	'oct': 10, 'october': 10,
	'nov': 11, 'november': 11,
	'dec': 12, 'december': 12}

def import_bibtex(request):
	if request.method == 'POST':
		# container for error messages
		errors = list()

		# publication types
		types = Type.objects.all()

		# check for errors
		if not request.POST['bibliography']:
			errors.append('This field is required.')

		if not errors:
			parser = BibTeXParser()
			entries = parser.parse(request.POST['bibliography'])
			if entries == None:
				for error in parser.getErrors():
					errors.append("%s (line: %d, column %d)" % (error["message"], error["line"], error["column"]))
			bib = list()
			processor = BibTeXProcessor()
			for entry in entries:
				processed_entry = processor.process(entry)
				if processed_entry == None:
					for error in processor.getErrors():
						errors.append("%s (line: %d, column %d)" % (error["message"], error["line"], error["column"]))
					continue
				processed_entry["type"] = entry["type"]
				bib.append(processed_entry)

		if not errors:

			publications = []
			# try adding publications
			for entry in bib:
				print entry
				if entry.has_key('title') and \
				   entry.has_key('author') and \
				   entry.has_key('year'):
					# parse authors
					authors = split(entry['author'], ' and ')
					for i in range(len(authors)):
						author = split(authors[i], ',')
						author = [author[-1]] + author[:-1]
						authors[i] = join(author, ' ')
					authors = join(authors, ', ')

					# add missing keys
					keys = [
						'journal',
						'booktitle',
						'publisher',
						'url',
						'doi',
						'keywords',
						'note',
						'month']

					for key in keys:
						if not entry.has_key(key):
							entry[key] = ''

					# map integer fields to integers
					entry['month'] = MONTHS.get(entry['month'].lower(), 0)
					entry['volume'] = entry.get('volume', None)
					entry['number'] = entry.get('number', None)

					# determine type
					type_id = None

					for t in types:
						if entry['type'] in t.bibtex_type_list:
							type_id = t.id
							break

					if type_id is None:
						errors.append('Type "' + entry['type'] + '" unknown.')
						break

					# add publication
					publications.append(Publication(
						type_id=type_id,
						title=entry['title'],
						authors=authors,
						year=entry['year'],
						month=entry['month'],
						journal=entry['journal'],
						book_title=entry['booktitle'],
						publisher=entry['publisher'],
						volume=entry['volume'],
						number=entry['number'],
						note=entry['note'],
						url=entry['url'],
						doi=entry['doi'],
						keywords=entry['keywords']))
				else:
					errors.append('Make sure that the keys title, author and year are present.')
					break

		if not errors and not publications:
			errors.append('No valid BibTex entries found.')

		if errors:
			# some error occurred
			errors = {"bibliography" : errors}
			return render_to_response(
				'admin/publications/import_bibtex.html', {
					'errors': errors,
					'title': 'Import BibTex',
					'types': Type.objects.all(),
					'request': request},
				RequestContext(request))
		else:
			try:
				# save publications
				for publication in publications:
					publication.save()
			except:
				msg = 'Some error occured during saving of publications.'
			else:
				if len(publications) > 1:
					msg = 'Successfully added ' + str(len(publications)) + ' publications.'
				else:
					msg = 'Successfully added ' + str(len(publications)) + ' publication.'

			# show message
			messages.info(request, msg)

			# redirect to publication listing
			return HttpResponseRedirect('../')
	else:
		return render_to_response(
			'admin/publications/import_bibtex.html', {
				'title': 'Import BibTex',
				'types': Type.objects.all(),
				'request': request},
			RequestContext(request))

import_bibtex = staff_member_required(import_bibtex)
