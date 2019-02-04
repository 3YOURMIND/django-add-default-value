# flake8: noqa
from .settings import *

CONNECTION_OPTS = {
    'host_is_server': True,
    'unicode_results': True,
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
        "HOST": "localhost",
        "PORT": '1433',
        "PASSWORD": DBPASSWORD,
        "OPTIONS": CONNECTION_OPTS,
    },
    "other": {
        "ENGINE": "sql_server.pyodbc",
        "NAME": DBNAME + "_other",
        "USER": DBUSER,
        "PASSWORD": DBPASSWORD,
        "OPTIONS": CONNECTION_OPTS,
    },
}

SECRET_KEY = "django_tests_secret_key"

# Use a fast hasher to speed up tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

if os.environ.get("ADD_TEST_APP", False):
    INSTALLED_APPS.append("dadv.apps.DadvConfig")
