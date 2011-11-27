django-publications
===================

A Django app for managing scientific publications.

Requirements
------------

* python >= 2.5.0
* django >= 1.3.0
* django-taggit >= 0.9.3

The app has been tested with the above versions, but older versions might also work.

Installation
------------

1) Install the `publications` folder so that it is visible in Python path.

2) Add the publications app to your settings.py.

3) Create publications folder in your media folder (used for storing files).

2) Add the following to your project's `urls.py`:

	url(r'^publications/', include('publications.urls')),
	url(r'^admin/publications/publication/import_bibtex/$', 'publications.admin_views.import_bibtex')

3) Run `python <yourproject>/manage.py syncdb`

Customization
-------------

There are some aspects of this app that can be costumized using your `settings.py` file:

* TODO

Documentation
-------------

TODO
