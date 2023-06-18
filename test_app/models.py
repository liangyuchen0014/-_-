from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    legal_person = models.CharField(max_length=255, null=True)  # 法人名称
    company = models.CharField(max_length=255, null=True)  # 公司名称
    phone = models.CharField(max_length=255, null=True)  # 电话
    name = models.CharField(max_length=255, null=True)  # 工作人员个人姓名或客户联系人姓名
    description = models.TextField(blank=True, null=True)
    post = models.CharField(max_length=255, null=True)  # 岗位
    type = models.IntegerField(default=0)  # 0:客户  1:水  2:电  3:机械  -1:管理人员
    is_available = models.IntegerField(default=0)  # 0:不空闲  1:空闲
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
            'post': self.post,
            'type': self.type,
            'is_available': self.is_available,
            'head_url': self.head_url
        }


class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    lease_id = models.ForeignKey('Lease', on_delete=models.DO_NOTHING, null=True)  # 租赁信息id
    time = models.BigIntegerField(null=True)


class Visitor(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey('User', on_delete=models.DO_NOTHING, null=True)  # 客户id
    name = models.CharField(max_length=255, null=True)  # 访客人员姓名
    number = models.CharField(max_length=255, null=True)  # 身份证号码
    visit_time = models.BigIntegerField(null=True)  # 到访时间
    phone = models.CharField(max_length=255, null=True)  # 电话
    apply_time = models.BigIntegerField(null=True)  # 申请时间


class Wiki(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.TextField(blank=True, null=True)  # 问题描述
    solution = models.TextField(blank=True, null=True)  # 解决方法


class Room(models.Model):
    id = models.AutoField(primary_key=True)
    number = models.CharField(max_length=255, null=True)  # 房间号（四位，如1001）
    level = models.CharField(max_length=255, null=True)


class Lease(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey('User', on_delete=models.DO_NOTHING, null=True)  # 客户id(外键)
    room_id = models.ForeignKey('Room', on_delete=models.DO_NOTHING, null=True)  # 房间id(外键)
    room_number = models.CharField(max_length=255, null=True)  # 房间号（四位，如1001）
    start_time = models.BigIntegerField(null=True)  # 起租时间
    end_time = models.BigIntegerField(null=True)  # 终止时间
    contract_time = models.BigIntegerField(null=True)  # 签约时间


class RepairForm(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.TextField(blank=True, null=True)  # 问题描述
    type = models.IntegerField(default=0)  # 问题类型 1:水  2:电  3:机械  4:其他
    repair_time = models.BigIntegerField(null=True)  # 报修时间
    room_number = models.CharField(max_length=255, null=True)  # 房间号
    room_id = models.ForeignKey('Room', on_delete=models.DO_NOTHING, null=True)  # 房间id(外键)
    company_name = models.CharField(max_length=255, null=True)  # 报修公司名称
    company_id = models.ForeignKey('User', on_delete=models.DO_NOTHING, null=True)  # 报修公司id(外键)
    contact_name = models.CharField(max_length=255, null=True)  # 报修联系人姓名
    contact_phone = models.CharField(max_length=255, null=True)  # 报修联系人电话
    maintain_time = models.BigIntegerField(null=True)  # 上门维修时间
    maintainer_name = models.CharField(max_length=255, null=True)  # 维修人员姓名
    maintainer_id = models.CharField(max_length=255, null=True)  # 维修人员id
    maintainer_phone = models.CharField(max_length=255, null=True)  # 维修人员电话
    feedback_time = models.BigIntegerField(null=True)  # 反馈时间
    solution = models.TextField(blank=True, null=True)  # 解决方法
    solve_time = models.BigIntegerField(null=True)  # 解决时间
    solver_name = models.CharField(max_length=255, null=True)  # 解决人员姓名
    solver_id = models.CharField(max_length=255, null=True)  # 解决人员id
    status = models.IntegerField(default=0)  # 0-未处理 1-进行中 2-已完成

    def get_info(self):
        return {
            'id': self.id,
            'description': self.description,
            'type': self.type,
            'repair_time': self.repair_time,
            'room_number': self.room_number,
            'room_id': self.room_id,
            'company_name': self.company_name,
            'company_id': self.company_id,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'maintain_time': self.maintain_time,
            'maintainer_name': self.maintainer_name,
            'maintainer_id': self.maintainer_id,
            'maintainer_phone': self.maintainer_phone,
            'feedback_time': self.feedback_time,
            'solution': self.solution,
            'solve_time': self.solve_time,
            'solver_name': self.solver_name,
            'solver_id': self.solver_id,
            'status': self.status
        }