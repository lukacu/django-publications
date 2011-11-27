# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-
__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

import re
from django import forms
from django.forms import widgets
from django.db import models
from publications.widgets import PagesWidget, PeopleWidget
from publications.models import RoleType

class PagesForm(forms.MultiValueField):
	widget = PagesWidget

	def __init__(self, *args, **kwargs):
		forms.MultiValueField.__init__(self, [
			forms.IntegerField(),
			forms.IntegerField()], *args, **kwargs)

	def compress(self, data_list):
		if data_list:
			if data_list[0] and data_list[1]:
				if data_list[0] == data_list[1]:
					return str(data_list[0])
				return str(data_list[0]) + '-' + str(data_list[1])
			if data_list[0]:
				return str(data_list[0])
			if data_list[1]:
				return str(data_list[1])
		return ''


class PagesField(models.Field):
	def formfield(self, **kwargs):
		kwargs['form_class'] = PagesForm
		return models.Field.formfield(self, **kwargs)


	def get_internal_type(self):
		return 'CharField'

class PeopleField(forms.CharField):

  widget = PeopleWidget(attrs={'size':'100'})

  def to_python(self, value):
    "Normalize data to a list of touples."

    # Return an empty list if no input was given.
    if not value:
        return []

    people = []
    for person in value.split(','):
      m = re.match("([^\\(]+)\\(([^\\)]+)\\)", person.strip(), re.U)
      if m:
        people.append((m.group(2).strip(), m.group(1).strip()))
      else:
        people.append((None, person.strip()))
    print people
    return people

  def validate(self, value):
    # TODO: better validation
    # Use the parent's handling of required fields, etc.
    super(PeopleField, self).validate(value)



