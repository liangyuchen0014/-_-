from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    legal_person = models.CharField(max_length=255, null=True)  # 法人名称
    company = models.CharField(max_length=255, null=True)  # 公司名称
    phone = models.CharField(max_length=255, null=True)  # 电话
    name = models.CharField(max_length=255, null=True)  # 工作人员个人姓名或客户联系人姓名
    description = models.TextField(blank=True, null=True)
    type = models.IntegerField(default=0)  # 0:客户  1:水  2:电  3:机械  -1:管理人员
    is_available = models.IntegerField(default=0)  # 1:空闲  0:不空闲
    head_url = models.TextField(blank=True, null=True)

    def get_info(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'legal_person': self.legal_person,
            'company': self.company,
            'phone': self.phone,
            'description': self.description,
            'type': self.type,
            'is_available': self.is_available,
            'head_url': self.head_url
        }


class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    lease_id = models.ForeignKey('Lease', on_delete=models.DO_NOTHING)  # 租赁信息id
    time = models.CharField(max_length=255, null=True)


class Visitor(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey('User', on_delete=models.DO_NOTHING)  # 客户id
    name = models.CharField(max_length=255, null=True)  # 访客人员姓名
    number = models.CharField(max_length=255, null=True)  # 身份证号码
    visit_time = models.CharField(max_length=255, null=True)  # 到访时间
    phone = models.CharField(max_length=255, null=True)  # 电话
    apply_time = models.CharField(max_length=255, null=True)  # 申请时间


class Wiki(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.TextField(blank=True, null=True)  # 问题描述
    solution = models.TextField(blank=True, null=True)  # 解决方法


class Room(models.Model):
    id = models.AutoField(primary_key=True)
    number = models.CharField(max_length=255, null=True)  # 房间号（四位，如1001）


class Lease(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey('User', on_delete=models.DO_NOTHING)  # 客户id(外键)
    room_id = models.ForeignKey('Room', on_delete=models.DO_NOTHING)  # 房间id(外键)
    start_time = models.CharField(max_length=255, null=True)  # 起租时间
    end_time = models.CharField(max_length=255, null=True)  # 终止时间
    contract_time = models.CharField(max_length=255, null=True)  # 签约时间
