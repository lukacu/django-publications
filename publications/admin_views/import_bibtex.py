__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from publications.bibtex import BibTeXParser, BibTeXProcessor
from publications.models import Publication
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

def generate_objects(bibliography, update=False):

	publications = []
	for entry in bibliography:
		# add missing keys
		keys = ['journal',
			'booktitle',
			'publisher',
			'url',
			'doi',
			'keywords',
			'note',
			'month',
			'abstract',
			'groups']

		for key in keys:
			if not entry.has_key(key):
				entry[key] = ''

		# map integer fields to integers
		entry['month'] = MONTHS.get(entry['month'].lower(), 0)
		entry['volume'] = entry.get('volume', None)
		entry['number'] = entry.get('number', None)

		publication = Publication(
			type=entry['@type'],
			title=entry['title'],
			year=entry['year'],
			month=entry['month'],
			journal=entry['journal'],
			book_title=entry['booktitle'],
			publisher=entry['publisher'],
			volume=entry['volume'],
			number=entry['number'],
			note=entry['note'],
			abstract=entry['abstract'],
			url=entry['url'],
			doi=entry['doi'],
			keywords=entry['keywords'])

		people = []

		if entry.has_key("author"):
			people.extend([("author", name) for name in entry["author"].split(" and ")])

		if entry.has_key("editor"):
			people.extend([("editor", name) for name in entry["editor"].split(" and ")])

		if len(people) > 0:
			publication.set_people = people

		if "," in entry["groups"]:
			publication.set_groups = [g.strip() for g in entry.get('groups', "").split(",")]
		else:
			publication.set_groups = [g.strip() for g in entry.get('groups', "").split(" ")]

		# add publication
		publications.append(publication)

	return publications

def import_bibtex(request):
	if request.method == 'POST':
		# container for error messages
		errors = list()

		# check for errors
		if not request.POST['bibliography']:
			errors.append('This field is required.')

		bibliography = list()
		if not errors:
			parser = BibTeXParser()
			entries = parser.parse(request.POST['bibliography'])
			if entries == None:
				for error in parser.getErrors():
					errors.append("%s (line: %d, column %d)" % (error["message"], error["line"], error["column"]))
			processor = BibTeXProcessor()
			for entry in entries:
				processed_entry = processor.process(entry)
				if processed_entry == None:
					for error in processor.getErrors():
						errors.append("%s (line: %d, column %d)" % (error["message"], error["line"], error["column"]))
					continue
				processed_entry["type"] = entry["type"]
				bibliography.append(processed_entry)

		if not errors:
			try:
				publications = generate_objects(bibliography)
			except e:
				errors.append(str(e))

		if not errors and not publications:
			errors.append('No valid BibTex entries found.')

		if errors:
			# some error occurred
			errors = {"bibliography" : errors}
			return render_to_response(
				'admin/publications/import_bibtex.html', {
					'errors': errors,
					'title': 'Import BibTex',
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
				'request': request},
			RequestContext(request))

import_bibtex = staff_member_required(import_bibtex)
