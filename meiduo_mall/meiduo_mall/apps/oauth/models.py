from django.db import models
from meiduo_mall.utils.models import BaseModel
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSSetializer
from django.conf import settings
from . import constants
from itsdangerous import BadData


# Create your models here.

class OAuthQQUser(BaseModel):
    """
    QQ登录用户数据
    """
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name

    @staticmethod
    def generate_save_user_token(openid):
        """
        生成绑定用户使用的token
        :param self:
        :param openid: qq用户对应的用户id
        :return:
        """
        serializer = TJWSSSetializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        data = {'openid': openid}
        token = serializer.dumps(data)
        return token.decode()

    @staticmethod
    def check_save_user_token(token):
        """
        解析用户绑定使用的token
        :param self:
        :param data:
        :return:
        """
        serializer = TJWSSSetializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        return data.get('openid')


