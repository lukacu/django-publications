#!/usr/bin/python
# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import django
from datetime import datetime
from django.db import models
from django.db.models.signals import post_init
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.files import File
from django.utils.encoding import smart_str, force_unicode
from django.utils.functional import curry
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlquote_plus
from string import ascii_uppercase
from publications.fields import PagesField
from os.path import exists, splitext, join, basename
from publications.orderedmodel import OrderedModel
from taggit.managers import TaggableManager

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
      ptype = PublicationType.objects.get(bibtex_type__contains = entry['@type'])
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

    # add publication
    publications.append(publication)

  return publications

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

class RoleType(OrderedModel):
  name = models.TextField(_('name'), blank=False)
  public = models.BooleanField(help_text='The type is publicly visible.', default=True)
  authorship = models.BooleanField(help_text='The type can be used for authorship related queries for people.', default=True)
  bibtex_field = models.TextField(_('BibTeX field'), blank=False, unique=True)

  def __unicode__(self):
    return self.name

class PublicationType(OrderedModel):
  title = models.TextField(_('title'), blank=False)
  description = models.TextField(_('title'), blank=False)
  public = models.BooleanField(help_text='The type is displayed in public listings.', default=True)
  bibtex_type = models.TextField(_('BibTeX types that translate into this type'), blank=False, unique=True)

  def __unicode__(self):
    return self.title

class Group(models.Model):
  identifier = models.CharField(_('identifier'), max_length=255)
  title = models.TextField(_('title'), blank=True)
  public = models.BooleanField(help_text='Is displayed in group listing.', default=True)

  def __unicode__(self):
    return self.title

  def save(self, *args, **kwargs):
    if not self.title:
      self.title = self.identifier
    self.identifier = self.identifier.lower().replace(" ", "")
    super(Group, self).save(*args, **kwargs)

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
  for person in people[1:-1]:
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
  if not instance.pk:
    return join("publications", basename(filename))
  else:
    name, ext = splitext(filename)
    if ext == '':
      return join("publications", "%d" % instance.pk)
    else:
      return join("publications", "%d%s" % (instance.pk, ext))

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
      family_name = " ".join(parts[2:-1])
    else:
      family_name = " ".join(parts[1:-1])

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

class PersonNaming(models.Model):
  naming = models.CharField(_('display name'), max_length=255, unique=True)
  person = models.ForeignKey(Person, verbose_name="person")

class Role(OrderedModel):
  person = models.ForeignKey("Person")
  publication = models.ForeignKey("Publication")
  role = models.ForeignKey("RoleType", on_delete=models.PROTECT)

class Metadata(models.Model):
  publication = models.ForeignKey("Publication", verbose_name="publication", editable = False)
  key = models.CharField(_('key'), max_length=64, blank=False, null=False)
  value = models.CharField(_('value'), max_length=255, blank=True, null=False)

  class Meta:
    verbose_name_plural = 'metadata'
    unique_together = ("publication", "key")

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
  note = models.CharField(max_length=256, blank=True)
  keywords = TaggableManager()
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
        role = person[0].strip().lower()
        if name == "":
          continue
        try:
          r = RoleType.objects.get(bibtex_field = role)
          person = parse_person_name(name)
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

    if hasattr(self, "set_keywords"):
      print self.set_keywords
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

