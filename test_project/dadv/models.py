from django.db import models


class TestBoolDefault(models.Model):
    id = models.BigAutoField(primary_key=True)
    is_functional = models.BooleanField(default=False)
