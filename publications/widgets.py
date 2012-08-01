# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from django import forms
from django.utils.safestring import mark_safe
from django.conf import settings
from django.forms.widgets import Input, MultiWidget, TextInput

class PagesWidget(MultiWidget):
	def __init__(self, *args, **kwargs):
		attrs = {'style': 'width: 40px; text-align: center;'}
		forms.widgets.MultiWidget.__init__(self,
			[TextInput(attrs), TextInput(attrs)], *args, **kwargs)


	def format_output(self, rendered_widgets):
		to = ' <span style="vertical-align: middle;">to</span> '
		return rendered_widgets[0] + to + rendered_widgets[1]


	def decompress(self, value):
		if value:
			values = value.split('-')

			if len(values) > 1:
				return values
			if len(values) > 0:
				return [values[0], values[0]]
		return [None, None]

class PeopleWidget(Input):
  pass

