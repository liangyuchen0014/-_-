import random
import time
from datetime import datetime

from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from test_app.message import send_sms_code
from test_app.models import *


@csrf_exempt
def register(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    email = request.POST.get('email')
    password = request.POST.get('password')
    # all() 函数用于判断给定的可迭代参数 iterable 中的所有元素是否都为 TRUE，如果是返回 True，否则返回 False。
    if not all([password, email]):
        return JsonResponse({'errno': 1002, 'msg': "参数不完整"})
    usr = User.objects.filter(username=email).first()
    if usr:
        return JsonResponse({'errno': 1003, 'msg': "该邮箱已注册"})
    new_user = User.objects.create_user(username=email, password=password, email=email)
    return JsonResponse({'errno': 0, 'msg': "注册成功", 'data': new_user.get_info()})


@csrf_exempt
def user_login(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    email = request.POST.get('email')
    password = request.POST.get('password')
    if not all([email, password]):
        return JsonResponse({'errno': 1003, 'msg': "参数不完整"})
    # 验证登录
    # authenticate() 函数接收两个参数，邮箱 email 和 密码 password，然后在数据库中验证。
    # 如果验证通过，返回一个User。对如果验证不通过，authenticate()返回 None。
    is_login = authenticate(username=email, password=password)
    if is_login is None:
        return JsonResponse({'errno': 1005, 'message': '邮箱或密码错误'})
    login(request, is_login)
    # 生成token
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
    payload = jwt_payload_handler(is_login)
    token = jwt_encode_handler(payload)
    # 解析token
    jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
    r = jwt_decode_handler(token)
    user_id = r['user_id']
    usr = User.objects.filter(user_id=user_id).first()
    return JsonResponse(
        {'errno': 0, 'msg': "登录成功", 'data': {'user_id': user_id, 'token': token, 'email': email, 'type': usr.type}})


def decode_token(token):
    jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
    try:
        r = jwt_decode_handler(token)
    except:
        return -1
    if r['exp'] < time.time():
        return -1
    return r['user_id']


@csrf_exempt
def change_user_info(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    t = request.POST.get('type')
    content = request.POST.get('content')
    if not all([token, t, content]):
        return JsonResponse({'errno': 1003, 'msg': "参数不完整"})
    usr = User.objects.filter(user_id=user_id).first()
    if not usr:
        return JsonResponse({'errno': 1002, 'msg': "用户不存在"})
    if t not in ['0', '1', '2']:
        return JsonResponse({'errno': 1004, 'msg': "类型错误"})
    t = int(t)
    if t == 0:
        usr.username = content
    elif t == 1:
        usr.description = content
    elif t == 2:
        name = str(time.time()) + 'qwerty'
        new_user = User.objects.create_user(username=name, password=content)
        usr.password = new_user.password
        new_user.delete()
    usr.save()
    return JsonResponse({'errno': 0, 'msg': "修改成功"})

#获取用户信息
@csrf_exempt
def get_user_info(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    usr = User.objects.filter(user_id=user_id).first()
    if not usr:
        return JsonResponse({'errno': 1002, 'msg': "用户不存在"})
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': usr.get_info()})


# 忘记密码
@csrf_exempt
def forget_password(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    email = request.POST.get('email')
    rand_code = request.POST.get('rand_code')
    new_password = request.POST.get('new_password')
    if not all([email, rand_code, new_password]):
        return JsonResponse({'errno': 1003, 'msg': "参数不完整"})
    usr = User.objects.filter(email=email).first()
    if not usr:
        return JsonResponse({'errno': 1002, 'msg': "用户不存在"})
    redis_default = get_redis_connection('default')
    sms_code = redis_default.get(email)
    sms_code = sms_code.decode()
    if rand_code != sms_code:
        return JsonResponse({'errno': 1004, 'msg': "验证码错误"})
    usr.set_password(new_password)
    usr.save()
    return JsonResponse({'errno': 0, 'msg': "修改成功"})


# 发送邮箱验证码
@csrf_exempt
def send_email_code(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    email = request.POST.get('email')
    if not all([email]):
        return JsonResponse({'errno': 1003, 'msg': "参数不完整"})
    usr = User.objects.filter(email=email).first()
    if not usr:
        return JsonResponse({'errno': 1002, 'msg': "用户不存在"})
    # 生成邮箱验证码
    sms_code = '%06d' % random.randint(0, 999999)
    redis_default = get_redis_connection('default')
    redis_default.set(email, sms_code, 60 * 5)
    status = send_sms_code(email, sms_code)
    if not status:
        return JsonResponse({'errno': 1004, 'msg': "验证码发送失败"})
    return JsonResponse({'errno': 0, 'msg': "验证码发送成功"})

#新增客户信息
@csrf_exempt
def addNewClient(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    else:
        new_name = request.POST.get('new_name')
        new_phone = request.POST.get('new_phone')
        new_company = request.POST.get('new_company')
        new_legal =request.POST.get('new_legal')
        # 在这里进行新增客户信息的操作
        usr = User.objects.create_user(username=new_name, phone=new_phone, legal_person=new_legal,company=new_company)
        usr.save()
        return JsonResponse({'status': 'success'})



#删除客户信息
@csrf_exempt
def deleteClientInfo(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    else:
        id = request.POST.get('id')
        usr = User.objects.filter(user_id=id).delete()
        return JsonResponse({'status': 'success'})

# 客户报修
@csrf_exempt
def repairReport(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    user = User.objects.filter(user_id=user_id).first()
    name = request.POST.get('name')
    phone = request.POST.get('phone')
    room_id = request.POST.get('rid')
    room = Room.objects.filter(id=room_id).first()
    if not room:
        return JsonResponse({'errno': 1005, 'msg': "房间不存在"})
    r_type = request.POST.get('type')
    description = request.POST.get('description')
    repair_time = time.time()
    if not all([user_id, name, phone, room_id, r_type, description, repair_time]):
        return JsonResponse({'errno': 1003, 'msg': "参数不完整"})
    repair_form = RepairForm.objects.filter(room_id=room_id)
    for form in repair_form:
        if form.status == 0 or form.status == 1:
            return JsonResponse({'errno': 1004, 'msg': "该房间已报修"})
    new_repair_form = RepairForm.objects.create(company_id=user, company_name=user.name, contact_name=name,
                                                contact_phone=phone, room_id=room,
                                                type=r_type, description=description, repair_time=repair_time)
    return JsonResponse({'errno': 0, 'msg': "报修成功"})


# 客户查看报修申请记录
@csrf_exempt
def myRepair(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    user = User.objects.filter(user_id=user_id).first()
    repair_form = RepairForm.objects.filter(company_id=user)
    data = []
    for form in repair_form:
        res = form.get_info()
        ret = {
            'wid': res['id'],
            'rid': res['room_id'],
            'type': res['type'],
            'repair_time': res['repair_time'],
            'maintain_time': datetime.fromtimestamp(res['maintain_time']).strftime('%Y-%m-%d %H:%M:%S'),
            'status': res['status'],
            'maintainer_name': res['maintainer_name'],
            'maintainer_phone': res['maintainer_phone'],
            'description': res['description'],
        }
        data.append(ret)
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': data})


# 维修工查看维修任务列表
@csrf_exempt
def repairService(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    user = User.objects.filter(user_id=user_id).first()
    repair_form = RepairForm.objects.filter(maintainer_id=user_id)
    data = []
    for form in repair_form:
        res = form.get_info()
        ret = {
            'wid': res['id'],
            'repair_time': datetime.fromtimestamp(res['repair_time']).strftime('%Y-%m-%d %H:%M:%S'),
            'status': res['status']
        }
        data.append(ret)
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': data})


# 维修工查看维修任务详情
@csrf_exempt
def repairDetail(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})

    wid = request.POST.get('wid')
    repair_form = RepairForm.objects.filter(id=wid).first()
    if not repair_form:
        return JsonResponse({'errno': 1003, 'msg': "报修单不存在"})
    res = repair_form.get_info()
    ret = {
        'rid': res['room_id'],
        'type': res['type'],
        'description': res['description'],
        'company_name': res['company_name'],
        'contact_name': res['contact_name'],
        'contact_phone': res['contact_phone'],
        'repair_time': datetime.fromtimestamp(res['repair_time']).strftime('%Y-%m-%d %H:%M:%S'),
        'status': res['status'],
    }
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': ret})


'''
# 维修工进行维修
@csrf_exempt
def repairStart(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    user_id = request.POST.get('user_id')
    user = User.objects.filter(user_id=user_id).first()
    if not user:
        return JsonResponse({'errno': 1002, 'msg': "用户不存在"})
    wid = request.POST.get('wid')
    repair_form = RepairForm.objects.filter(id=wid).first()
    if not repair_form:
        return JsonResponse({'errno': 1003, 'msg': "报修单不存在"})
    if repair_form.status != 0:
        return JsonResponse({'errno': 1004, 'msg': "报修单状态错误"})
    repair_form.status = 1
    repair_form.save()
    return JsonResponse({'errno': 0, 'msg': "维修成功"})
'''


# 维修工完成维修，提交记录
@csrf_exempt
def repairComplete(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})

    solve_time = request.POST.get('solve_time')
    solution = request.POST.get('solution')
    user = User.objects.filter(user_id=user_id).first()
    if not user:
        return JsonResponse({'errno': 1002, 'msg': "用户不存在"})
    solver_name = user.name
    solver_id = user_id
    wid = request.POST.get('wid')
    repair_form = RepairForm.objects.filter(id=wid).first()
    if not repair_form:
        return JsonResponse({'errno': 1003, 'msg': "报修单不存在"})
    if repair_form.status != 1:
        return JsonResponse({'errno': 1004, 'msg': "报修单状态错误"})

    dt = datetime.strptime(solve_time, '%Y-%m-%d %H:%M:%S')
    solve_time = dt.timestamp()

    repair_form.solver_name = solver_name
    repair_form.solver_id = solver_id
    repair_form.solve_time = solve_time
    repair_form.solution = solution
    repair_form.status = 2
    repair_form.save()
    return JsonResponse({'errno': 0, 'msg': "提交成功"})

#获取某一楼层所有房间状态
@csrf_exempt
def get_room_status(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    level = request.POST.get('level')
    if not level:
        return JsonResponse({'errno': 1002, 'msg': "参数不完整"})
    now = int(time.time())
    rooms = Room.objects.filter(level=level).all()
    r = []
    for room in rooms:
        t = {'roomNo': room.id}
        lease = Lease.objects.filter(room_id=room).filter(start_time__lte=now).filter(end_time__gte=now).first()
        if not lease:
            t['isRented'] = False
            t['userID'] = None
            t['userName'] = None
            t['startTime'] = None
            t['endTime'] = None
            t['Company'] = None
        else:
            t['isRented'] = True
            t['userID'] = lease.user_id_id
            t['userName'] = lease.user_id.name
            t['startTime'] = datetime.fromtimestamp(lease.start_time).strftime('%Y.%m.%d')
            t['endTime'] = datetime.fromtimestamp(lease.end_time).strftime('%Y.%m.%d')
            t['Company'] = lease.user_id.company
        r.append(t)
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': r})


# 获取客户信息
@csrf_exempt
def get_client_info(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    clients = []
    client = User.objects.filter(type=0).all()
    for c in client:
        rooms = Lease.objects.filter(user_id=c.user_id)
        room_info = []
        payment = []  # 需要修改数据库设计
        for r in rooms:
            tmp = {
                'id': r.room_id_id,
                'start_year': datetime.fromtimestamp(r.start_time).strftime('%Y.%m.%d'),
                'end_year': datetime.fromtimestamp(r.end_time).strftime('%Y.%m.%d'),
                'contract_time': datetime.fromtimestamp(r.contract_time).strftime('%Y.%m.%d')
            }
            room_info.append(tmp)
            payments = Payment.objects.filter(lease_id=r.id).all()
            for p in payments:
                if not p.time:
                    is_paid = False
                else:
                    is_paid = True
                tmp = {
                    'year': p.year,
                    'ispaid': is_paid,
                    'pay_time': p.time
                }
                payment.append(tmp)

        ret = {
            'legal_person': c.legal_person,
            'company': c.company,
            'name': c.name,
            'phone': c.phone,
            'room': room_info,
            'payment': payment,
            'id': c.user_id
        }
        clients.append(ret)
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'clients': clients})


# 修改客户信息
@csrf_exempt
def change_client_info(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    user_id = request.POST.get('id')
    new_name = request.POST.get('new_name')
    new_phone = request.POST.get('new_phone')
    new_company = request.POST.get('new_company')
    new_legal = request.POST.get('new_legal')
    client = User.objects.filter(user_id=user_id).first()
    client.name = new_name
    client.phone = new_phone
    client.company = new_company
    client.legal_person = new_legal
    client.save()
    return JsonResponse({'errno': 0, 'msg': "修改成功"})


# 管理员设置维修工
@csrf_exempt
def setMaintainer(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    user = User.objects.filter(user_id=user_id).first()
    if not user:
        return JsonResponse({'errno': 1002, 'msg': "用户不存在"})
    form_id = request.POST.get('form_id')
    repair_form = RepairForm.objects.filter(id=form_id).first()
    if not repair_form:
        return JsonResponse({'errno': 1003, 'msg': "报修单不存在"})
    if repair_form.status != 0:
        return JsonResponse({'errno': 1004, 'msg': "报修单状态错误"})

    maintain_time = request.POST.get('maintain_time')
    maintainer_name = request.POST.get('maintainer_name')
    maintainer_id = request.POST.get('maintainer_id')
    maintainer_phone = request.POST.get('maintainer_phone')
    # 将时间字符串转换为时间戳
    dt = datetime.strptime(maintain_time, '%Y-%m-%d %H:%M:%S')
    maintain_time = dt.timestamp()

    repair_form.maintain_time = maintain_time
    repair_form.maintainer_name = maintainer_name
    repair_form.maintainer_id = maintainer_id
    repair_form.maintainer_phone = maintainer_phone
    repair_form.feedback_time = time.time()
    repair_form.status = 1
    repair_form.save()
    return JsonResponse({'errno': 0, 'msg': "设置成功"})


# 管理员查看维修单列表
@csrf_exempt
def repairList(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    repair_form = RepairForm.objects.all()
    data = []
    for form in repair_form:
        res = form.get_info()
        ret = {
            'form_id': res['id'],
            'user_id': res['company_id'],
            'room_id': res['room_id'],
            'status': res['status'],
            'repair_time': datetime.fromtimestamp(res['repair_time']).strftime('%Y-%m-%d %H:%M:%S')
        }
        data.append(ret)
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': data})


@csrf_exempt
def save_lease(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    user_id = request.POST.get('id')
    room_id = request.POST.get('room_id')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    sign_time = request.POST.get('sign_time')
    if not all([token, user_id, room_id, start_time, end_time]):
        return JsonResponse({'errno': 1002, 'msg': "参数不完整"})
    admin_id = decode_token(token)
    if admin_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    admin = User.objects.filter(user_id=admin_id).first()
    if not admin:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    if admin.type != -1:
        return JsonResponse({'errno': 1005, 'msg': "用户无权限"})
    usr = User.objects.filter(user_id=user_id).first()
    if not usr:
        return JsonResponse({'errno': 1004, 'msg': "用户不存在"})
    room = Room.objects.filter(id=room_id).first()
    if not room:
        return JsonResponse({'errno': 1003, 'msg': "房间不存在"})
    lease = Lease.objects.filter(room_id=room).first()
    if lease:
        lease.start_time = start_time
        lease.end_time = end_time
        lease.contract_time = sign_time
        lease.user_id = usr
        lease.save()
    else:
        Lease.objects.create(start_time=start_time, end_time=end_time, contract_time=sign_time, room_id=room,
                             user_id=usr)
    return JsonResponse({'errno': 0, 'msg': "保存成功"})


@csrf_exempt
def del_lease(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    room_id = request.POST.get('room_id')
    if not all([token, room_id]):
        return JsonResponse({'errno': 1002, 'msg': "参数不完整"})
    admin_id = decode_token(token)
    if admin_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    admin = User.objects.filter(user_id=admin_id).first()
    if not admin:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    if admin.type != -1:
        return JsonResponse({'errno': 1005, 'msg': "用户无权限"})
    room = Room.objects.filter(id=room_id).first()
    if not room:
        return JsonResponse({'errno': 1003, 'msg': "房间不存在"})
    lease = Lease.objects.filter(room_id=room).first()
    if not lease:
        return JsonResponse({'errno': 1006, 'msg': "合同不存在"})
    lease.delete()
    return JsonResponse({'errno': 0, 'msg': "删除成功"})


@csrf_exempt
def get_worker(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    page = int(request.POST.get('page'))
    num = int(request.POST.get('numInOnePage'))
    if not all([token, page, num]):
        return JsonResponse({'errno': 1002, 'msg': "参数不完整"})
    admin_id = decode_token(token)
    if admin_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    admin = User.objects.filter(user_id=admin_id).first()
    if not admin:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    if admin.type != -1:
        return JsonResponse({'errno': 1005, 'msg': "用户无权限"})
    workers = User.objects.filter(type__in=[-1, 1, 2, 3]).all()[(page - 1) * num: page * num]
    r = []
    for worker in workers:
        r.append({'name': worker.name, 'tel': worker.phone, 'job': worker.post, 'isMaintainer': worker.type != -1,
                  'category': worker.type, 'isAvailable': worker.is_available})
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': r})
