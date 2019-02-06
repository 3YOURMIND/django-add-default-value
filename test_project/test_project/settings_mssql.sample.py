# flake8: noqa
from .settings import *

CONNECTION_OPTIONS = {
    'driver': 'FreeTDS',
    'host_is_server': True,
    'unicode_results': True,
    # See: https://github.com/michiya/django-pyodbc-azure/issues/185#issuecomment-460007327
    'extra_params': 'tds_version=8.0',
}
DBNAME = os.environ.get("MSSQL_DBNAME", "dadv")
DBUSER = os.environ.get("MSSQL_DBUSER", "SA")
DBPASSWORD = os.environ.get("MSSQL_DBPASSWORD", "|8Chars|")

DATABASES = {
    "default": {
        "ENGINE": "sql_server.pyodbc",
        "NAME": DBNAME,
        "USER": DBUSER,
        "PASSWORD": DBPASSWORD,
        "HOST": "localhost",
        "PORT": '1433',
        "OPTIONS": CONNECTION_OPTIONS,
    },
}

SECRET_KEY = "django_tests_secret_key"

# Use a fast hasher to speed up tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

if os.environ.get("ADD_TEST_APP", False):
    INSTALLED_APPS.append("dadv.apps.DadvConfig")
