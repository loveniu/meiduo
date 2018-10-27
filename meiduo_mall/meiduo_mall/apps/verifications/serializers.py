from rest_framework import serializers
from django_redis import get_redis_connection
from redis.exceptions import RedisError
import logging

logger = logging.getLogger('django')


class CheckImageCodeSerializer(serializers.Serializer):
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):
        # 获取参数
        image_code_id = attrs['image_code_id']
        text = attrs['text']

        # 从redis取图片验证码并和前端传递的参数进行对比
        redis_con = get_redis_connection('verify_codes')

        redis_image_text = redis_con.get('img_%s' % image_code_id)
        # real_image_text = redis_image_text
        if not redis_image_text:
            raise serializers.ValidationError('无效图片验证码')

        # TODO 对于从redis数据删除图片出现异常，不交给全局异常处理，以获得良好的用户体验
        try:
            redis_con.delete('image_%s' % image_code_id)
        except RedisError as e:
            logger.error(e)
            pass

        real_image_text = redis_image_text.decode()
        print(real_image_text, '==============================')  # 数据类型bytes
        if text.lower() != real_image_text.lower():
            raise serializers.ValidationError('图片验证码错误')

        # TODO 设置短信验证码60s过期
        # get_serializer->get_serializer_context->dis_patch()
        # 里面self.kwargs属性
        # print(self.context['format'], self.context['view'], self.context['request'])

        # mobile = self.context['view'].kwargs['mobile']
        # send_flag = redis_con.get('sendf_flag_%s' % mobile)
        # if send_flag:
        #     raise serializers.ValidationError('请求过于频繁')

        """找回密码时修改序列化器"""
        mobile = self.context['view'].kwargs.get('mobile')  # 有参数说明是注册逻辑，没有说明是找回密码验证图片逻辑
        if mobile:
            send_flag = redis_con.get('sendf_flag_%s' % mobile)
            if send_flag:
                raise serializers.ValidationError('请求过于频繁')

        return attrs
