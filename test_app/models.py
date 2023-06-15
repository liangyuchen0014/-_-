from django.contrib.auth.models import AbstractUser
from django.db import models


class User(models.Model):
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


class Client(models.Model):
    id = models.AutoField(primary_key=True)  # id
    legal_person = models.CharField(max_length=255)  # 法人名称
    company = models.CharField(max_length=255)  # 公司名称
    contact_name = models.CharField(max_length=255)  # 联系人姓名
    phone = models.IntegerField(default=0)  # 电话

