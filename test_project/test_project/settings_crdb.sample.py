# flake8: noqa
from .settings import *

DBUSER = os.environ.get("CRDB_USER", "root")
DBHOST = os.environ.get("CRDB_HOST", "localhost")
DBPORT = None
if not DBHOST.startswith("/"):
    DBPORT = os.environ.get("CRDB_PORT", "26257")
DBNAME = os.environ.get("CRDB_DATABASE", "defaultdb")

DATABASES = {
    "default": {
        "ENGINE": "django_cockroachdb",
        "NAME": DBNAME,
        "HOST": DBHOST,
        "PORT": DBPORT,
        "USER": DBUSER,
    },
}

SECRET_KEY = "django_tests_secret_key"

# Use a fast hasher to speed up tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

if os.environ.get("ADD_TEST_APP", False):
    INSTALLED_APPS.append("dadv.apps.DadvConfig")
