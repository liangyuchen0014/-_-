from django.contrib.auth.models import AbstractUser
from django.db import models

'''
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
'''


class Client(models.Model):
    id = models.AutoField(primary_key=True)  # id
    legal_person = models.CharField(max_length=255)  # 法人名称
    company = models.CharField(max_length=255)  # 公司名称
    contact_name = models.CharField(max_length=255)  # 联系人姓名
    phone = models.IntegerField(default=0)  # 电话


class Staff(models.Model):
    id = models.AutoField(primary_key=True)  # id
    name = models.CharField(max_length=255)  # 工作人员个人姓名
    phone = models.IntegerField(default=0)  # 电话
    fix_type = models.IntegerField(default=0)  # 0:管理人员  1:水  2:电  3:机械
    is_valiable = models.IntegerField(default=0)  #  0:空闲  1:不空闲