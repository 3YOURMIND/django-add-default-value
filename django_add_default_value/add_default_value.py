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

from django.db.migrations.operations.base import Operation
from django.db import models, ProgrammingError
from datetime import date, datetime
from django.utils import timezone

NOW = "__NOW__"
TODAY = "__TODAY__"
START = 0
END = 1

NO_MIGRATION_SQL = """
---
--- No migration needed
---
"""


class AddDefaultValue(Operation):
    reversible = True

    def __init__(self, model_name, name, value):
        self.model_name = model_name
        self.name = name
        self.value = value
        self.quotes = {}

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
        if not is_supported_vendor(schema_editor.connection.vendor):
            return NO_MIGRATION_SQL

        self.initialize_vendor_state(schema_editor.connection)

        to_model = to_state.apps.get_model(app_label, self.model_name)
        if not self.can_apply_default(to_model, self.name, schema_editor.connection):
            warnings.warn(
                "You requested a default for a field / database combination "
                "that does not allow one. The default will not be set on: "
                "{model}.{field}.".format(model=to_model.__name__, field=self.name)
            )
            return NO_MIGRATION_SQL

        sql_value, value_quote = self.clean_value(schema_editor.connection, self.value)
        format_kwargs = dict(
            table=to_model._meta.db_table,
            field=self.name,
            value=sql_value,
            value_quote_start=value_quote[START],
            value_quote_end=value_quote[END],
            name_quote_start=self.quotes["name"][START],
            name_quote_end=self.quotes["name"][END],
        )
        if not is_mssql(schema_editor.connection.vendor):
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
        if not is_supported_vendor(schema_editor.connection.vendor):
            return NO_MIGRATION_SQL

        self.initialize_vendor_state(schema_editor.connection)

        to_model = to_state.apps.get_model(app_label, self.model_name)
        if not self.can_apply_default(
            model=to_model, connection=schema_editor.connection
        ):
            return NO_MIGRATION_SQL

        format_kwargs = dict(
            table=to_model._meta.db_table,
            field=self.name,
            name_quote_start=self.quotes["name"][START],
            name_quote_end=self.quotes["name"][END],
        )
        if not is_mssql(schema_editor.connection.vendor):
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

    def initialize_vendor_state(self, connection):
        self.set_quotes(connection.vendor)

    def set_quotes(self, vendor):
        """
        Set the various quotes according to vendor.

        Since we can switch vendor if we have multiple vendors configured for one project, we must
        set them as if everything is unset.

        Right now, we have 4 types and only one type differs between vendors. However, these types
        align with SQL primitives and vendors may change these quotes or more vendors may be
        supported with different quotations. Judge whether this is needed or we can simplify to
        using ``self.name_quotes`` at the end of the year.

        :param vendor: Connection vendor string as provided by the db backend
        """
        if is_postgresql(vendor):
            self.quotes = {
                "value": ("'", "'"),
                "constant": ("", ""),
                "function": ("", ""),
                "name": ('"', '"'),
                "nested_expression": ("(", ")"),
            }
        elif is_mysql(vendor):
            self.quotes = {
                "value": ("'", "'"),
                "constant": ("", ""),
                "function": ("", ""),
                "name": ("`", "`"),
                "nested_expression": ("(", ")"),
            }
        elif is_mssql(vendor):
            self.quotes = {
                "value": ("'", "'"),
                "constant": ("", ""),
                "function": ("", ""),
                "name": ("[", "]"),
                "nested_expression": ("(", ")"),
            }

    def can_apply_default(self, model, connection):
        field = model._meta.get_field(self.name)  # type: models.Field
        if is_text_field(field) and not can_have_default_for_text(connection):
            return False

        if is_temporal_field(field) and not can_apply_temporal_defaults():
            return False

        return True

    def clean_value(self, connection, value):
        """
        Lie, cheat and apply plastic surgery where needed

        This handles the following issues:
        - Only PostgreSQL understands boolean values
        - Temporal values must be translated to strings
        - Strings that match the values for ``NOW`` or ``TODAY`` must be translated to equivalent
          functions if the vendor supports it or strings with a fixed date / time if the vendor
          does not.

        :param connection: database vendor we need to perform operations for
        :param value: the value as provided in the migration
        :return: a 2-tuple containing the new value and the quotation to use
        """
        value, quote, handled = self._clean_boolean(connection, value)
        if handled:
            return value, quote

        value, quote, handled = self._clean_temporal(connection, value)
        if handled:
            return value, quote

        value, quote, handled = self._clean_temporal_constants(connection, value)
        if handled:
            return value, quote

        return value, self.quotes["value"]

    def mssql_constraint_name(self):
        return "DADV_{model}_{field}_DEFAULT".format(
            model=self.model_name, field=self.name
        )

    def _clean_boolean(self, connection, value):
        if isinstance(value, bool):
            if not is_postgresql(connection.vendor):
                value = 1 if value else 0

            return value, self.quotes["value"], True
        return value, self.quotes["value"], False

    def _clean_temporal(self, connection, value):
        if isinstance(value, date):
            return value.isoformat(), self.quotes["value"], True

        if isinstance(value, datetime):
            if is_postgresql(connection.vendor):
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

    def _clean_temporal_constants(self, connection, value):
        if value == NOW or value == TODAY:
            if is_postgresql(connection.vendor):
                return "now()", self.quotes["function"], True
            elif is_mssql(connection.vendor):
                return "GETDATE()", self.quotes["function"], True
            # https://stackoverflow.com/a/20461045/10000573
            elif value == NOW and is_mysql(connection.vendor):
                return "CURRENT_TIMESTAMP", self.quotes["nested_expression"], True
            elif value == TODAY and (
                is_mysql_8013_or_better(connection)
                or is_mariadb_1012_or_better(connection)
            ):
                return "CURRENT_DATE", self.quotes["nested_expression"], True
            elif value == TODAY and is_mysql(connection.vendor):
                raise ProgrammingError(
                    "Method `can_apply_default` should have prevented code from reaching this"
                )

        return value, self.quotes["value"], False

    def _clean_text_blob(self, connection, value):
        """
        Using MySQL we need to wrap our string with value quotes and then surround them with
        expression parentheses.
        """
        if (
            is_mysql(connection.vendor)
            and can_have_default_for_text(connection)
            and is_text_field(self.model_name, self.name)
        ):
            value = "{quote_start}{value}{quote_end}".format(
                quote_start=self.quotes["value"][START],
                value=value,
                quote_end=self.quotes["value"][END],
            )
            return value, self.quotes["nested_expression"], True

        return value, self.quotes["value"], False


