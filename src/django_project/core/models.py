from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your models here.
class ShortenedURL(models.Model):
    alias = models.TextField()
    url = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL,)
    inserted_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True,)

