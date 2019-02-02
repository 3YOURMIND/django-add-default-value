# Copyright 2018 3YOURMIND GmbH

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
import warnings

from django.db.migrations.operations.base import Operation
from django.db import models
from datetime import date, datetime
from django.utils import timezone


NOW = "__NOW__"
TODAY = "__TODAY__"


def is_text_field(model, field_name):
    options = model._meta  # type: models.base.Options
    field = options.get_field(field_name)
    return isinstance(field, models.TextField)


def is_date_field(model, field_name):
    options = model._meta  # type: models.base.Options
    field = options.get_field(field_name)
    return isinstance(field, models.DateField)


class AddDefaultValue(Operation):
    reversible = True
    value_quote = "'"
    constant_quote = ""
    func_quote = ""

    def __init__(self, model_name, name, value):
        self.model_name = model_name
        self.name = name
        self.value = value

    def deconstruct(self):
        return (
            self.__class__.__name__,
            [],
            {"model_name": self.model_name, "name": self.name, "value": self.value},
        )

    @classmethod
    def is_supported_vendor(cls, vendor):
        return (cls.is_postgresql(vendor) or cls.is_mysql(vendor)) and not cls.is_mssql(
            vendor
        )

    @classmethod
    def is_mysql(cls, vendor):
        return vendor.startswith("mysql")

    @classmethod
    def is_postgresql(cls, vendor):
        return vendor.startswith("postgre")

    @classmethod
    def is_mssql(cls, vendor):
        return vendor.startswith("microsoft")

    @classmethod
    def is_mariadb(cls, connection):
        if hasattr(connection, "mysql_is_mariadb"):
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
        :type connection: django.db.backends.base.base.BaseDatabaseWrapper
        :return: A boolean indicating we support default values for text
                 fields.
        :rtype: bool
        """
        if cls.is_postgresql(connection.vendor):
            return True

        if not hasattr(connection, "mysql_version") or not callable(
            getattr(connection, "mysql_version", None)
        ):
            return False

        if not cls.is_mariadb(connection):
            return False

        major, minor, patch = connection.mysql_version()
        return major > 9 and minor > 1 and patch > 0

    def state_forwards(self, app_label, state):
        """
        Take the state from the previous migration, and mutate it
        so that it matches what this migration would perform.
        """
        # Nothing to do
        # because the field should have the default set anyway
        pass

    def _clean_temporal(self, vendor, value):
        if isinstance(value, date):
            return value.isoformat(), self.value_quote, True

        if isinstance(value, datetime):
            if self.is_postgresql(vendor):
                return value.isoformat(" ", timespec="seconds"), self.value_quote, True
            else:
                naive = timezone.make_naive(value)
                return naive.isoformat(" ", timespec="seconds"), self.value_quote, True

        return value, self.value_quote, False

    def _clean_temporal_constants(self, vendor, value):
        if value == NOW:
            if self.is_postgresql(vendor):
                return "now()", self.func_quote, True
            elif self.is_mysql(vendor):
                return "CURRENT_DATE", self.constant_quote, True
        elif value == TODAY and self.is_postgresql(vendor):
            return "now()", self.func_quote, True

        return value, self.value_quote, False

    def clean_value(self, vendor, value):
        """
        Lie, cheat and apply plastic surgery where needed

        :param vendor: database vendor we need to perform operations for
        :param value: the value as provided in the migration
        :return: a 2-tuple containing the new value and the quotation to use
        """
        if isinstance(value, bool) and not self.is_postgresql(vendor):
            if value:
                return 1, self.value_quote

            return 0, self.value_quote

        value, quote, handled = self._clean_temporal(vendor, value)
        if handled:
            return value, quote

        value, quote, handled = self._clean_temporal_constants(vendor, value)
        if handled:
            return value, quote

        return value, self.value_quote

    def can_apply_default(self, model, name, connection):
        if is_text_field(model, name) and not self.can_have_default_for_text(
            connection
        ):
            return False

        if self.value == TODAY and not self.is_postgresql(connection.vendor):
            return False

        if is_date_field(model, name) and self.is_mysql(connection.vendor):
            return False

        return True

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        """
        Perform the mutation on the database schema in the normal
        (forwards) direction.
        """
        if not self.is_supported_vendor(schema_editor.connection.vendor):
            return

        to_model = to_state.apps.get_model(app_label, self.model_name)
        if not self.can_apply_default(to_model, self.name, schema_editor.connection):
            warnings.warn(
                "You requested a default for a field / database combination "
                "that does not allow one. The default will not be set on: "
                "{model}.{field}.".format(model=to_model, field=self.name)
            )
            return

        sql_value, quote = self.clean_value(
            schema_editor.connection.vendor, self.value
        )
        format_kwargs = dict(
            table=to_model._meta.db_table,
            field=self.name,
            value=sql_value,
            quote=quote,
        )
        if self.is_postgresql(schema_editor.connection.vendor):
            sql_query = (
                'ALTER TABLE {table} ALTER COLUMN "{field}" '
                "SET DEFAULT {quote}{value}{quote};".format(**format_kwargs)
            )
        else:
            sql_query = (
                "ALTER TABLE `{table}` ALTER COLUMN `{field}` SET DEFAULT "
                "{quote}{value}{quote};".format(**format_kwargs)
            )

        schema_editor.execute(sql_query)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        """
        Perform the mutation on the database schema in the reverse
        direction - e.g. if this were CreateModel, it would in fact
        drop the model's table.
        """
        if not self.is_supported_vendor(schema_editor.connection.vendor):
            return

        to_model = to_state.apps.get_model(app_label, self.model_name)
        if not self.can_apply_default(to_model, self.name, schema_editor.connection):
            return

        self.value, __ = self.clean_value(schema_editor.connection.vendor, self.value)
        if self.is_postgresql(schema_editor.connection.vendor):
            sql_query = 'ALTER TABLE {table} ALTER COLUMN "{field}" DROP DEFAULT;'.format(
                table=to_model._meta.db_table, field=self.name
            )

        else:
            sql_query = (
                "ALTER TABLE `{table}` ALTER COLUMN `{field}` DROP "
                "DEFAULT;".format(table=to_model._meta.db_table, field=self.name)
            )

        schema_editor.execute(sql_query)

    def describe(self):
        """
        Output a brief summary of what the action does.
        """
        return "Add to field {field} the default value {value}".format(
            field=self.name, value=self.value
        )
