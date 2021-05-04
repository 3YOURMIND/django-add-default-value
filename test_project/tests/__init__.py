from __future__ import unicode_literals

import io
import os
import unittest

from django.core.management import call_command
from django.test import TestCase, modify_settings

settings_module = os.environ["DJANGO_SETTINGS_MODULE"]


class MigrateMixin:
    @unittest.skipIf(
        settings_module != "test_project.settings_pgsql",
        "Executing DDL statements while in a transaction on databases that can't perform a "
        "rollback is prohibited.",
    )
    def test_migrate(self):
        """Make sure migrations actually work"""
        # with open(os.devnull, "w") as nothing:
        #    self.assertIsNone(call_command("migrate", "dadv", stdout=nothing))
        try:
            call_command("migrate")
        except Exception:
            self.assertTrue(False, "Migrations failed")
        else:
            self.assertTrue(True, "Migrations succeded")


class CommandOutputMixin:
    def get_command_output(self, cmd, *cmd_args, **cmd_options):
        file_obj = io.StringIO()
        cmd_options.update(stdout=file_obj)
        call_command(cmd, *cmd_args, **cmd_options)
        output = file_obj.getvalue()

        file_obj.close()
        return output


class MigrationsTesterBase(MigrateMixin, CommandOutputMixin):
    bool_match = "ALTER COLUMN \"is_functional\" SET DEFAULT 'False';"
    text_match = (
        'ALTER TABLE "dadv_testtextdefault" ALTER COLUMN "description" '
        "SET DEFAULT 'No description provided';"
    )
    charfield_match = (
        'ALTER TABLE "dadv_testhappypath" ALTER COLUMN "name" '
        "SET DEFAULT 'Happy path'"
    )
    date_match = 'ALTER TABLE "dadv_testhappypath" ALTER COLUMN "dob" SET DEFAULT \'1970-01-01\';'
    current_timestamp_match = (
        'ALTER TABLE "dadv_testhappypath" ALTER COLUMN "rebirth" SET DEFAULT now();'
    )
    current_date_match = (
        'ALTER TABLE "dadv_testhappypath" ALTER COLUMN "married" SET DEFAULT now();'
    )

    custom_column_match = 'ALTER TABLE "dadv_testcustomcolumnname" ALTER COLUMN "custom_field" SET DEFAULT \'False\';'

    def test_bool_default(self):
        actual = self.get_command_output("sqlmigrate", "dadv", "0001")
        self.assertIn(self.bool_match, actual)

    def test_text_default(self):
        """Make sure we can add defaults for text fields"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0002")
        self.assertIn(self.text_match, actual)

    def test_charfield_default(self):
        """Make sure we can add defaults for char fields"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0003")
        self.assertIn(self.charfield_match, actual)

    def test_default_date(self):
        """Make sure temporal values work"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0004")
        self.assertIn(self.date_match, actual)

    def test_current_timestamp(self):
        """Make sure we can provide current timestamps as default"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0004")
        self.assertIn(self.current_timestamp_match, actual)

    def test_current_date(self):
        """Make sure we can provide current dates as default"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0004")
        self.assertIn(self.current_date_match, actual)

    def test_custom_column_name(self):
        """Make sure we can provide current dates as default"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0005")
        self.assertIn(self.custom_column_match, actual)


@unittest.skipUnless(
    settings_module == "test_project.settings_pgsql",
    "PostgreSQL settings file not selected",
)
@modify_settings(INSTALLED_APPS={"append": "dadv.apps.DadvConfig"})
class MigrationsTesterPgSQL(TestCase, MigrationsTesterBase):
    pass


@unittest.skipUnless(
    settings_module == "test_project.settings_crdb",
    "CockroachDB settings file not selected",
)
@modify_settings(INSTALLED_APPS={"append": "dadv.apps.DadvConfig"})
class MigrationsTesterCRDB(TestCase, MigrationsTesterBase):
    bool_match = "Add to field TestBoolDefault.is_functional the default value False"
    text_match = "Add to field TestTextDefault.description the default value No description provided"
    charfield_match = "Add to field TestHappyPath.name the default value Happy path"
    date_match = "Add to field testhappypath.dob the default value 1970-01-01"
    current_timestamp_match = (
        "Add to field testhappypath.rebirth the default value __NOW__"
    )
    current_date_match = (
        "Add to field testhappypath.married the default value __TODAY__"
    )

    custom_column_match = (
        "Add to field TestCustomColumnName.is_functional the default value False"
    )


@unittest.skipUnless(
    settings_module == "test_project.settings_mysql", "MySQL settings file not selected"
)
@modify_settings(INSTALLED_APPS={"append": "dadv.apps.DadvConfig"})
class MigrationsTesterMySQL(TestCase, MigrationsTesterBase):
    bool_match = "ALTER COLUMN `is_functional` SET DEFAULT '0';"
    charfield_match = (
        "ALTER TABLE `dadv_testhappypath` ALTER COLUMN `name` SET DEFAULT 'Happy path';"
    )
    date_match = (
        "ALTER TABLE `dadv_testhappypath` ALTER COLUMN `dob` SET DEFAULT '1970-01-01';"
    )
    current_timestamp_match = (
        "ALTER TABLE `dadv_testhappypath` ALTER COLUMN `rebirth` SET DEFAULT "
        "CURRENT_TIMESTAMP;"
    )

    custom_column_match = "ALTER TABLE `dadv_testcustomcolumnname` ALTER COLUMN `custom_field` SET DEFAULT '0';"

    @unittest.expectedFailure
    def test_text_default(self):
        super(MigrationsTesterMySQL, self).test_text_default()

    @unittest.expectedFailure
    def test_current_date(self):
        super(MigrationsTesterMySQL, self).test_current_date()


@unittest.skipUnless(
    settings_module == "test_project.settings_mssql",
    "Microsoft SQL Server settings file not selected",
)
@modify_settings(INSTALLED_APPS={"append": "dadv.apps.DadvConfig"})
class MigrationsTesterMicrosoftSQL(TestCase, MigrationsTesterBase):
    bool_match = (
        "ALTER TABLE [dadv_testbooldefault] "
        "ADD CONSTRAINT [DADV_TestBoolDefault_is_functional_DEFAULT] "
        "DEFAULT '0' FOR [is_functional];"
    )
    charfield_match = (
        "ALTER TABLE [dadv_testhappypath] ADD CONSTRAINT [DADV_TestHappyPath_name_DEFAULT] "
        "DEFAULT 'Happy path' FOR [name];"
    )
    text_match = (
        "ALTER TABLE [dadv_testtextdefault] ADD CONSTRAINT ["
        "DADV_TestTextDefault_description_DEFAULT] DEFAULT 'No description provided' FOR ["
        "description];"
    )
    date_match = (
        "ALTER TABLE [dadv_testhappypath] "
        "ADD CONSTRAINT [DADV_testhappypath_dob_DEFAULT] DEFAULT '1970-01-01' FOR [dob];"
    )
    current_date_match = (
        "ALTER TABLE [dadv_testhappypath] "
        "ADD CONSTRAINT [DADV_testhappypath_married_DEFAULT] "
        "DEFAULT GETDATE() "
        "FOR [married];"
    )
    current_timestamp_match = (
        "ALTER TABLE [dadv_testhappypath] ADD CONSTRAINT [DADV_testhappypath_rebirth_DEFAULT] "
        "DEFAULT GETDATE() FOR [rebirth];"
    )
