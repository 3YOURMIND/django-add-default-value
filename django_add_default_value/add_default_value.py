# Copyright 2018 3YOURMIND GmbH

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
from __future__ import unicode_literals
import warnings

import django
from django.db.migrations.operations.base import Operation
from django.db import models
from datetime import date, datetime
from django.utils import timezone

NOW = "__NOW__"
TODAY = "__TODAY__"
START = 0
END = 1


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
    quotes = {
        "value": ("'", "'"),
        "constant": ("", ""),
        "function": ("", ""),
        "name": ('"', '"'),
    }

    def __init__(self, model_name, name, value):
        self.model_name = model_name
        self.name = name
        self.value = value

    def describe(self):
        """
        Output a brief summary of what the action does.
        """
        return "Add to field {model}.{field} the default value {value}".format(
            model=self.model_name, field=self.name, value=self.value
        )

    def state_forwards(self, app_label, state):
        """
        Take the state from the previous migration, and mutate it
        so that it matches what this migration would perform.
        """
        # Nothing to do
        # because the field should have the default set anyway
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        """
        Perform the mutation on the database schema in the normal
        (forwards) direction.
        """
        if not self.is_supported_vendor(schema_editor.connection.vendor):
            return

        self.initialize_vendor_state(schema_editor)

        to_model = to_state.apps.get_model(app_label, self.model_name)
        if not self.can_apply_default(to_model, self.name, schema_editor.connection):
            warnings.warn(
                "You requested a default for a field / database combination "
                "that does not allow one. The default will not be set on: "
                "{model}.{field}.".format(model=to_model.__name__, field=self.name)
            )
            return

        sql_value, value_quote = self.clean_value(
            schema_editor.connection.vendor, self.value
        )
        format_kwargs = dict(
            table=to_model._meta.db_table,
            field=self.name,
            value=sql_value,
            value_quote_start=value_quote[START],
            value_quote_end=value_quote[END],
            name_quote_start=self.quotes["name"][START],
            name_quote_end=self.quotes["name"][END],
        )
        if not self.is_mssql(schema_editor.connection.vendor):
            sql_query = (
                "ALTER TABLE {name_quote_start}{table}{name_quote_end} "
                "ALTER COLUMN {name_quote_start}{field}{name_quote_end} "
                "SET DEFAULT {value_quote_start}{value}{value_quote_end};".format(
                    **format_kwargs
                )
            )
        else:
            constraint_name = self.mssql_constraint_name()
            format_kwargs.update(constraint_name=constraint_name)
            sql_query = (
                "ALTER TABLE {name_quote_start}{table}{name_quote_end} "
                "ADD CONSTRAINT {name_quote_start}{constraint_name}{name_quote_end} "
                "DEFAULT {value_quote_start}{value}{value_quote_end} "
                "FOR {name_quote_start}{field}{name_quote_end};".format(**format_kwargs)
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

        self.initialize_vendor_state(schema_editor)

        to_model = to_state.apps.get_model(app_label, self.model_name)
        if not self.can_apply_default(to_model, self.name, schema_editor.connection):
            return

        format_kwargs = dict(
            table=to_model._meta.db_table,
            field=self.name,
            name_quote_start=self.quotes["name"][START],
            name_quote_end=self.quotes["name"][END],
        )
        if not self.is_mssql(schema_editor.connection.vendor):
            sql_query = (
                "ALTER TABLE {name_quote_start}{table}{name_quote_end} "
                "ALTER COLUMN {name_quote_start}{field}{name_quote_end} "
                "DROP DEFAULT;".format(**format_kwargs)
            )
        else:
            constraint_name = self.mssql_constraint_name()
            format_kwargs.update(constraint_name=constraint_name)
            sql_query = "DROP DEFAULT {name_quote_start}{constraint_name}{name_quote_end};".format(
                **format_kwargs
            )

        schema_editor.execute(sql_query)

    def deconstruct(self):
        return (
            self.__class__.__name__,
            [],
            {"model_name": self.model_name, "name": self.name, "value": self.value},
        )

    def initialize_vendor_state(self, schema_editor):
        self.set_quotes(schema_editor.connection.vendor)
        major, minor, patch, __, ___ = django.VERSION
        if (
            self.is_mysql(schema_editor.connection.vendor)
            and version_with_broken_quote_value(major, minor, patch)
            and not hasattr(schema_editor.__class__, "_patched_quote_value")
        ):
            schema_editor.__class__.quote_value = quote_value
            schema_editor.__class__._patched_quote_value = True

    def set_quotes(self, vendor):
        """
        Set the various quotes according to vendor. The default quotes are set to the
        default vendor.

        :param vendor: Connection vendor string as provided by the db backend
        """
        if self.is_default_vendor(vendor):
            self.quotes["name"] = ('"', '"')

        if self.is_mysql(vendor):
            self.quotes["name"] = ("`", "`")

        if self.is_mssql(vendor):
            self.quotes["name"] = ("[", "]")

    @classmethod
    def is_supported_vendor(cls, vendor):
        return cls.is_postgresql(vendor) or cls.is_mysql(vendor) or cls.is_mssql(vendor)

    @classmethod
    def is_default_vendor(cls, vendor):
        return cls.is_postgresql(vendor)

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

    def can_apply_default(self, model, name, connection):
        if is_text_field(model, name) and not self.can_have_default_for_text(
            connection
        ):
            return False

        if self.value == TODAY and self.is_mysql(connection.vendor):
            return False

        return True

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
        if cls.is_postgresql(connection.vendor) or cls.is_mssql(connection.vendor):
            return True

        if not hasattr(connection, "mysql_version") or not callable(
            getattr(connection, "mysql_version", None)
        ):
            return False

        if not cls.is_mariadb(connection):
            return False

        # noinspection PyUnresolvedReferences
        major, minor, patch = connection.mysql_version()
        return major > 9 and minor > 1 and patch > 0

    def clean_value(self, vendor, value):
        """
        Lie, cheat and apply plastic surgery where needed

        :param vendor: database vendor we need to perform operations for
        :param value: the value as provided in the migration
        :return: a 2-tuple containing the new value and the quotation to use
        """
        if isinstance(value, bool) and not self.is_postgresql(vendor):
            if value:
                return 1, self.quotes["value"]

            return 0, self.quotes["value"]

        value, quote, handled = self._clean_temporal(vendor, value)
        if handled:
            return value, quote

        value, quote, handled = self._clean_temporal_constants(vendor, value)
        if handled:
            return value, quote

        return value, self.quotes["value"]

    def mssql_constraint_name(self):
        return "DADV_{model}_{field}_DEFAULT".format(
            model=self.model_name, field=self.name
        )

    def _clean_temporal(self, vendor, value):
        if isinstance(value, date):
            return value.isoformat(), self.quotes["value"], True

        if isinstance(value, datetime):
            if self.is_postgresql(vendor):
                return (
                    value.isoformat(" ", timespec="seconds"),
                    self.quotes["value"],
                    True,
                )
            else:
                naive = timezone.make_naive(value)
                return (
                    naive.isoformat(" ", timespec="seconds"),
                    self.quotes["value"],
                    True,
                )

        return value, self.quotes["value"], False

    def _clean_temporal_constants(self, vendor, value):
        if value == NOW or value == TODAY:
            if self.is_postgresql(vendor):
                return "now()", self.quotes["function"], True
            elif self.is_mssql(vendor):
                return "GETDATE()", self.quotes["function"], True

        # https://stackoverflow.com/a/20461045/10000573
        if value == NOW and self.is_mysql(vendor):
            return "CURRENT_TIMESTAMP", self.quotes["constant"], True

        return value, self.quotes["value"], False


def version_with_broken_quote_value(major, minor, patch):
    if major == 2:
        if minor == 1 and patch < 9:
            return True
        elif minor == 2 and patch < 2:
            return True

    return False


def quote_value(self, value):
    self.connection.ensure_connection()

    # MySQLdb escapes to string, PyMySQL to bytes.
    quoted = self.connection.connection.escape(
        value, self.connection.connection.encoders
    )
    if isinstance(value, str) and isinstance(quoted, bytes):
        quoted = quoted.decode()
    return quoted
