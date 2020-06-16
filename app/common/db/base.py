# The wraps the Postgres backend to handle tsvector
# migrations: https://github.com/damoti/django-tsvector-field#installation
# -- the first installation of that package leads to
# https://github.com/damoti/django-tsvector-field/issues/3
# so we use this installation method.

import tsvector_field
from django_db_geventpool.backends.postgis import base


class DatabaseWrapper(base.DatabaseWrapper):
    SchemaEditorClass = tsvector_field.DatabaseSchemaEditor
