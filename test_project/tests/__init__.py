from __future__ import unicode_literals

import os
import unittest

from django.core.management import call_command
from django.test import TestCase, modify_settings
from django.utils.six import StringIO

settings_module = os.environ["DJANGO_SETTINGS_MODULE"]


class MigrateMixin:
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
        return file_obj.getvalue()


class MigrationsTesterBase(MigrateMixin, CommandOutputMixin):
    def test_bool_default(self):
        actual = self.get_command_output("sqlmigrate", "dadv", "0001")
        self.assertIn("ALTER COLUMN \"is_functional\" SET DEFAULT 'False';", actual)

    def test_text_default(self):
        """Make sure we can add defaults for text fields"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0002")
        self.assertIn(
            "ALTER TABLE dadv_testtextdefault ALTER COLUMN "
            "\"description\" SET DEFAULT 'No description provided';",
            actual,
        )

    def test_charfield_default(self):
        """Make sure we can add defaults for char fields"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0003")
        self.assertIn(
            'ALTER TABLE dadv_testhappypath ALTER COLUMN "name" SET DEFAULT \'Happy '
            "path'",
            actual,
        )

    def test_default_date(self):
        """Make sure temporal values work"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0004")
        self.assertIn(
            'ALTER TABLE dadv_testhappypath ALTER COLUMN "dob" SET '
            "DEFAULT '1970-01-01';",
            actual,
        )

    @unittest.expectedFailure
    def test_current_timestamp(self):
        """Make sure we can do provide current timestamps"""
        actual = self.get_command_output("sqlmigrate", "dadv", "0004")
        self.assertIn(
            'ALTER TABLE dadv_testhappypath ALTER COLUMN "rebirth" SET DEFAULT '
            "CURRENT_TIMESTAMP;",
            actual,
            "There should be no quotes around CURRENT_TIMESTAMP",
        )


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
    pass
