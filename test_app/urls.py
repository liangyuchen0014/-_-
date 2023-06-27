"""test_back URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from .views import *

urlpatterns = [
    path('register', register),
    path('login', user_login),
    path('changeUserInfo', change_user_info),
    path('get_user_info', get_user_info),
    path('forget_password', forget_password),
    path('send_email_code', send_email_code),
    path('getRoomStatus', get_room_status),
    path('get_client_info', get_client_info),
    path('repairReport', repairReport),
    path('myRepair', myRepair),
    path('repairService', repairService),
    path('repairDetail', repairDetail),
    path('repairComplete', repairComplete),
    path('setMaintainer', setMaintainer),
    path('repairList', repairList),
    path('changeClientInfo', change_client_info),
    path('saveLeaseInfo', save_lease),
    path('deleteLeaseInfo', del_lease),
    path('getWorker', get_worker),
    path('addNewClient', add_new_client),
    path('deleteClientInfo', delete_client_info),
    path('getLeaseRoom', get_lease_room),
    path('getSolution', get_solution),
    path('deleteSolution', del_solution),
    path('addSolution', add_solution),
    path('userApply', visit_apply),
    path('autoDeliver', deliver),
    path('send_reminder', send_reminder),
    path('visit_verify', visit_verify),
    path('addPayment', add_payment),
    path('changePayment', change_payment),
    path('getWorkNumber', get_maintain_num),
    path('AddWorker', add_worker),
    path('getVisitorNumber', get_visitor_num),
    path('send_sms', send_sms),
    path('getStatistics', get_total_num),
    path('getTodayOrder', get_today_repair),
]
