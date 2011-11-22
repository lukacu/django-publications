# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import django
from django.db import models
from django.db.models.signals import post_init
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_str, force_unicode
from django.utils.functional import curry
from django.utils.translation import ugettext_lazy as _

class Group(models.Model):
  name = models.CharField(_('title'), max_length=255)
  text = models.TextField(_('text'), blank=True)

  class Meta:
    app_label = 'publications'

  def __unicode__(self):
    return self.name
