# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

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
