import json
import time
from datetime import datetime, timedelta

from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from test_app.message import *
from test_app.models import *
from test_app.sms import Sample


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
    if not token:
        return JsonResponse({'errno': 1003, 'msg': "参数不完整"})
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    new_name = request.POST.get('new_name')
    new_phone = request.POST.get('new_phone')
    new_legal = request.POST.get('new_legal')
    new_email = request.POST.get('new_email')
    new_description = request.POST.get('new_description')
    usr = User.objects.filter(user_id=user_id).first()
    if not usr:
        return JsonResponse({'errno': 1002, 'msg': "用户不存在"})
    if new_name:
        usr.name = new_name
    if new_phone:
        usr.phone = new_phone
    if new_legal:
        usr.legal_person = new_legal
    if new_description:
        usr.description = new_description
    if new_email:
        if usr.email != new_email and User.objects.filter(email=new_email).first():
            return JsonResponse({'errno': 1004, 'msg': "该邮箱已注册"})
        usr.email = new_email
    usr.save()
    return JsonResponse({'errno': 0, 'msg': "修改成功"})


# 获取用户信息
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
    # redis_default = get_redis_connection('default')
    # redis_default.set(email, sms_code, 60 * 5)
    status = send_sms_code(email, sms_code)
    if not status:
        return JsonResponse({'errno': 1004, 'msg': "验证码发送失败"})
    return JsonResponse({'errno': 0, 'msg': "验证码发送成功"})


