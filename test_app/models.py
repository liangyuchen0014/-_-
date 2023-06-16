from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    legal_person = models.CharField(max_length=255, null=True)  # 法人名称
    company = models.CharField(max_length=255, null=True)  # 公司名称
    contact_name = models.CharField(max_length=255, null=True)  # 联系人姓名
    phone = models.CharField(max_length=255, null=True)  # 电话
    name = models.CharField(max_length=255)  # 工作人员个人姓名
    description = models.TextField(blank=True, null=True)
    type = models.IntegerField(default=0)  # 0:客户  1:水  2:电  3:机械  4:管理人员
    is_available = models.IntegerField(default=0)  # 0:空闲  1:不空闲
    head_url = models.TextField(blank=True, null=True)

    def get_info(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'description': self.description,
            'type': self.type,
            'head_url': self.head_url
        }
