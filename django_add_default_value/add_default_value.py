# Copyright 2018 3YOURMIND GmbH

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and

from django.db.migrations.operations.base import Operation
from django.db import models


def is_text_field(model, field_name):
    options = model._meta  # type: models.base.Options
    field = options.get_field(field_name)
    return isinstance(field, models.TextField)


class AddDefaultValue(Operation):
    reversible = True

    def __init__(self, model_name, name, value):
        self.model_name = model_name
        self.name = name
        self.value = value

    def deconstruct(self):
        return self.__class__.__name__, [], {
            'model_name': self.model_name,
            'name': self.name,
            'value': self.value
        }

    @classmethod
    def is_correct_vendor(cls, vendor):
        return vendor.startswith('mysql') or vendor.startswith('postgre')

    @classmethod
    def is_postgresql(cls, vendor):
        return vendor.startswith('postgre')

    @classmethod
    def is_mariadb(cls, connection):
        if hasattr(connection, 'mysql_is_mariadb'):
            return connection.mysql_is_mariadb()
        return False

    @classmethod
    def can_have_default_for_text(cls, connection):
        """
        MySQL has not allowed DEFAULT for BLOB and TEXT fields since the
        beginning of time, but it is changing:

            Before MariaDB 10.2.1, BLOB and TEXT columns could not be assigned
            a DEFAULT value. This restriction was lifted in MariaDB 10.2.1.

        Oracle does not yet have a version available that supports it,
        quoting the `documentation
        <https://dev.mysql.com/doc/refman/8.0/en/blob.html>`_:

            BLOB and TEXT columns cannot have DEFAULT values.

        :param connection: The DB connection, aka `schema_editor.connection`
        :type connection: :class:`django.db.backends.base.base.BaseDatabaseWrapper`
        :return: A boolean indicating we support default values for text
                 fields.
        :rtype: bool
        """
        if cls.is_postgresql(connection.vendor):
            return True

        if not hasattr(connection, 'mysql_version') or \
                not callable(getattr(connection, 'mysql_version', None)):
            return False

        if not cls.is_mariadb(connection):
            return False

        maj, min, patch = connection.mysql_version()
        return maj > 9 and min > 1 and patch > 0

    def state_forwards(self, app_label, state):
        """
        Take the state from the previous migration, and mutate it
        so that it matches what this migration would perform.
        """
        # Nothing to do
        # because the field should have the default set anyway
        pass

    def clean_value(self, vendor, value):
        """
        Lie, cheat and apply plastic surgery where needed

        :param vendor: database vendor we need to perform operations for
        :param value: the value as provided in the migration
        :return: a better version of ourselves
        """
        if isinstance(value, bool) and not self.is_postgresql(vendor):
            return 1 if value else 0

        return value

    def can_apply_default(self, model, name, conn):
        if is_text_field(model, name) and \
                not self.can_have_default_for_text(conn):
            return False

        return True

    def database_forwards(
        self, app_label, schema_editor, from_state, to_state
    ):
        """
        Perform the mutation on the database schema in the normal
        (forwards) direction.
        """
        if not self.is_correct_vendor(schema_editor.connection.vendor):
            return

        to_model = to_state.apps.get_model(app_label, self.model_name)
        if not self.can_apply_default(
                to_model, self.name, schema_editor.connection):
            return

        self.value = self.clean_value(schema_editor.connection.vendor,
                                      self.value)

        if self.is_postgresql(schema_editor.connection.vendor):
            sql_query = \
                'ALTER TABLE {0} ALTER COLUMN "{1}" ' \
                'SET DEFAULT \'{2}\';'.format(
                    to_model._meta.db_table, self.name, self.value
                )
        else:
            sql_query = \
                'ALTER TABLE `{0}` ALTER COLUMN `{1}` SET DEFAULT \'{2}\';'\
                .format(to_model._meta.db_table, self.name, self.value)

        schema_editor.execute(sql_query)

    def database_backwards(
            self, app_label, schema_editor, from_state, to_state
    ):
        """
        Perform the mutation on the database schema in the reverse
        direction - e.g. if this were CreateModel, it would in fact
        drop the model's table.
        """
        if not self.is_correct_vendor(schema_editor.connection.vendor):
            return

        to_model = to_state.apps.get_model(app_label, self.model_name)
        if not self.can_apply_default(
                to_model, self.name, schema_editor.connection):
            return

        self.value = self.clean_value(schema_editor.connection.vendor,
                                      self.value)
        if self.is_postgresql(schema_editor.connection.vendor):
            sql_query = 'ALTER TABLE {0} ALTER COLUMN "{1}" DROP DEFAULT;'.\
                format(to_model._meta.db_table, self.name)

        else:
            sql_query = 'ALTER TABLE `{0}` ALTER COLUMN `{1}` DROP DEFAULT;'.\
                format(to_model._meta.db_table, self.name)
        schema_editor.execute(sql_query)

    def describe(self):
        """
        Output a brief summary of what the action does.
        """
        return 'Add to field {0} the default value {1}'.format(
            self.name, self.value)
