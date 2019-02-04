from __future__ import unicode_literals

import os
import unittest

from django.core.management import call_command
from django.test import TestCase, modify_settings
from io import StringIO

settings_module = os.environ["DJANGO_SETTINGS_MODULE"]


class MigrateMixin:
    # @unittest.skip
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
        file_obj = StringIO()
        cmd_options.update(stdout=file_obj)
        call_command(cmd, *cmd_args, **cmd_options)
        output = file_obj.getvalue()

        file_obj.close()
        return output


class MigrationsTesterBase(MigrateMixin, CommandOutputMixin):
    bool_match = "ALTER COLUMN \"is_functional\" SET DEFAULT 'False';"
    current_date_match = (
        'ALTER TABLE dadv_testhappypath ALTER COLUMN "married" SET DEFAULT now();'
    )

    def test_bool_default(self):
        actual = self.get_command_output("sqlmigrate", "dadv", "0001")
        self.assertIn(self.bool_match, actual)

    def test_text_default(self):
        """Make sure we can add defaults for text fields"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0002")
        self.assertIn(
            "ALTER TABLE \"dadv_testtextdefault\" ALTER COLUMN "
            "\"description\" SET DEFAULT 'No description provided';",
            actual,
        )

    def test_charfield_default(self):
        """Make sure we can add defaults for char fields"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0003")
        self.assertIn(
            'ALTER TABLE "dadv_testhappypath" ALTER COLUMN "name" SET DEFAULT \'Happy '
            "path'",
            actual,
        )

    def test_default_date(self):
        """Make sure temporal values work"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0004")
        self.assertIn(
            'ALTER TABLE "dadv_testhappypath" ALTER COLUMN "dob" SET '
            "DEFAULT '1970-01-01';",
            actual,
        )

    def test_current_timestamp(self):
        """Make sure we can provide current timestamps as default"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0004")
        self.assertIn(
            'ALTER TABLE "dadv_testhappypath" ALTER COLUMN "rebirth" SET DEFAULT '
            "now();",
            actual,
            "We should be using the now() function without quotes.",
        )

    def test_current_date(self):
        """Make sure we can provide current dates as default"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0004")
        self.assertIn(self.current_date_match, actual)


@unittest.skipUnless(
    settings_module == "test_project.settings_pgsql",
    "PostgreSQL settings file not selected",
)
@modify_settings(INSTALLED_APPS={"append": "dadv.apps.DadvConfig"})
class MigrationsTesterPgSQL(TestCase, MigrationsTesterBase):
    pass


@unittest.skipUnless(
    settings_module == "test_project.settings_mysql", "MySQL settings file not selected"
)
@modify_settings(INSTALLED_APPS={"append": "dadv.apps.DadvConfig"})
class MigrationsTesterMySQL(TestCase, MigrationsTesterBase):
    bool_match = "ALTER COLUMN `is_functional` SET DEFAULT '0';"
    current_date_match = (
        'ALTER TABLE `dadv_testhappypath` ALTER COLUMN `married` SET DEFAULT '
        'CURRENT_DATE;'
    )