# 新增客户信息
@csrf_exempt
def addNewClient(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    new_name = request.POST.get('new_name')
    new_phone = request.POST.get('new_phone')
    new_company = request.POST.get('new_company')
    new_legal = request.POST.get('new_legal')
    new_email = request.POST.get('new_email')
    if not all([new_name, new_phone, new_company, new_legal, new_email]):
        return JsonResponse({'errno': 1003, 'msg': "参数不完整"})
    usr = User.objects.filter(username=new_email).first()
    if usr:
        return JsonResponse({'errno': 1002, 'msg': "用户已存在"})
    # 在这里进行新增客户信息的操作
    User.objects.create_user(username=new_email, phone=new_phone, legal_person=new_legal, company=new_company,
                             email=new_email, name=new_name, password=new_email)
    return JsonResponse({'errno': 0, 'msg': "客户信息添加成功"})


# 删除客户信息
@csrf_exempt
def deleteClientInfo(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    else:
        id = request.POST.get('id')
        usr = User.objects.filter(user_id=id).delete()
    if usr:
        return JsonResponse({'errno': 0, 'msg': "客户信息已删除"})
    else:
        return JsonResponse({'errno': 1, 'msg': "客户信息不存在"})


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

    period = int(request.POST.get('period'))
    maintain_day = str(request.POST.get('maintain_day'))
    # 时间拼接
    start_time = ['08:00', '10:00', '14:00', '16:00']
    end_time = ['10:00', '12:00', '16:00', '18:00']
    maintain_start_time = maintain_day + ' ' + start_time[period - 1]
    maintain_end_time = maintain_day + ' ' + end_time[period - 1]
    # 字符串转时间戳
    mst = datetime.strptime(maintain_start_time, '%Y-%m-%d %H:%M')
    met = datetime.strptime(maintain_end_time, '%Y-%m-%d %H:%M')
    maintain_start_time = mst.timestamp()
    maintain_end_time = met.timestamp()
    maintain_day = time.mktime(time.strptime(maintain_day, "%Y-%m-%d"))
    if not all([user_id, name, phone, room_id, r_type, description, period, maintain_day]):
        return JsonResponse({'errno': 1003, 'msg': "参数不完整"})
    repair_form = RepairForm.objects.filter(room_id=room_id)
    for form in repair_form:
        if form.status == 0 or form.status == 1:
            return JsonResponse({'errno': 1004, 'msg': "该房间已报修"})

    RepairForm.objects.create(company_id=user, company_name=user.name, contact_name=name, period=period,
                              maintain_day=maintain_day, contact_phone=phone, room_id=room,
                              type=r_type, description=description, repair_time=repair_time,
                              maintain_start_time=maintain_start_time, maintain_end_time=maintain_end_time)
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
        maintain_time = datetime.fromtimestamp(res['maintain_day']).strftime('%Y-%m-%d') + ' ' \
                        + datetime.fromtimestamp(res['maintain_start_time']).strftime('%H:%M') + '-' \
                        + datetime.fromtimestamp(res['maintain_end_time']).strftime('%H:%M')
        ret = {
            'wid': res['id'],
            'rid': res['room_id'],
            'type': res['type'],
            'repair_time': datetime.fromtimestamp(res['repair_time']).strftime('%Y-%m-%d %H:%M:%S'),
            'maintain_time': maintain_time,
            # 'period': res['period'],
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
    repair_form = RepairForm.objects.filter(maintainer_id=user_id)
    data = []
    today = datetime.today().strftime('%Y-%m-%d')
    tomorrow = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    taskCount = {
        'sum': repair_form.count(),
        'today': []
    }
    repair = []
    today_num = [0, 0, 0, 0]
    for form in repair_form:
        res = form.get_info()
        maintain_day = datetime.fromtimestamp(res['maintain_day']).strftime('%Y-%m-%d')
        if maintain_day == today:
            today_num[int(res['period'] - 1)] = 1
        ret = {
            'wid': res['id'],
            'repair_time': datetime.fromtimestamp(res['repair_time']).strftime('%Y-%m-%d %H:%M:%S'),
            'maintain_time': datetime.fromtimestamp(res['maintain_day']).strftime('%Y-%m-%d'),
            'period': res['period'],
            'status': res['status']
        }
        repair.append(ret)
    taskCount['today'] = today_num
    data = {
        'taskCount': taskCount,
        'repair': repair
    }
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
        'maintain_day': datetime.fromtimestamp(res['maintain_day']).strftime('%Y-%m-%d'),
        'period': res['period'],
        'status': res['status']
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
    user.is_available = 1
    user.save()

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


# 获取某一楼层所有房间状态
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
    token = request.POST.get('token')
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    admin = User.objects.filter(user_id=user_id).first()
    if not admin:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    if admin.type != -1:
        return JsonResponse({'errno': 1005, 'msg': "用户无权限"})
    clients = []
    client = User.objects.filter(type=0).all()
    for c in client:
        rooms = Lease.objects.filter(user_id=c.user_id)
        room_info = []
        for r in rooms:
            payments = Payment.objects.filter(lease_id=r.id).all()
            payment = []
            for p in payments:
                if not p.time:
                    is_paid = False
                    tmp = {
                        'year': str(p.year),
                        'ispaid': is_paid,
                        'pay_time': None
                    }
                else:
                    is_paid = True
                    tmp = {
                        'year': str(p.year),
                        'ispaid': is_paid,
                        'pay_time': datetime.fromtimestamp(p.time).strftime('%Y-%m-%d')
                    }
                payment.append(tmp)
            tmp = {
                'id': r.room_id_id,
                'start_time': datetime.fromtimestamp(r.start_time).strftime('%Y-%m-%d'),
                'end_time': datetime.fromtimestamp(r.end_time).strftime('%Y-%m-%d'),
                'sign_time': datetime.fromtimestamp(r.contract_time).strftime('%Y-%m-%d'),
                'payment': payment,
                'lease_id': r.id
            }
            room_info.append(tmp)

        ret = {
            'legal_person': c.legal_person,
            'company': c.company,
            'name': c.name,
            'phone': c.phone,
            'room': room_info,
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
    form_id = int(request.POST.get('form_id'))
    repair_form = RepairForm.objects.filter(id=form_id).first()
    if not repair_form:
        return JsonResponse({'errno': 1003, 'msg': "报修单不存在"})
    if repair_form.status != 0:
        return JsonResponse({'errno': 1004, 'msg': "报修单状态错误"})

    maintain_day = request.POST.get('maintain_date')
    period = request.POST.get('maintain_period')
    maintainer_name = request.POST.get('maintainer_name')
    maintainer_id = int(request.POST.get('maintainer_id'))
    maintainer_phone = request.POST.get('maintainer_phone')

    # # 维修工状态设为不空闲
    # maintainer = User.objects.filter(user_id=maintainer_id).first()
    # if not maintainer:
    #     return JsonResponse({'errno': 1005, 'msg': "维修工不存在"})
    # maintainer.is_available = 0
    # maintainer.save()

    # 将时间字符串转换为时间戳
    dt = datetime.strptime(maintain_day, '%Y-%m-%d')
    maintain_day = dt.timestamp()

    repair_form.maintain_day = maintain_day
    repair_form.period = period
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
        maintain_time = datetime.fromtimestamp(res['maintain_day']).strftime('%Y-%m-%d') + ' ' \
                        + datetime.fromtimestamp(res['maintain_start_time']).strftime('%H:%M') + '-' \
                        + datetime.fromtimestamp(res['maintain_end_time']).strftime('%H:%M')
        ret = {
            'form_id': res['id'],
            'repair_time': datetime.fromtimestamp(res['repair_time']).strftime('%Y-%m-%d %H:%M:%S'),
            'expect_time': maintain_time,
            'user_id': res['company_id'],
            'room_id': res['room_id'],
            'status': res['status'],
            'type': res['type'],
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
                             user_id=usr, )
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


# @csrf_exempt
# def get_worker(request):
#     if request.method != 'POST':
#         return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
#     token = request.POST.get('token')
#     page = int(request.POST.get('page'))
#     num = int(request.POST.get('numInOnePage'))
#     if not all([token, page, num]):
#         return JsonResponse({'errno': 1002, 'msg': "参数不完整"})
#     admin_id = decode_token(token)
#     if admin_id == -1:
#         return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
#     admin = User.objects.filter(user_id=admin_id).first()
#     if not admin:
#         return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
#     if admin.type != -1:
#         return JsonResponse({'errno': 1005, 'msg': "用户无权限"})
#     workers = User.objects.filter(type__in=[-1, 1, 2, 3]).all()[(page - 1) * num: page * num]
#     r = []
#     for worker in workers:
#         t = time.time()
#         form = RepairForm.objects.filter(maintainer_id=worker.user_id).filter(maintain_start_time__lte=t).filter(
#             maintain_end_time__gte=t).filter(status__lt=2).first()
#         k = 1
#         if form:
#             k = 0
#         r.append({'user_id': worker.user_id, 'name': worker.name, 'tel': worker.phone, 'job': worker.post,
#                   'isMaintainer': worker.type != -1, 'category': str(worker.type), 'isAvailable': k})
#     return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': r})


@csrf_exempt
def get_worker(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    if not all([token]):
        return JsonResponse({'errno': 1002, 'msg': "参数不完整"})
    admin_id = decode_token(token)
    if admin_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    admin = User.objects.filter(user_id=admin_id).first()
    if not admin:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    if admin.type != -1:
        return JsonResponse({'errno': 1005, 'msg': "用户无权限"})
    workers = User.objects.filter(type__in=[-1, 1, 2, 3]).all()
    r = []
    for worker in workers:
        t = time.time()
        form = RepairForm.objects.filter(maintainer_id=worker.user_id).filter(maintain_start_time__lte=t).filter(
            maintain_end_time__gte=t).filter(status__lt=2).first()
        k = 1
        if form:
            k = 0
        r.append({'user_id': worker.user_id, 'name': worker.name, 'tel': worker.phone, 'job': worker.post,
                  'isMaintainer': worker.type != -1, 'category': str(worker.type), 'isAvailable': k})
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': r})


# 客户获取自己租赁的房间的信息
@csrf_exempt
def get_lease_room(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    user = User.objects.filter(user_id=user_id).first()
    if not user:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    room_list = Lease.objects.filter(user_id=user).all()
    data = []
    for room in room_list:
        res = room.get_info()
        if res['start_time'] < time.time() < res['end_time']:
            ret = {
                'room_id': res['room_id']
            }
            data.append(ret)
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': data})


# 获取维修工作数量（按照最近5年 最近6个月统计）
@csrf_exempt
def get_maintain_num(request):
    if request.method != 'GET':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    repair_forms = RepairForm.objects.filter(status=2).order_by('-solve_time')
    # 按年份统计不同种类的维修工作的数量
    data = []
    works_year = []
    for i in range(5):
        works_year.append({
            'year': str(datetime.now().year - (4 - i)),
            'number_water': 0,
            'number_elec': 0,
            'number_mecha': 0,
            'number_other': 0,
            'number_total': 0
        })
    for repair_form in repair_forms:
        year = datetime.fromtimestamp(repair_form.solve_time).strftime('%Y')
        status = int(repair_form.status)
        flag = False
        for work_year in works_year:
            if year == work_year.get('year'):
                flag = True
                if status == 1:
                    work_year['number_water'] += 1
                elif status == 2:
                    work_year['number_elec'] += 1
                elif status == 3:
                    work_year['number_mecha'] += 1
                elif status == 4:
                    work_year['number_other'] += 1
                work_year['number_total'] += 1
                break
        if not flag:
            break
    # 按月份统计不同种类的维修工作的数量（yyyy-mm格式的字符串，按照时间倒序排列)
    works_month = []
    for i in [5, 4, 3, 2, 1, 0]:
        month = (datetime.now() - timedelta(days=30 * i)).strftime('%Y-%m')
        works_month.append({
            'month': month,
            'number_water': 0,
            'number_elec': 0,
            'number_mecha': 0,
            'number_other': 0,
            'number_total': 0
        })
    for repair_form in repair_forms:
        month = datetime.fromtimestamp(repair_form.solve_time).strftime('%Y-%m')
        status = int(repair_form.status)
        flag = False
        for work_month in works_month:
            if month == work_month['month']:
                flag = True
                if status == 1:
                    work_month['number_water'] += 1
                elif status == 2:
                    work_month['number_elec'] += 1
                elif status == 3:
                    work_month['number_mecha'] += 1
                elif status == 4:
                    work_month['number_other'] += 1
                work_month['number_total'] += 1
                break
        if not flag:
            break
    data = {
        'works_year': works_year,
        'works_month': works_month
    }
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': data})


# 获取访客数量（按照最近14天，最近12个月，公司统计(公司也按照最近14天，最近12个月)）
@csrf_exempt
def get_visitor_num(request):
    if request.method != 'GET':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    visitors = Visitor.objects.all().order_by('-visit_time')
    data = []
    # 按照最近14天统计
    sum_visitors_day = []
    for i in range(14):
        day = (datetime.now() - timedelta(days=(13 - i))).strftime('%Y-%m-%d')
        ret = {
            'day': day,
            'number': 0
        }
        sum_visitors_day.append(ret)
    for visitor in visitors:
        day = datetime.fromtimestamp(visitor.visit_time).strftime('%Y-%m-%d')

        flag = False
        for visitor_day in sum_visitors_day:
            if day == visitor_day['day']:
                flag = True
                visitor_day['number'] += 1
                break
        if not flag:
            break
    # 按照最近12个月统计
    sum_visitors_month = []
    for i in [11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]:
        month = (datetime.now() - timedelta(days=30 * i)).strftime('%Y-%m')
        ret = {
            'month': month,
            'number': 0
        }
        sum_visitors_month.append(ret)

    for visitor in visitors:
        month = datetime.fromtimestamp(visitor.visit_time).strftime('%Y-%m')
        flag = False
        for visitor_month in sum_visitors_month:
            if month == visitor_month['month']:
                flag = True
                visitor_month['number'] += 1
                break
        if not flag:
            break
    ret = {
        'name': '总访客数',
        'visitors_day': sum_visitors_day,
        'visitors_month': sum_visitors_month
    }
    data.append(ret)
    # 按照公司统计，公司也按照最近14天，最近12个月统计
    # 公司列表
    sum_company = []
    companies = Visitor.objects.values('company').distinct()
    for company in companies:
        company_name = company['company']
        visitors_day = []
        for i in range(14):
            day = (datetime.now() - timedelta(days=(13 - i))).strftime('%Y-%m-%d')
            ret = {
                'day': day,
                'number': 0
            }
            visitors_day.append(ret)
        visitors_month = []
        for i in [11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]:
            month = (datetime.now() - timedelta(days=30 * i)).strftime('%Y-%m')
            ret = {
                'month': month,
                'number': 0
            }
            visitors_month.append(ret)
        sum_company.append({
            'name': company_name,
            'visitors_day': visitors_day,
            'visitors_month': visitors_month
        })
    for visitor in visitors:
        company_name = visitor.company
        day = datetime.fromtimestamp(visitor.visit_time).strftime('%Y-%m-%d')
        month = datetime.fromtimestamp(visitor.visit_time).strftime('%Y-%m')
        for company in sum_company:
            if company_name == company['name']:
                for visitor_day in company['visitors_day']:
                    if day == visitor_day['day']:
                        visitor_day['number'] += 1
                        break
                for visitor_month in company['visitors_month']:
                    if month == visitor_month['month']:
                        visitor_month['number'] += 1
                        break
                break
    data.extend(sum_company)
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': data})


@csrf_exempt
def get_solution(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    t = request.POST.get('type')
    if t:
        issues = Wiki.objects.filter(type=t)
    else:
        issues = Wiki.objects.all()
    data = []
    for issue in issues:
        data.append({'problem': issue.description, 'solution': issue.solution, 'type': issue.type})
    return JsonResponse({'errno': 0, 'msg': "查询成功", 'data': data})


@csrf_exempt
def add_solution(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    problem = request.POST.get('problem')
    solution = request.POST.get('solution')
    t = request.POST.get('type')
    if not all([token, problem, solution, t]):
        return JsonResponse({'errno': 1002, 'msg': "参数不完整"})
    admin_id = decode_token(token)
    if admin_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    admin = User.objects.filter(user_id=admin_id).first()
    if not admin:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    if admin.type != -1:
        return JsonResponse({'errno': 1005, 'msg': "用户无权限"})
    Wiki.objects.create(description=problem, solution=solution, type=t)
    return JsonResponse({'errno': 0, 'msg': "添加成功"})


@csrf_exempt
def visit_apply(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    name = request.POST.get('user_name')
    number = request.POST.get('user_id')
    phone = request.POST.get('phone_num')
    visit_time = int(request.POST.get('visit_time'))
    if not all([token, name, number, phone, visit_time]):
        return JsonResponse({'errno': 1002, 'msg': "参数不完整"})
    user_id = decode_token(token)
    if user_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    user = User.objects.filter(user_id=user_id).first()
    if not user:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    t = datetime.fromtimestamp(visit_time).strftime('%Y-%m-%d')
    time_array = time.strptime(t, '%Y-%m-%d')
    start = int(time.mktime(time_array))
    end = start + 86400
    visitor = Visitor.objects.filter(number=number).filter(visit_time__gte=start).filter(visit_time__lt=end).first()
    if visitor:
        return JsonResponse({'errno': 1003, 'msg': "该访客已申请过"})
    password = '%06d' % random.randint(0, 999999)
    Visitor.objects.create(name=name, number=number, visit_time=visit_time, phone=phone, apply_time=time.time(),
                           user_id=user, password=password, company=user.company)
    return JsonResponse({'errno': 0, 'msg': "申请成功"})


@csrf_exempt
def deliver(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    type = int(request.POST.get('type'))
    print(type)
    print('--------')
    period = int(request.POST.get('period'))
    maintain_time = request.POST.get('maintain_time')
    if not all([token, type, period, maintain_time]):
        return JsonResponse({'errno': 1002, 'msg': "参数不完整"})
    admin_id = decode_token(token)
    if admin_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    admin = User.objects.filter(user_id=admin_id).first()
    if not admin:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    if admin.type != -1:
        return JsonResponse({'errno': 1005, 'msg': "用户无权限"})
    if type not in [1, 2, 3, 4]:
        return JsonResponse({'errno': 1003, 'msg': "时间段错误"})
    time_array = time.strptime(maintain_time, '%Y-%m-%d')
    start_time = int(time.mktime(time_array)) + 21600 + period * 7200
    forms = RepairForm.objects.filter(maintain_start_time=start_time)
    unavailables = []
    for form in forms:
        if form.maintainer_id:
            unavailables.append(int(form.maintainer_id))
    types = []
    if type == 4:
        types = [1, 2, 3]
    else:
        types.append(type)
    workers = User.objects.filter(type__in=types)
    for worker in workers:
        if worker.user_id not in unavailables:
            return JsonResponse({'errno': 0, 'msg': "派单成功",
                                 'data': {'maintainer_name': worker.name, 'maintainer_phone': worker.phone,
                                          'maintainer_id': worker.user_id, 'maintain_time': start_time}})
    return JsonResponse({'errno': 1004, 'msg': "该时段无空闲维修工"})


@csrf_exempt
def send_reminder(request):
    t = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')
    time_array = time.strptime(t, '%Y-%m-%d')
    start = int(time.mktime(time_array)) + 2678400
    end = start + 86400
    rooms = Lease.objects.filter(end_time__gte=start).filter(end_time__lt=end)
    for room in rooms:
        print(room.room_id)
        usr = room.user_id
        if not usr:
            print("用户不存在")
            continue
        email = usr.email
        year = int(datetime.fromtimestamp(start).strftime('%Y'))
        month = int(datetime.fromtimestamp(start).strftime('%m'))
        day = int(datetime.fromtimestamp(start).strftime('%d'))
        date = '{0}年{1}月{2}日'.format(year, month, day)
        status = send_reminder_email(email, room.room_id.id, date)
        if not status:
            print("验证码发送失败")
    return JsonResponse({'errno': 0, 'msg': "邮件发送完成"})


@csrf_exempt
def visit_verify(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    password = request.POST.get('password')
    number = request.POST.get('number')
    t = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')
    time_array = time.strptime(t, '%Y-%m-%d')
    start = int(time.mktime(time_array))
    end = start + 86400
    visitor = Visitor.objects.filter(number=number).filter(visit_time__gte=start).filter(visit_time__lt=end).first()
    if not visitor:
        return JsonResponse({'errno': 1002, 'msg': "未查询到申请记录"})
    if password != visitor.password:
        return JsonResponse({'errno': 1003, 'msg': "动态密码错误"})
    return JsonResponse({'errno': 0, 'msg': "认证成功"})


@csrf_exempt
def add_payment(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    admin_id = decode_token(token)
    if admin_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    admin = User.objects.filter(user_id=admin_id).first()
    if not admin:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    lease_id = request.POST.get('lease_id')
    year = request.POST.get('year')
    ispaid = request.POST.get('ispaid')
    pay_time = request.POST.get('pay_time')
    lease = Lease.objects.filter(id=lease_id).first()
    year = int(year)
    start_year = int(datetime.fromtimestamp(lease.start_time).strftime('%Y'))
    end_year = int(datetime.fromtimestamp(lease.end_time).strftime('%Y'))
    if not start_year <= year and year <= end_year:
        return JsonResponse({'errno': 1002, 'msg': "年份超出租赁时段"})
    if pay_time:
        nowTimeArray = time.strptime(pay_time, "%Y-%m-%d")
        nowTimeStamp = str(int(time.mktime(nowTimeArray)))
        new_payment = Payment.objects.create(lease_id=lease, year=year, time=nowTimeStamp)
    else:
        new_payment = Payment.objects.create(lease_id=lease, year=year)
    return JsonResponse({'errno': 0, 'msg': "新增成功"})


@csrf_exempt
def change_payment(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    token = request.POST.get('token')
    admin_id = decode_token(token)
    if admin_id == -1:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    admin = User.objects.filter(user_id=admin_id).first()
    if not admin:
        return JsonResponse({'errno': 1000, 'msg': "token校验失败"})
    lease_id = request.POST.get('lease_id')
    year = request.POST.get('year')
    ispaid = request.POST.get('ispaid')
    pay_time = request.POST.get('pay_time')
    lease = Lease.objects.filter(id=lease_id).first()
    if pay_time:
        nowTimeArray = time.strptime(pay_time, "%Y-%m-%d")
        nowTimeStamp = str(int(time.mktime(nowTimeArray)))
        payment = Payment.objects.filter(lease_id=lease, year=year).first()
        payment.time = nowTimeStamp
        payment.save()
    else:
        payment = Payment.objects.filter(lease_id=lease, year=year).first()
        payment.time = None
    return JsonResponse({'errno': 0, 'msg': "修改成功"})


# 添加维修工人
@csrf_exempt
def add_worker(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    try:
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        post = request.POST.get('post')
        re_type = request.POST.get('type')
        email = request.POST.get('email')
        User.objects.create_user(name=name, phone=phone, post=post, type=re_type, username=email, email=email,
                                 password=email)
    except:
        return JsonResponse({'errno': 1002, 'msg': "添加失败"})
    return JsonResponse({'errno': 0, 'msg': "添加成功"})


@csrf_exempt
def send_sms(request):
    t = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')
    time_array = time.strptime(t, '%Y-%m-%d')
    start = int(time.mktime(time_array))
    end = time.time() + 1860
    visits = Visitor.objects.filter(status=0).filter(visit_time__gte=start).filter(visit_time__lt=end)
    for visit in visits:
        r = [visit.phone, str({"code": visit.password})]
        code = dict(json.loads(Sample.main(r))).get('body').get('Code')
        if code == 'OK':
            visit.status = 1
            visit.save()
    return JsonResponse({'errno': 0, 'msg': "发送完成"})