def can_have_default_for_text(connection):
    """
    MySQL has not allowed DEFAULT for BLOB and TEXT fields since the
    beginning of time, but it is changing:

        Before MariaDB 10.2.1, BLOB and TEXT columns could not be assigned
        a DEFAULT value. This restriction was lifted in MariaDB 10.2.1.

    Oracle implemented defaults in 8.0.13, quoting the `documentation
    <https://dev.mysql.com/doc/refman/8.0/en/data-type-defaults.html>`_:

        The BLOB, TEXT, GEOMETRY, and JSON data types can be assigned a default value only
        if the value is written as an expression, even if the expression value is a literal.

    :param connection: The DB connection, aka `schema_editor.connection`
    :type connection: django.db.backends.base.base.BaseDatabaseWrapper
    :return: A boolean indicating we support default values for text
             fields.
    :rtype: bool
    """
    if is_postgresql(connection.vendor) or is_mssql(connection.vendor):
        return True

    if not hasattr(connection, "mysql_version") or not callable(
        getattr(connection, "mysql_version", None)
    ):
        return False

    return is_mysql_8013_or_better(connection) or is_mariadb_1012_or_better(connection)


def is_text_field(field):
    return isinstance(field, (models.TextField, models.BinaryField))


def is_temporal_field(field):
    return isinstance(field, (models.DateField, models.DateTimeField, models.TimeField))


def is_supported_vendor(vendor):
    return is_postgresql(vendor) or is_mysql(vendor) or is_mssql(vendor)


def can_apply_temporal_defaults(connection):
    return (
        not is_mysql(connection.vendor)
        or is_mysql_8013_or_better(connection)
        or is_mariadb_1012_or_better(connection)
    )


def is_mysql_8013_or_better(connection):
    if (
        not is_mariadb(connection.vendor)
        and is_mysql(connection.vendor)
        and callable(getattr(connection, "mysql_version"))
    ):
        # noinspection PyUnresolvedReferences
        major, minor, patch = connection.mysql_version()
        return major > 7 and minor >= 0 and patch > 12

    return False


def is_mariadb_1012_or_better(connection):
    if is_mariadb(connection.vendor) and callable(
        getattr(connection, "mysql_version", None)
    ):
        # noinspection PyUnresolvedReferences
        major, minor, patch = connection.mysql_version()
        return major > 9 and minor > 1 and patch > 0

    return False


def is_mysql(vendor):
    return vendor.startswith("mysql")


def is_postgresql(vendor):
    return vendor.startswith("postgre")


def is_mssql(vendor):
    return vendor.startswith("microsoft")


def is_mariadb(connection):
    if hasattr(connection, "mysql_is_mariadb"):
        return connection.mysql_is_mariadb()
    return False
