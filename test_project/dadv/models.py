from django.db import models
from datetime import date
from django.utils import timezone


class TestBoolDefault(models.Model):
    id = models.BigAutoField(primary_key=True)
    is_functional = models.BooleanField(default=False)


class TestTextDefault(models.Model):
    id = models.BigAutoField(primary_key=True)
    description = models.TextField(default="No description provided")


class TestHappyPath(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(default="Happy path", max_length=15)
    dob = models.DateField(default=date(1970, 1, 1))
    rebirth = models.DateTimeField(default=timezone.now)
    married = models.DateField(default=date.today)
