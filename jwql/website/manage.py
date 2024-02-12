#! /usr/bin/env python

"""Utility module for administrative tasks.

A python script version of Django's command-line utility for
administrative tasks (``django-admin``). Additionally, puts the project
package on ``sys.path`` and defines the ``DJANGO_SETTINGS_MODULE``
variable to point to the jwql ``settings.py`` file.

Generated by ``django-admin startproject`` using Django 2.0.1.

Use
---

    To run the web app server:
    ::

        python manage.py runserver

    To start the interactive shellL:
    ::

        python manage.py shell

    To run tests for all installed apps:
    ::

        python manage.py test

References
----------
For more information please see:
    ``https://docs.djangoproject.com/en/2.0/ref/django-admin/``
"""

import os
import sys

from jwql.utils.utils import get_config

if __name__ == "__main__":

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jwql_proj.settings")

    directory_mapping = {
        'filesystem': 'filesystem',
        'outputs': 'outputs',
        'preview_image_filesystem': 'preview_images',
        'thumbnail_filesystem': 'thumbnails'
    }

    for directory in ['filesystem', 'outputs', 'preview_image_filesystem', 'thumbnail_filesystem']:
        symlink_location = os.path.join(os.path.dirname(__file__), 'apps', 'jwql', 'static', directory_mapping[directory])
        if not os.path.exists(symlink_location):
            print("{} does not exist".format(symlink_location))
            symlink_path = get_config()[directory]
            os.symlink(symlink_path, symlink_location)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
