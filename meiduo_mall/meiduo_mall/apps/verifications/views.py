from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from django.http import HttpResponse
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework.request import Request
import random
from rest_framework import status
from meiduo_mall.apps.users.models import User

from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.libs.yuntongxun.sms import CCP
from meiduo_mall.utils.renders import JPEGRenderer
from celery_tasks.sms.tasks import send_sms_code
from . import constants
from . import serializers

from django.conf import settings
# Create your views here.


class ImageCodeView(APIView):
    """
    图片验证码
    """
    # renderer_classes = (JPEGRenderer,)  # 自定义渲染器

    def get(self, request, image_code_id):
        """

        :param request:
        :param image_code_id:
        :return:
        """
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection("verify_codes")
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 固定返回验证码图片数据，不需要REST framework框架的Response帮助我们决定返回响应数据的格式
        # 所以此处直接使用Django原生的HttpResponse即可
        return HttpResponse(image, content_type="images/jpg")
        # return Response(image, content_type="images/jpg")


class SmsCodeView(GenericAPIView):
    serializer_class = serializers.CheckImageCodeSerializer

    def get(self, request, mobile):
        # 校验图片验证码和发送短信的频次
        # mobile是被放到了类视图对象属性kwargs中
        # print('query_params: %s' % (request.query_params))
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 校验通过
        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)

        # 保存验证码及发送记录
        redis_conn = get_redis_connection('verify_codes')
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 使用redis的pipeline管道一次执行多个命令
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        # 让管道执行命令
        pl.execute()

        # 发送短信
        # ccp = CCP()
        # time = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        # result = ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_CODE_TEMP_ID)
        # print(result)
        # 使用celery发布异步任务
        send_sms_code.delay(mobile, sms_code)
        print(sms_code)

        # 返回
        return Response({'message': 'OK'})


# 找回密码短信验证码试图
class SMSCodeByTokenView(APIView):
    """根据access_token发送短信"""

    def get(self, request):
        # 获取并校验 access_token
        access_token = request.query_params.get('access_token')
        if not access_token:
            return Response({"message": "缺少access token"}, status=status.HTTP_400_BAD_REQUEST)

        # 从access_token中取出手机号
        mobile = User.check_send_sms_code_token(access_token)
        if mobile is None:
            return Response({"message": "无效的access token"}, status=status.HTTP_400_BAD_REQUEST)

        # 判断手机号发送的次数
        redis_conn = get_redis_connection('verify_codes')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return Response({"message": "发送短信次数过于频"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # 生成短信验证码
        # 发送短信验证码
        sms_code = '%06d' % random.randint(0, 999999)

        # 保存验证码及发送记录
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 使用redis的pipeline管道一次执行多个命令
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        # 让管道执行命令
        pl.execute()

        # 发送短信
        # ccp = CCP()
        # time = str(constants.SMS_CODE_REDIS_EXPIRES / 60)
        # ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_CODE_TEMP_ID)
        # 使用celery发布异步任务
        send_sms_code.delay(mobile, sms_code)
        print(sms_code)

        # 返回
        return Response({'message': 'OK'})
