from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    description = models.TextField(blank=True, null=True)
    state = models.IntegerField(default=0)
    head_url = models.TextField(blank=True, null=True)

    def get_info(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'description': self.description,
            'state': self.state,
            'head_url': self.head_url
        }
