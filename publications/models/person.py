# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import django
from django.db import models
from django.db.models.signals import post_init
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_str, force_unicode
from django.utils.functional import curry
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

def parse_person_name(text):
  name = None
  surname = None
  display = None
  if "," in text:
    parts = [e.strip() for e in text.split(",")]
    name = parts[1].strip()
    surname = parts[0].strip()
  else:
    display = text.strip()

  try:
    p = Person.objects.get(surname__iexact = surname)
  except ObjectDoesNotExist:
    p = Person(name=name, surname=surname, display=display)
    p.save()

  return p


class Person(models.Model):
  display = models.CharField(_('display name'), max_length=255)
  name = models.CharField(_('first name'), max_length=100, blank=True, null=True)
  surname = models.CharField(_('family name'), max_length=100, blank=True, null=True)

  def save(self, *args, **kwargs):
    if not self.display:
      self.display = self.name + " " + self.surname
    super(Person, self).save(*args, **kwargs)


  class Meta:
    app_label = 'publications'

  def __unicode__(self):
    return self.name

  def identifier(self):
    if self.surname:
      return self.surname
    else:
      return self.display.replace(" ", "_")


