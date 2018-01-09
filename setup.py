# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

data_files = []

import fnmatch
import os

for root, dirnames, filenames in os.walk(os.path.join('publications', 'templates')):
    for filename in fnmatch.filter(filenames, '*.html'):
        data_files.append(os.path.join('..', root, filename))

print data_files

setup(
    name = "django-publications",
    version = "0.1",
    author = "Luka Cehovin",
    description = "A Django app for managing a list of scientific publications",
    long_description = open("README.md").read(),
    license = "BSD",
    url = "https://github.com/lukacu/django-publications",
    download_url = "https://github.com/lukacu/django-publications/archive/master.zip",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    package_data={'': data_files},
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ]
)
