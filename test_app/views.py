import time
import datetime

from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_jwt.settings import api_settings

from test_app.models import *
from qunxing_backend.settings import EMAIL_HOST_USER
from qunxing_backend.settings import MEDIA_ROOT


@csrf_exempt
def register(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    username = request.POST.get('username')
    email = request.POST.get('email')
    password = request.POST.get('password')
    if not all([username, password, email]):
        return JsonResponse({'errno': 1002, 'msg': "参数不完整"})
    usr = User.objects.filter(username=username).first()
    if usr:
        return JsonResponse({'errno': 1003, 'msg': "该用户名已注册"})
    new_user = User.objects.create_user(username=username, password=password, email=email)
    return JsonResponse({'errno': 0, 'msg': "注册成功", 'data': new_user.get_info()})


@csrf_exempt
def user_login(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    username = request.POST.get('username')
    password = request.POST.get('password')
    if not all([username, password]):
        return JsonResponse({'errno': 1003, 'msg': "参数不完整"})
    # 验证登录
    is_login = authenticate(username=username, password=password)
    if is_login is None:
        return JsonResponse({'errno': 1005, 'message': '用户名或密码错误'})
    login(request, is_login)
    # 生成token
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
    payload = jwt_payload_handler(is_login)
    token = jwt_encode_handler(payload)
    # 解析token
    jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
    r = jwt_decode_handler(token)
    return JsonResponse(
        {'errno': 0, 'msg': "登录成功", 'data': {'user_id': r['user_id'], 'username': r['username'], 'token': token}})


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
def email_send(request):
    if request.method != 'POST':
        return JsonResponse({'errno': 1001, 'msg': "请求方式错误"})
    email = request.POST.get('email')
    rand_code = request.POST.get('rand_code')
    message = "您的验证码是" + rand_code + ", 请尽快完成您的信息验证。"
    if not all([email, rand_code]):
        return JsonResponse({'errno': 1003, 'msg': "参数不完整"})
    try:
        send_mail('群星闪耀时', message, EMAIL_HOST_USER, [email], fail_silently=False)
        return JsonResponse(
            {'errno': 0, 'msg': "验证码已发送"})
    except:
        # traceback.print_exc()
        return JsonResponse(
            {'errno': 1004, 'msg': "验证码发送失败"})


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
