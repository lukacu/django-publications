django-publications
===================

A Django app for managing scientific publications. A working setup of this fork can be seen [here](http://prints.vicos.si/).

Requirements
------------

* python >= 2.8.0
* django >= 1.8.0
* django-taggit >= 0.22.1

The app has been tested with the above versions, but older versions might also work.

Installation
------------

0) Install dependencies.

1) Install the `publications` folder so that it is visible in Python path.

2) Add the publications app to your settings.py.

3) Add the following to your project's `urls.py`:

	url(r'^publications/', include('publications.urls')),

4) Run `python <yourproject>/manage.py syncdb` and `python <yourproject>/manage.py collectstatic`

Customization
-------------

There are some aspects of this app that can be costumized using your `settings.py` file:

* TODO

Documentation
-------------

TODO
