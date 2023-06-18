# 发送邮箱验证码
import random

from django.core.mail import send_mail


def send_sms_code(to_email, sms_code):
    """
    发送邮箱验证码
    :param to_mail: 发到这个邮箱
    :return: 成功：0 失败 -1
    """
    EMAIL_FROM = "1870772330@qq.com"  # 邮箱来自
    email_title = '邮箱激活'
    email_body = "您的邮箱注册验证码为：{0}, 该验证码有效时间为两分钟，请及时进行验证。".format(sms_code)
    # send_status函数作用
    send_status = send_mail(email_title, email_body, EMAIL_FROM, [to_email])
    return send_status