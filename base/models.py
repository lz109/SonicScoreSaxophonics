from django.db import models
from django.contrib.auth.models import User

class CustomUser(models.Model):
    userId = models.IntegerField(default=0)
    practice_count = models.IntegerField(default=0)
    total_practice_count = models.IntegerField(default=0)
    

