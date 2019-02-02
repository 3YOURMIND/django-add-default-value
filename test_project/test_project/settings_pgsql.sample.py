# flake8: noqa
from .settings import *

DBUSER = os.environ.get("PGUSER", os.environ["USER"])
DBHOST = os.environ.get("PGHOST", "localhost")
DBPORT = None
if not DBHOST.startswith("/"):
    DBPORT = os.environ.get("PGPORT", "5432")
DBNAME = os.environ.get("PGDATABASE", "dadv")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": DBHOST,
        "PORT": DBPORT,
        "NAME": DBNAME,
        "USER": DBUSER,
    },
    "other": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": DBHOST,
        "PORT": DBPORT,
        "NAME": DBNAME + "_other",
        "USER": DBUSER,
    },
}

SECRET_KEY = "django_tests_secret_key"

# Use a fast hasher to speed up tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

if os.environ.get("ADD_TEST_APP", False):
    INSTALLED_APPS.append("dadv.apps.DadvConfig")
