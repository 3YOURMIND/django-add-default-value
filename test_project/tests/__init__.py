from io import StringIO
from django.test import TestCase, modify_settings
from django.core.management import call_command
from unittest import skipUnless
import os


settings_module = os.environ['DJANGO_SETTINGS_MODULE']


@skipUnless(settings_module == 'test_project.settings_pgsql',
            'PostgreSQL settings file not selected')
class MigrationsTesterPostgresql(TestCase):
    @modify_settings(INSTALLED_APPS={'append': 'dadv.apps.DadvConfig'})
    def test_bool_default(self):
        file_obj = StringIO()
        call_command('sqlmigrate', 'dadv', '0001', stdout=file_obj)
        self.assertIn(
            "ALTER COLUMN \"is_functional\" SET DEFAULT 'False';",
            file_obj.getvalue()
        )


@skipUnless(settings_module == 'test_project.settings_mysql',
            'MySQL settings file not selected')
class MigrationsTesterMySQL(TestCase):
    @modify_settings(INSTALLED_APPS={'append': 'dadv.apps.DadvConfig'})
    def test_bool_default(self):
        file_obj = StringIO()
        call_command('sqlmigrate', 'dadv', '0001', stdout=file_obj)
        self.assertIn(
            "ALTER COLUMN `is_functional` SET DEFAULT '0';",
            file_obj.getvalue()
        )
