# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import os
from datetime import datetime
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.core.files import File
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from os.path import exists, splitext, join, basename
from tagging.fields import TagField
from tagging.models import Tag

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

def generate_publication_object(entry, publication_update = None, people_merge = None):

  if getattr(settings, 'PUBLICATIONS_IMPORT_HANDLER', None):
    (module, sep, method) = settings.PUBLICATIONS_IMPORT_HANDLER.rpartition(".")
    handlermodule = __import__(module)
    if hasattr(handlermodule, method):
      handler = getattr(handlermodule, method)
      entry = handler(entry)

  publication_type = resolve_publication_type(entry['type'])
  if not publication_type:
    raise PublicationImportException("Unrecognized publication type %s" % entry['type'])

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
  if entry.has_key("authors"):
    for name in entry["authors"]:
      if people_merge is None:
        candidate = find_person_object(name)
        if type(candidate) == list and len(candidate) > 0:
          candidates[name] = [str(c) for c in candidate]
        else:
          people.append(name)
      else:
        people.append((people_merge.get(name, name), name))

  if len(candidates) > 0:
    raise PeopleMergeException(candidates)

  if not publication:
    publication = Publication(type=publication_type["identifier"], title=entry['title'], year=entry['year'])

  publication.month=MONTHS_MAPPING.get(entry.get('month', "").lower(), None)
  publication.within=entry.get('within', "")
  publication.publisher=entry.get('publisher', "")
  publication.volume=entry.get('volume', None)
  publication.number=entry.get('number', None)
  publication.pages=entry.get('pages', None)
  publication.note=entry.get('note', "")
  publication.abstract=entry.get('abstract', "")
  publication.url=entry.get('url', "")
  publication.code=entry.get('code', "")
  publication.doi=entry.get('doi', "")

  if len(people) > 0:
    publication.set_people = people

  groups = entry.get('groups', "")
  if "," in groups:
    publication.set_groups = [g.strip() for g in groups.split(",")]
  else:
    publication.set_groups = [g.strip() for g in groups.split(" ")]

  if entry.has_key("tags"):
    publication.set_tags = [k.strip().lower() for k in entry['tags'] if k.strip() != ""]

  if entry.has_key("files") and type(entry["files"]) == list:
    publication.set_files = entry["files"]

  if entry.has_key("metadata") and type(entry["metadata"]) == dict:
    publication.set_metadata = entry["metadata"]

  return publication


def group_people_by_family_name(people):
  groups = {}

  for person in people:
    key = slugify(person.family_name.strip())
    if groups.has_key(key):
      groups[key].append(person)
    else:
      groups[key] = [person]

  return groups

def merge_people(people, pivot = None):
  if len(people) < 2:
    return

  if not pivot:
    pivot = people[0]

    # Search for pivot element (primitive attempt)
    for person in people[1:]:
      if person.family_name == pivot.family_name:
        if len(person.primary_name) > len(pivot.primary_name):
          pivot = person
        elif person.primary_name == pivot.primary_name:
          pivot = person

  for person in people:
    if person == pivot:
      continue
    Authorship.objects.filter(person = person).update(person = pivot)
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
  if "," in text:
    parts = [e.strip() for e in text.partition(",")]
    primary_name = " ".join([e.strip() for e in parts[2].split(" ")])
    family_name = " ".join([e.strip() for e in parts[0].split(" ")])
  else:
    parts = [e.strip() for e in text.split(" ")]
    primary_name = " ".join(parts[0:-1])
    family_name = parts[len(parts)-1]

  return primary_name, family_name

def merge_person_name(name1, name2):
  name = [None, None]
  for i in [0, 1]:
    if name1[i] and name2[i]:
      if len(name2[i]) < len(name1[i]):
        name[i] = name1[i]
      elif len(name2[i]) > len(name1[i]):
        name[i] = name2[i]
      else:
        name[i] = name1[i]
    elif name1[i] and not name2[i]:
      name[i] = name1[i]
    elif not name1[i] and name2[i]:
      name[i] = name2[i]
    else:
      name[i] = name1[i]

  return name[0], name[1]

def generate_person_object(text, suggest = None):
  (primary_name, family_name) = parse_person_name(text)

  try:
    person = Person.objects.get(primary_name = primary_name, family_name = family_name)

    if suggest:
      (primary_name, family_name) = merge_person_name(parse_person_name(text), parse_person_name(suggest))
      person.primary_name = primary_name
      person.family_name = family_name
      person.save()

  except ObjectDoesNotExist:
    person = Person(primary_name=primary_name, family_name=family_name)
    person.save()

  return person

def find_person_object(text):
  (primary_name, family_name) = parse_person_name(text)

  try:
    person = Person.objects.get(primary_name = primary_name, family_name = family_name)
    return person
  except ObjectDoesNotExist:
    candidates = Person.objects.filter( family_name__iexact = family_name)
    return list(candidates)

class Group(models.Model):
  identifier = models.CharField(_('identifier'), max_length=255)
  title = models.CharField(_('title'), blank=True, max_length=255)
  public = models.BooleanField(help_text='Is displayed in group listing.', default=False)

  def __unicode__(self):
    return self.title

  def save(self, *args, **kwargs):
    if not self.title:
      self.title = self.identifier
    self.identifier = self.identifier.lower().replace(" ", "")
    super(Group, self).save(*args, **kwargs)

