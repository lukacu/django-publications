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
from publications.bibtex import BIBTEX_TYPES
from os.path import exists, splitext, join, basename

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

    # map integer fields to integers
    entry['month'] = MONTHS_MAPPING.get(entry['month'].lower(), 0)
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

    if entry.has_key("@file"):
      publication.set_file = entry["@file"]

    # add publication
    publications.append(publication)

  return publications

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

def merge_group(group):
  pivot = group[0]

#  for person in group:
#    if 

  for person in group:
    if person == pivot:
      continue
    roles = Role.objects.filter(person = person)
    for role in roles:
      role.person = pivot
      role.save()
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
      return "%s, %s %s" % (self.primary_name, self.middle_name, self.family_name)
    else:
      return "%s, %s" % (self.primary_name, self.family_name)

class PersonNaming(models.Model):
  naming = models.CharField(_('display name'), max_length=255, unique=True)
  person = models.ForeignKey(Person, verbose_name="person")


class Role(models.Model):
  class Meta:
    ordering = ["role", "sequence"]

  person = models.ForeignKey("Person")
  publication = models.ForeignKey("Publication")
  role = models.CharField(_('role'), choices=ROLE_CHOICES, max_length=16)
  sequence = models.IntegerField(blank=True, null=True)


class Publication(models.Model):
  class Meta:
    ordering = ['-year', '-month', '-id']

  type = models.CharField(max_length=64, choices=TYPE_CHOICES)
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
  keywords = models.CharField(max_length=1024, blank=True,
    help_text='List of keywords separated by commas.')
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
          g = Group.objects.get(identifier__iexact = group)
        except ObjectDoesNotExist:
          g = Group(identifier=group)
          g.save()
        self.groups.add(g)

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
    return [(keyword.strip(), urlquote_plus(keyword.strip()))
      for keyword in self.keywords.split(',')]

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
    entry["author"] = " and ".join([ p.person.full_name() for p in Role.objects.filter(role="author", publication = self).order_by("sequence") ])
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

