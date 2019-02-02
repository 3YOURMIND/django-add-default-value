# flake8: noqa
from .settings import *

OPTIONS_FILE = os.path.join(os.environ["HOME"], ".my.cnf")
DBNAME = os.environ.get("MYSQL_DBNAME", "dadv")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": DBNAME,
        "OPTIONS": {"read_default_file": OPTIONS_FILE},
    },
    "other": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": DBNAME + "_other",
        "OPTIONS": {"read_default_file": OPTIONS_FILE},
    },
}

SECRET_KEY = "django_tests_secret_key"

# Use a fast hasher to speed up tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

if os.environ.get("ADD_TEST_APP", False):
    INSTALLED_APPS.append("dadv.apps.DadvConfig")