class Person(models.Model):
  primary_name = models.CharField(_('first name'), max_length=255, blank=False, null=False)
  family_name = models.CharField(_('family name'), max_length=255, blank=False, null=False)
  url = models.URLField(blank=True, verbose_name='URL',
    help_text='Home page of the person.')
  public = models.BooleanField(
    help_text='Has a public listing page for publications.', default=True)
  group = models.ForeignKey(Group, verbose_name="default group", null=True, blank=True, on_delete=models.SET_NULL)

  class Meta:
    verbose_name_plural = 'people'
    ordering = ['family_name', 'primary_name']

  def __unicode__(self):
    return self.full_name_reverse()

  def identifier(self):
    from publications_bibtex.transcode import unicode_to_ascii
    return unicode_to_ascii(self.family_name).replace("?", "_")

  def full_name(self):
      return "%s %s" % (self.primary_name, self.family_name)

  def full_name_reverse(self):
      return "%s, %s" % (self.family_name, self.primary_name)

  def get_absolute_url(self):
    return reverse("publications-person", kwargs={"person_id" : self.id })

  def first_letter(self):
    return self.family_name and self.family_name[0].upper() or ''

class PublicationType(models.Model):
  identifier = models.CharField("Identifier", max_length=128)
  title = models.CharField("Title", max_length=128)
  description = models.TextField("Description", blank=True)
  weight = models.IntegerField(default=0)

  def __unicode__(self):
    return self.title


class Authorship(models.Model):
  order = models.PositiveIntegerField(editable=False)
  person = models.ForeignKey("Person")
  publication = models.ForeignKey("Publication")

  def __unicode__(self):
    return "%s is author of %s" % (self.person.full_name(), self.publication.title)

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

  publication_type = models.ForeignKey("PublicationType", null=True)
  date_added = models.DateTimeField(_('date added'), default=datetime.now, editable = False, auto_now_add=True)
  date_modified = models.DateTimeField(_('date modified'), editable = False, auto_now = True, default=datetime.now)
  title = models.CharField(max_length=512)
  people = models.ManyToManyField("Person", through='Authorship')
  year = models.PositiveIntegerField(max_length=4)
  month = models.IntegerField(choices=MONTH_CHOICES, blank=True, null=True)
  within = models.CharField("Published in", max_length=256, blank=True)
  publisher = models.CharField(max_length=256, blank=True)
  volume = models.CharField(max_length=32,blank=True, null=True)
  number = models.CharField(max_length=32,blank=True, null=True, verbose_name='Issue number')
  pages = PagesField(max_length=32, blank=True)
  note = models.CharField(max_length=256, blank=True, null=True)
  tags = TagField(blank=True)
  url = models.URLField(blank=True, verbose_name='URL', help_text='Link to PDF or a journal page.')
  code = models.URLField(blank=True, help_text='Link to page with code.')
  file = models.FileField(upload_to=determine_file_name, verbose_name='File', blank=True, null=True, help_text='The file resource attached to the entry. PDF format is preferred.')
  doi = models.CharField(max_length=128, verbose_name='DOI', blank=True)
  abstract = models.TextField("Abstract", blank=True)
  public = models.BooleanField(help_text='To hide a publication remove this flag.', default=True)
  groups = models.ManyToManyField(Group)

  def type(self):
    return self.publication_type

  def save(self, *args, **kwargs):

    # In case we do not have a primary key

    if not self.pk:
      super(Publication, self).save(*args, **kwargs)

    if hasattr(self, "set_people"):
      i = 0
      Authorship.objects.filter(publication = self).delete()
      for person in self.set_people:
        if type(person) is tuple:
          name = person[0].strip()
          suggestion = person[1].strip()
        else:
          name = person
          suggestion = None
        if name == "":
          continue
        try:
          person = generate_person_object(name, suggestion)
          if not person:
            continue
          i += 1
          r = Authorship(person = person, publication = self, order = i)
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

    if hasattr(self, "set_tags"):
      Tag.objects.update_tags(self, " ".join([ '"%s"' % t for t in self.set_tags ]))

    files = getattr(self, "set_files", None)
    if files and len(files) > 0:
      filename = files[0]
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

  def get_absolute_url(self):
    return reverse("publication", kwargs={"publication_id" : self.id })

  def authors(self):
    return [author.person for author in Authorship.objects.filter(publication = self).order_by("order")]

  def first_author(self):
    people = Authorship.objects.filter(publication=self).order_by("order")
    try:
      return people[0].person
    except IndexError:
      return None

  def generate_identifier(self):
    from publications_bibtex.transcode import unicode_to_ascii

    first_author = self.first_author()
    if first_author:
      author_identifier = first_author.identifier()
    else:
      author_identifier = "UNCREDITED"

    firstword, restwords= self.title.split(' ',1)

    return author_identifier + str(self.year) + unicode_to_ascii(firstword).replace("?", "_")

  def people_as_string(self):
    authors = Authorship.objects.filter(publication = self).order_by("order")
    return "; ".join([author.person.full_name_reverse() for author in authors])

  def to_dictionary(self, longfields=True):
    entry = {"title": self.title,
             "authors": [p.person.full_name() for p in Authorship.objects.filter(publication=self).order_by("order")],
             "year": self.year}

    if self.within:
      entry["within"] = self.within
    if self.publisher:
      entry["publisher"] = self.publisher
    if self.volume:
      entry["volume"] = self.volume
    if self.number:
      entry["number"] = self.number
    if self.pages:
      entry["pages"] = self.pages
    if self.month:
      entry["month"] = self.month
    if self.tags:
      entry["keywords"] = ", ".join([str(k) for k in Tag.objects.get_for_object(self)])
    if self.doi:
      entry["doi"] = self.doi
    if self.url:
      entry["url"] = self.url
    if self.note:
      entry["note"] = self.note
    if self.abstract:
      entry["abstract"] = self.abstract

    md = {}
    metadata = Metadata.objects.filter(publication=self)
    for mdentry in metadata:
      md[mdentry.key] = mdentry.value

    entry["metadata"] = md

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

  def __unicode__(self):
    return self.title


