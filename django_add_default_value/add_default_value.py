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

    def state_forwards(self, app_label, state):
        """
        Take the state from the previous migration, and mutate it
        so that it matches what this migration would perform.
        """
        # Nothing to do
        # because the field should have the default setted anyway
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

    def database_forwards(
        self, app_label, schema_editor, from_state, to_state
    ):
        """
        Perform the mutation on the database schema in the normal
        (forwards) direction.
        """
        if not self.is_correct_vendor(schema_editor.connection.vendor):
            return

        self.value = self.clean_value(schema_editor.connection.vendor,
                                      self.value)

        to_model = to_state.apps.get_model(app_label, self.model_name)
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
        self.value = self.clean_value(schema_editor.connection.vendor,
                                      self.value)

        to_model = to_state.apps.get_model(app_label, self.model_name)
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
