from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from rest_framework.generics import GenericAPIView

from .utils import OAuthQQ
from .exceptions import QQAPIException
from .models import OAuthQQUser
from .serializers import OAuthQQUserSerializer
from meiduo_mall.apps.carts.utils import merge_cart_cookie_to_redis


# Create your views here.


class OAuthQQURLView(APIView):
    """
    提供QQ登录的网址
    前端请求的接口网址  /oauth/qq/authorization/?state=xxxxxxx
    state参数是由前端传递，参数值为在QQ登录成功后，我们后端把用户引导到哪个美多商城页面
    """

    def get(self, request):
        # 提取state参数
        state = request.query_params.get('state')
        if not state:
            state = '/'  # 如果前端未指明，我们设置用户QQ登录成功后，跳转到主页

        # 按照QQ的说明文档，拼接用户QQ登录的链接地址
        oauth_qq = OAuthQQ(state=state)
        login_url = oauth_qq.generate_qq_login_url()

        # 返回链接地址
        return Response({"oauth_url": login_url})


class OAuthQQUserView(GenericAPIView):
    """
    获取QQ用户对应的美多商城用户
    """
    serializer_class = OAuthQQUserSerializer

    def get(self, request):
        # 提取code参数
        code = request.query_params.get('code')
        if not code:
            return Response({"message": "缺少code"}, status=status.HTTP_400_BAD_REQUEST)

        # 凭借code向QQ服务器发起请求，获取access_token
        oauth_qq = OAuthQQ()
        try:
            access_token = oauth_qq.get_access_token(code)

            # 凭借 access_token向QQ服务器发送请求，获取openid
            openid = oauth_qq.get_openid(access_token)
        except:
            return Response({'message': '获取QQ用户数据异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 根据openid查询此用户是否之前在美多中绑定的用户
        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果未绑定，手动创建接下来绑定身份使用的access_token, 并返回
            access_token = OAuthQQUser.generate_save_user_token(openid)
            return Response({'access_token': access_token})
        else:
            # 如果已经绑定，直接生成登录凭证 JWT token，并返回
            # 手动为用户生成JWT token
            user = oauth_user.user

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            response = Response({
                'token': token,
                'username': user.username,
                'user_id': user.id
            })
            merge_cart_cookie_to_redis(request, user, response)
            return response

    def post(self, request):
        # 调用序列化器检查数据， 保存
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 保存用户对象与openid的对应关系
        user = serializer.save()

        # 返回用户登录成功的JWT token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        response = Response({
            'token': token,
            'username': user.username,
            'user_id': user.id
        })
        merge_cart_cookie_to_redis(request, user, response)
        return response
