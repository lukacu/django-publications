# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os
import django
from datetime import datetime
from django.db import models
from django.db.models.signals import post_init
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.core.files import File
from django.utils.encoding import smart_str, force_unicode
from django.utils.functional import curry
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.http import urlquote_plus
from string import ascii_uppercase
from os.path import exists, splitext, join, basename
from publications.orderedmodel import OrderedModel
from taggit.managers import TaggableManager

DEFAULT_PERSON_ROLE = "author"
PROTECTED_PERSON_ROLES = ["author", "editor"]

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

# mapping of months
MONTHS_MAPPING = {
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

def generate_publication_objects(bibliography, update=False):

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

    try:
      ptype = PublicationType.objects.get(bibtex_type__iexact = entry['@type'])
    except ObjectDoesNotExist:
      continue

    # map integer fields to integers
    entry['month'] = MONTHS_MAPPING.get(entry['month'].lower(), 0)
    entry['volume'] = entry.get('volume', None)
    entry['number'] = entry.get('number', None)

    publication = Publication(
      type=ptype,
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
      doi=entry['doi'])

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

    if entry.has_key("keywords"):
      publication.set_keywords = [k.strip().lower() for k in entry['keywords'].split(",")]

    if entry.has_key("@file"):
      publication.set_file = entry["@file"]

    if entry.has_key("@meta") and type(entry["@meta"]) == dict:
      publication.set_metadata = entry["@meta"]

    # add publication
    publications.append(publication)

  return publications

def group_people_by_family_name(people):
  groups = {}

  for person in people:
    if groups.has_key(person.family_name):
      groups[person.family_name].append(person)
    else:
      groups[person.family_name] = [person]

  return groups

def merge_people(people):
  if len(people) < 2:
    return

  pivot = people[0]

  # Search for pivot element (primitive attempt)
  for person in people[1:]:
    if person.family_name == pivot.family_name:
      if len(person.primary_name) > len(pivot.primary_name):
        pivot = person
      elif person.primary_name == pivot.primary_name and person.middle_name and not pivot.middle_name:
        pivot = person

  for person in people:
    if person == pivot:
      continue
    Role.objects.filter(person = person).update(person = pivot)
    PersonNaming.objects.filter(person = person).update(person = pivot)
    person.delete()

def determine_file_name(instance, filename):
  p = "%016x" % instance.pk
  path = "publications"

  for i in xrange(0, len(p)-2, 2):
    path = join(path, p[i:i+2])

  if not exists(join(settings.MEDIA_ROOT, path)):
    os.makedirs(join(settings.MEDIA_ROOT, path))

  if not instance.pk:
    return join("publications", basename(filename))
  else:
    name, ext = splitext(filename)
    if ext == '':
      return join(path, p[-2:])
    else:
      return join(path, "%s%s" % (p[-2:], ext))

def parse_person_name(text):
  primary_name = None
  middle_name = None
  family_name = None
  if "," in text:
    parts = [e.strip() for e in text.partition(",")]
    primary_name = " ".join([e.strip() for e in parts[2].split(" ")])
    family_name = " ".join([e.strip() for e in parts[0].split(" ")])
  else:
    parts = [e.strip() for e in text.split(" ")]
    primary_name = parts[0]
    if len(parts) > 2:
      middle_name = parts[1]
      family_name = " ".join(parts[2:])
    else:
      family_name = " ".join(parts[1:])

  return (primary_name, middle_name, family_name)

def generate_person_object(text):
  (primary_name, middle_name, family_name) = parse_person_name(text)

  if middle_name:
    naming =  "%s %s %s" % (primary_name, middle_name, family_name)
  else:
    naming = "%s %s" % (primary_name, family_name)

  try:
    naming = PersonNaming.objects.get(naming = naming)
    return naming.person
  except ObjectDoesNotExist:
    p = Person(primary_name=primary_name, middle_name = middle_name, family_name=family_name)
    p.save()
    return p

def find_person_object(text):
  (primary_name, middle_name, family_name) = parse_person_name(text)

  if middle_name:
    naming =  "%s %s %s" % (primary_name, middle_name, family_name)
  else:
    naming = "%s %s" % (primary_name, family_name)

  try:
    naming = PersonNaming.objects.get(naming = naming)
    return naming.person
  except ObjectDoesNotExist:
    namings = PersonNaming.objects.filter(naming__icontains = family_name)
    return list(namings)

class RoleType(OrderedModel):
  identifier = models.CharField(_('identifier'), blank=False, unique=True, max_length=64)
  name = models.CharField(_('name'), blank=False, max_length=255)
  public = models.BooleanField(help_text='The type is publicly visible.', default=True)
  authorship = models.BooleanField(help_text='The type can be used for authorship related queries for people.', default=True)
  bibtex_field = models.CharField(_('BibTeX field'), blank=True, unique=True, max_length=64)

  def __unicode__(self):
    return self.name

class PublicationType(OrderedModel):
  identifier = models.CharField(_('identifier'), blank=False, unique=True, max_length=64)
  title = models.CharField(_('title'), blank=False, max_length=255)
  description = models.TextField(_('title'), blank=False)
  public = models.BooleanField(help_text='The type is displayed in public listings.', default=True)
  bibtex_type = models.CharField(_('BibTeX types that translate into this type'), blank=True, unique=True, max_length=64)

  def __unicode__(self):
    return self.title

class Group(models.Model):
  identifier = models.CharField(_('identifier'), max_length=255)
  title = models.CharField(_('title'), blank=True, max_length=255)
  public = models.BooleanField(help_text='Is displayed in group listing.', default=True)

  def __unicode__(self):
    return self.title

  def save(self, *args, **kwargs):
    if not self.title:
      self.title = self.identifier
    self.identifier = self.identifier.lower().replace(" ", "")
    super(Group, self).save(*args, **kwargs)

class Person(models.Model):
  primary_name = models.CharField(_('first name'), max_length=100, blank=False, null=False)
  middle_name = models.CharField(_('middle name'), max_length=50, blank=True, null=True)
  family_name = models.CharField(_('family name'), max_length=100, blank=False, null=False)
  url = models.URLField(blank=True, verify_exists=False, verbose_name='URL',
    help_text='Home page of the person.')
  public = models.BooleanField(
    help_text='Has a public listing page for publications.', default=True)
  group = models.ForeignKey(Group, verbose_name="default group", null=True, blank=True, on_delete=models.SET_NULL)

  def save(self, *args, **kwargs):
    super(Person, self).save(*args, **kwargs)

    try:
      PersonNaming.objects.get(naming = self.full_name())
    except ObjectDoesNotExist:
      naming = PersonNaming(naming = self.full_name(), person = self)
      naming.save()

  class Meta:
    verbose_name_plural = 'people'
    unique_together = ("primary_name", "family_name")

  def __unicode__(self):
    return self.full_name_reverse()

  def identifier(self):
    from publications.transcode import unicode_to_ascii
    return unicode_to_ascii(self.family_name).replace("?", "_")

  def full_name(self):
    if self.middle_name:
      return "%s %s %s" % (self.primary_name, self.middle_name, self.family_name)
    else:
      return "%s %s" % (self.primary_name, self.family_name)

  def full_name_reverse(self):
    if self.middle_name:
      return "%s, %s %s" % (self.family_name, self.primary_name, self.middle_name)
    else:
      return "%s, %s" % (self.family_name, self.primary_name)

  def get_absolute_url(self):
    return reverse("publications-person", kwargs={"person_id" : self.id, "slug" : slugify(self.full_name()) })


class PersonNaming(models.Model):
  naming = models.CharField(_('display name'), max_length=255, unique=True)
  person = models.ForeignKey(Person, verbose_name="person")

  def __unicode__(self):
    return self.naming

class Role(models.Model):
  order = models.PositiveIntegerField(editable=False)
  person = models.ForeignKey("Person")
  publication = models.ForeignKey("Publication")
  role = models.ForeignKey("RoleType", on_delete=models.PROTECT)

  def __unicode__(self):
    return "%s is %s of %s" % (self.person.full_name(), self.role.name, self.publication.title)

class Metadata(models.Model):
  publication = models.ForeignKey("Publication", verbose_name="publication", editable = False)
  key = models.CharField(_('key'), max_length=64, blank=False, null=False)
  value = models.CharField(_('value'), max_length=255, blank=True, null=False)

  class Meta:
    verbose_name_plural = 'metadata'
    unique_together = ("publication", "key")

  def __unicode__(self):
    return "%s: %s" % (self.key, self.value)

from publications.fields import PagesField

class Publication(models.Model):
  class Meta:
    ordering = ['-year', '-month', '-id']

  type = models.ForeignKey("PublicationType", on_delete=models.PROTECT)
  date_added = models.DateTimeField(_('date added'), default=datetime.now, editable = False, auto_now_add=True)
  date_modified = models.DateTimeField(_('date modified'), editable = False, auto_now = True, default=datetime.now)
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
  note = models.CharField(max_length=256, blank=True, null=True)
  keywords = TaggableManager(blank=True)
  url = models.URLField(blank=True, verify_exists=False, verbose_name='URL',
    help_text='Link to PDF or journal page.')
  code = models.URLField(blank=True, verify_exists=False,
    help_text='Link to page with code.')
  file = models.FileField(upload_to=determine_file_name, verbose_name='File', blank=True, null=True, help_text='The file resource attached to the entry. PDF format is preferred.')
  doi = models.CharField(max_length=128, verbose_name='DOI', blank=True)
  abstract = models.TextField("Abstract", blank=True)
  public = models.BooleanField(help_text='To hide a publication remove this flag.', default=True)
  groups = models.ManyToManyField(Group)

  def save(self, *args, **kwargs):

    # In case we do not have a primary key
    if not self.pk:
      super(Publication, self).save(*args, **kwargs)

    if hasattr(self, "set_people"):
      i = 0
      Role.objects.filter(publication = self).delete()
      for person in self.set_people:
        name = person[1].strip()
        if person[0]:
          role = person[0].strip().lower()
        else:
          role = DEFAULT_PERSON_ROLE
        if name == "":
          continue
        try:
          r = RoleType.objects.get(bibtex_field = role)
          person = generate_person_object(name)
          if not person:
            continue
          i = i + 1
          r = Role(person = person, publication = self, role=r, order = i)
          r.save()
        except ObjectDoesNotExist:
          pass

    if hasattr(self, "set_groups"):
      self.groups.clear()
      for group in self.set_groups:
        group = group.strip().lower()
        if group == "":
          continue
        try:
          g = Group.objects.get(identifier__iexact = group)
        except ObjectDoesNotExist:
          g = Group(identifier=group)
          g.save()
        self.groups.add(g)

    if hasattr(self, "set_metadata"):
      Metadata.objects.filter(publication = self).delete()
      for key, value in self.set_metadata.items():
        key = key.strip()
        if key == "":
          continue
        try:
          m = Metadata.objects.get(key = key, publication = self)
          m.value = value
        except ObjectDoesNotExist:
          m = Metadata(key=key, value = value, publication = self)
        m.save()

    if hasattr(self, "set_keywords"):
      keywords = filter(lambda k : len(k) > 0, self.set_keywords)
      self.keywords.set(*keywords)

    if hasattr(self, "set_file"):
      filename = self.set_file
      if exists(filename):
        f = open(filename)
        self.file = File(f)

    super(Publication, self).save(*args, **kwargs)

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
    return ", ".join([str(k) for k in self.keywords.all()])

  def get_absolute_url(self):
    slug = slugify(self.__unicode__())
    return reverse("publication", kwargs={"publication_id" : self.id, "slug" : slug })

  def month_bibtex(self):
    return MONTH_BIBTEX.get(self.month, '')

  def first_author(self):
    people = Role.objects.filter(publication=self).order_by("role", "order")
    try:
      return people[0].person
    except IndexError:
      return None

  def journal_or_book_title(self):
    if self.journal:
      return self.journal
    else:
      return self.book_title


  def people_as_string(self):
    roles = Role.objects.filter(publication = self).order_by("role__order", "order")

    people = []
    for role in roles:
      people.append("%s (%s)" % (role.person.full_name(), role.role.name))

    return ", ".join(people)

  def primary_authors(self):
    people = Role.objects.filter(publication = self).order_by("role", "order")
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

    try:
      author = RoleType.objects.get(bibtex_field = "author")
      entry["author"] = " and ".join([ p.person.full_name() for p in Role.objects.filter(role=author, publication = self).order_by("order") ])
    except ObjectDoesNotExist:
      pass

    try:
      editor = RoleType.objects.get(bibtex_field = "editor")
      entry["editor"] = " and ".join([ p.person.full_name() for p in Role.objects.filter(role=editor, publication = self).order_by("order") ])
    except ObjectDoesNotExist:
      pass

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
      entry["keywords"] = self.keywords_escaped()
    if self.doi:
      entry["doi"] = self.doi
    if self.url:
      entry["url"] = self.url
    if self.note:
      entry["note"] = self.note
    if self.abstract:
      entry["abstract"] = self.abstract

    return entry

class PublicationImportException(Exception):
   def __init__(self, message):
       self.message = message
   def __str__(self):
       return repr(self.message)

class PublicationUpdateException(Exception):
   def __init__(self, candidates):
       self.candidates = candidates

class PeopleMergeException(Exception):
   def __init__(self, candidates):
       self.candidates = candidates

class Import(models.Model):
  class Meta:
    ordering = ['date_added']

  source = models.CharField(max_length=64, editable = False)
  title = models.CharField(max_length=255, editable = False)
  data = models.TextField(blank = False, editable = False)
  date_added = models.DateTimeField(default=datetime.now, editable = False, auto_now_add=True)

  def __init__(self, *args, **kwargs):
    if kwargs.has_key('data') and type(kwargs['data']) != str:
      from django.utils import simplejson
      kwargs['data'] = simplejson.dumps(kwargs['data'])

    super(Import, self).__init__(*args, **kwargs)

  def get_data(self):
    from django.utils import simplejson
    return simplejson.loads(self.data)

  def construct_publication_object(self, publication_update = None, people_merge = None):
    entry = self.get_data()

    if not (entry.has_key('title') and entry.has_key('year')):
      raise PublicationImportException("Cannot match publication type %s" % entry['@type'])

    if getattr(settings, 'PUBLICATIONS_IMPORT_HANDLER', None):
      (module, sep, method) = settings.PUBLICATIONS_IMPORT_HANDLER.rpartition(".")
      handlermodule = __import__(module)
      if hasattr(handlermodule, method):
        handler = getattr(handlermodule, method)
        entry = handler(entry)

    try:
      ptype = PublicationType.objects.get(bibtex_type__iexact = entry['@type'])
    except ObjectDoesNotExist:
      raise PublicationImportException("Cannot match publication type %s" % entry['@type'])

    # map integer fields to integers
    # TODO: do this in BibTeX import module
    entry['month'] = MONTHS_MAPPING.get(entry.get('month', '').lower(), 0)

    publication = None

    if not publication_update:
      candidates = list(Publication.objects.filter(title__iexact = entry['title']))
      if len(candidates) > 0:
        raise PublicationUpdateException(candidates)
    else:
      try:
        publication = Publication.objects.get(pk=publication_update)
      except ObjectDoesNotExist:
        pass

    people = []

    candidates = {}
    for field in ["author", "editor"]:
      if entry.has_key(field):
        for name in entry[field].split(" and "):
          if not people_merge:
            candidate = find_person_object(name)
            if type(candidate) == list and len(candidate) > 0:
              candidates[name] = find_person_object(name)
              continue
            if people_merge:
              people.append((field, people_merge.get(name, name)))
            else:
              people.append((field, name))

    if len(candidates) > 0:
      raise PeopleMergeException(candidates)

    if not publication:
      publication = Publication(type=ptype, title=entry['title'], year=entry['year'])

    publication.month=entry.get('month', None)
    publication.journal=entry.get('journal', "")
    publication.book_title=entry.get('booktitle', "")
    publication.publisher=entry.get('publisher', "")
    publication.volume=entry.get('volume', None)
    publication.number=entry.get('number', None)
    publication.note=entry.get('note', "")
    publication.abstract=entry.get('abstract', "")
    publication.url=entry.get('url', "")
    publication.doi=entry.get('doi', "")

    if len(people) > 0:
      publication.set_people = people

    groups = entry.get('groups', "")
    if "," in groups:
      publication.set_groups = [g.strip() for g in groups.split(",")]
    else:
      publication.set_groups = [g.strip() for g in groups.split(" ")]

    if entry.has_key("keywords"):
      publication.set_keywords = [k.strip().lower() for k in entry['keywords'].split(",")]

    if entry.has_key("@file"):
      publication.set_file = entry["@file"]

    if entry.has_key("@meta") and type(entry["@meta"]) == dict:
      publication.set_metadata = entry["@meta"]

    return publication

  def __unicode__(self):
    return self.title


