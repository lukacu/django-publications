__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.db import models
from django.utils.http import urlquote_plus
from string import split, strip, join, replace, ascii_uppercase
from publications.fields import PagesField
from publications.models import Group, Person
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from publications.bibtex import BIBTEX_TYPES
from publications.models import parse_person_name

TYPE_CHOICES = []

for k, v in BIBTEX_TYPES.items():
	TYPE_CHOICES.append((k, v["name"]))

# names shown in admin area
MONTH_CHOICES = (
		(1, 'January'),
		(2, 'February'),
		(3, 'March'),
		(4, 'April'),
		(5, 'May'),
		(6, 'June'),
		(7, 'July'),
		(8, 'August'),
		(9, 'September'),
		(10, 'October'),
		(11, 'November'),
		(12, 'December')
	)

# abbreviations used in BibTex
MONTH_BIBTEX = {
		1: 'Jan',
		2: 'Feb',
		3: 'Mar',
		4: 'Apr',
		5: 'May',
		6: 'Jun',
		7: 'Jul',
		8: 'Aug',
		9: 'Sep',
		10: 'Oct',
		11: 'Nov',
		12: 'Dec'
	}


ROLE_CHOICES = (
		('author', 'Author'),
		('editor', 'Editor')
	)

class Role(models.Model):
	class Meta:
		ordering = ["role", "sequence"]
		app_label = 'publications'

	person = models.ForeignKey("Person")
	publication = models.ForeignKey("Publication")
	role = models.CharField(_('role'), choices=ROLE_CHOICES, max_length=16)
	sequence = models.IntegerField(blank=True, null=True)


class Publication(models.Model):
	class Meta:
		app_label = 'publications'
		ordering = ['-year', '-month', '-id']

	type = models.CharField(max_length=64, choices=TYPE_CHOICES)
	title = models.CharField(max_length=512)
	people = models.ManyToManyField("Person", through='Role')
	year = models.PositiveIntegerField(max_length=4)
	month = models.IntegerField(choices=MONTH_CHOICES, blank=True, null=True)
	journal = models.CharField(max_length=256, blank=True)
	book_title = models.CharField(max_length=256, blank=True)
	publisher = models.CharField(max_length=256, blank=True)
	volume = models.CharField(max_length=32,blank=True, null=True)
	number = models.CharField(max_length=32,blank=True, null=True, verbose_name='Issue number')
	pages = PagesField(max_length=32, blank=True)
	note = models.CharField(max_length=256, blank=True)
	keywords = models.CharField(max_length=1024, blank=True,
		help_text='List of keywords separated by commas.')
	url = models.URLField(blank=True, verify_exists=False, verbose_name='URL',
		help_text='Link to PDF or journal page.')
	code = models.URLField(blank=True, verify_exists=False,
		help_text='Link to page with code.')
	pdf = models.FileField(upload_to='publications/', verbose_name='PDF', blank=True, null=True)
	doi = models.CharField(max_length=128, verbose_name='DOI', blank=True)
	abstract = models.TextField("Abstract", blank=True)
	public = models.BooleanField(
		help_text='To hide a publication remove this flag.', default=True)
	groups = models.ManyToManyField(Group)


	def __init__(self, *args, **kwargs):
		models.Model.__init__(self, *args, **kwargs)

		# post-process keywords
		self.keywords = replace(self.keywords, ';', ',')
		self.keywords = replace(self.keywords, ', and ', ', ')
		self.keywords = replace(self.keywords, ',and ', ', ')
		self.keywords = replace(self.keywords, ' and ', ', ')
		self.keywords = [strip(s).lower() for s in split(self.keywords, ',')]
		self.keywords = join(self.keywords, ', ').lower()



	def save(self, *args, **kwargs):

		super(Publication, self).save(*args, **kwargs)

		if hasattr(self, "set_people"):
			i = 0
			Role.objects.filter(publication = self).delete()
			for person in self.set_people:
				name = person[1].strip()
				role = person[0].strip().lower()
				if name == "":
					continue
				if not role in [ r[0] for r in ROLE_CHOICES]:
					continue
				person = parse_person_name(name)
				if not person:
					continue
				i = i + 1
				r = Role(person = person, publication = self, role=role, sequence = i)
				r.save()

		if hasattr(self, "set_groups"):
			self.groups.clear()
			for group in self.set_groups:
				group = group.strip().lower()
				if group == "":
					continue
				try:
					g = Group.objects.get(name__iexact = group)
				except ObjectDoesNotExist:
					g = Group(name=group)
					g.save()
				self.groups.add(g)

	def __unicode__(self):
		if len(self.title) < 64:
			return self.title
		else:
			index = self.title.rfind(' ', 40, 62)

			if index < 0:
				return self.title[:61] + '...'
			else:
				return self.title[:index] + '...'


	def keywords_escaped(self):
		return [(strip(keyword), urlquote_plus(strip(keyword)))
			for keyword in split(self.keywords, ',')]

	def month_bibtex(self):
		return MONTH_BIBTEX.get(self.month, '')

	def first_author(self):
		people = Role.objects.filter(publication=self).order_by("role", "sequence")
		try:
			return people[0].person
		except IndexError:
			return None

	def journal_or_book_title(self):
		if self.journal:
			return self.journal
		else:
			return self.book_title

	def primary_authors(self):
		people = Role.objects.filter(publication = self).order_by("role", "sequence")
		authors = []
		role = None
		for a in people:
			if a.role == role or not role:
				authors.append(a.person)
				role = a.role
			else:
				break
		return authors

	def to_dictionary(self):
		entry = {}
		entry["title"] = self.title
		entry["author"] = " and ".join([ p.person.display for p in Role.objects.filter(role="author", publication = self).order_by("sequence") ])
		entry["year"] = self.year

		if self.journal:
			entry["journal"] = self.journal
		if self.book_title:
			entry["booktitle"] = self.book_title
		if self.publisher:
			entry["publisher"] = self.publisher
		if self.volume:
			entry["volume"] = self.volume
		if self.number:
			entry["number"] = self.number
		if self.pages:
			entry["pages"] = self.pages
		if self.month:
			entry["month"] = self.month_bibtex()
		if self.keywords:
			entry["keywords"] = self.keywords
		if self.doi:
			entry["doi"] = self.doi
		if self.url:
			entry["url"] = self.url
		if self.note:
			entry["note"] = self.note
		if self.abstract:
			entry["abstract"] = self.abstract

		return entry


