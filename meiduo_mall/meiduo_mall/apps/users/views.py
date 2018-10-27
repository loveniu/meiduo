from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, GenericAPIView, mixins, RetrieveAPIView, UpdateAPIView
from meiduo_mall.apps.verifications.serializers import CheckImageCodeSerializer
from rest_framework import status
import re
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from django_redis import get_redis_connection

from .models import User
from rest_framework.generics import CreateAPIView, GenericAPIView, mixins
from meiduo_mall.apps.verifications.serializers import CheckImageCodeSerializer
from rest_framework import status
import re
from . import constants
from meiduo_mall.apps.goods.models import SKU

from .utils import get_user_by_account
from .models import User
from . import serializers

from rest_framework_jwt.views import ObtainJSONWebToken
from meiduo_mall.apps.carts.utils import merge_cart_cookie_to_redis
from meiduo_mall.utils.permissions import IsOwner

# Create your views here.
from rest_framework.serializers import ValidationError


# 第二天
# 验证用户是否存在
class UsernameCountView(APIView):
    """
    用户名数量
    """

    def get(self, request, username):
        """
        获取指定用户名数量
        """
        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }
        # raise ValidationError('异常数据')
        return Response(data)


# 验证手机号是否存在
class MobileCountView(APIView):
    """
    手机号数量
    """

    def get(self, request, mobile):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)


# 用户注册
class UserView(CreateAPIView):
    """
    用户注册
    """
    serializer_class = serializers.CreateUserSerializer


# 第三天
# 生成用于发送短信验证码的token
class SMSCodeTokenView(GenericAPIView):
    """获取发送短信验证码的凭据"""

    serializer_class = CheckImageCodeSerializer

    def get(self, request, account):
        # 校验图片验证码
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 根据account查询User对象
        user = get_user_by_account(account)
        if user is None:
            return Response({"message": '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 根据User对象的手机号生成access_token
        access_token = user.generate_send_sms_code_token()

        # 修改手机号
        mobile = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', user.mobile)

        return Response({
            'mobile': mobile,
            'access_token': access_token
        })


# 生成用于设置密码的token
class PasswordTokenView(GenericAPIView):
    """
    用户帐号设置密码的token
    """
    serializer_class = serializers.CheckSMSCodeSerializer

    def get(self, request, account):
        """
        根据用户帐号获取修改密码的token
        """
        # 校验短信验证码
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = serializer.user  # 因为序列话器对象验证方法中已经添加了user属性

        # 生成修改用户密码的access token
        access_token = user.generate_set_password_token()

        return Response({'user_id': user.id, 'access_token': access_token})


# 设置新密码和修改密码
class PasswordView(mixins.UpdateModelMixin, GenericAPIView):
    """
    用户密码
    """
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.ResetPasswordSerializer
        elif self.request.method == 'PUT':
            return serializers.ChangePasswordSerializer

    def get_permissions(self):
        if self.request.method == "PUT":
            # return [IsAuthenticated()]
            return [IsOwner()]
        else:
            return [AllowAny()]

    def post(self, request, pk):
        return self.update(request, pk)

    def put(self, request, pk):
        return self.update(request, pk)


# 第五天
# 用户个人中心
class UserDetailView(RetrieveAPIView):
    """用户详情信息
       /users/<pk>/

       /user/
       """
    # def get(self, request):
    #     request.user
    #
    # def post(self, request):

    # 在类视图对象中也保存了请求对象request
    # request对象的user属性是通过认证检验之后的请求用户对象
    # 类视图对象还有kwargs属性

    serializer_class = serializers.UserDetailSerializer
    # 补充通过认证才能访问接口的权限
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        返回请求的用户对象
        :return: user
        """
        return self.request.user


# 发送激活邮件
class EmailView(UpdateAPIView):
    serializer_class = serializers.EmailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# 激活邮件
class EmailVerifyView(APIView):
    """
    邮箱激活视图
    """

    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response('缺少token', status.HTTP_400_BAD_REQUEST)
        # 校验  保存
        result = User.check_email_verify_token(token)

        if result:
            return Response({"message": "OK"})
        else:
            return Response({"非法的token"}, status=status.HTTP_400_BAD_REQUEST)


# 我的地址
class AddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = serializers.UserAddressSerializer
    permissions = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = serializers.UserAddressSerializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None, address_id=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# 用户浏览历史
class UserBrowsingHistoryView(mixins.CreateModelMixin, GenericAPIView):
    """
    用户浏览历史记录
    """
    serializer_class = serializers.AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]  # 视图权限，用户登录之后才可以访问

    def post(self, request):
        return self.create(request)

    def get(self, request):
        user_id = request.user.id
        redis_conn = get_redis_connection('history')
        sku_ids = redis_conn.lrange('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT)
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)
        serializer = serializers.SKUSerializer(skus, many=True)
        return Response(serializer.data)


# 购物车合并时重写登录视图
# 用户登录认证视图
class UserAuthorizeView(ObtainJSONWebToken):
    """
    用户认证
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # print(123)
            user = serializer.validated_data.get('user') or request.user
            response = merge_cart_cookie_to_redis(request, user, response)
        return response
