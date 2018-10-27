import logging
from decimal import Decimal
from django.db import transaction
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, APIException
from django.utils import timezone

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)


class OrderCommitSerializer(serializers.ModelSerializer):
    """
       下单数据序列化器
    """
    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        redis_conn = get_redis_connection("cart")
        logger = logging.getLogger('django')
        user = self.context['request'].user

        # 组织订单信息 20170903153611+user.id
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        # 生成订单
        with transaction.atomic():
            # 创建一个保存点
            save_id = transaction.savepoint()

            try:
                # 创建订单信息
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=validated_data['address'],
                    total_count=0,
                    total_amount=Decimal(0),
                    freight=Decimal(10),
                    pay_method=validated_data['pay_method'],
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if validated_data['pay_method'] ==
                                                                    OrderInfo.PAY_METHODS_ENUM['CASH'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )
                # 获取购物车信息
                redis_cart = redis_conn.hgetall("cart_%s" % user.id)
                cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)
                # 将bytes类型转换为int类型
                cart = {}
                for sku_id in cart_selected:
                    cart[int(sku_id)] = int(redis_cart[sku_id])

                total_amount = Decimal("0")
                total_count = 0

                skus = SKU.objects.filter(id__in=cart.keys())

                # 用于演示并发下单
                # import time
                # time.sleep(5)

                # 处理订单商品
                for sku in skus:
                    # 出现对于同一个商品的争抢下单时，如失败，再次尝试，直到库存不足
                    while True:
                        sku = SKU.objects.get(id=sku.id)
                        sku_count = cart[sku.id]

                        # 判断库存
                        origin_stock = sku.stock  # 原始库存
                        origin_sales = sku.sales  # 原始销量

                        if sku_count > origin_stock:
                            transaction.savepoint_rollback(save_id)
                            raise ValidationError({'detail': '商品库存不足'})

                        # 减少库存
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count

                        # 根据原始库存条件更新，返回更新的条目数，乐观锁
                        ret = SKU.objects.filter(id=sku.id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                        if ret == 0:
                            continue

                        sku.goods.sales += sku_count
                        sku.goods.save()

                        sku_amount = sku.price * sku_count  # 商品金额
                        total_amount += sku_amount  # 累计总金额
                        total_count += sku_count  # 累计总额

                        # 保存订单商品
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )

                        # 更新成功
                        break
                    """
                    # 未加锁的情况
                    sku_count = cart[sku.id]

                    # 判断库存
                    origin_stock = sku.stock  # 原始库存
                    origin_sales = sku.sales  # 原始销量

                    if sku_count > origin_stock:
                        transaction.savepoint_rollback(save_id)
                        raise ValidationError({'detail': '商品库存不足'})

                    # 减少库存
                    new_stock = origin_stock - sku_count
                    new_sales = origin_sales + sku_count

                    sku.stock = new_stock
                    sku.sales = new_sales
                    sku.save()

                    sku.goods.sales += sku_count
                    sku.goods.save()

                    sku_amount = sku.price * sku_count  # 商品金额
                    total_amount += sku_amount  # 累计总金额
                    total_count += sku_count  # 累计总额

                    # 保存订单商品
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=sku_count,
                        price=sku.price,
                    )
                    """

                # 更新订单的金额数量信息
                order.total_amount = total_amount
                order.total_amount += order.freight
                order.total_count = total_count
                order.save()

            except ValidationError:
                raise
            except Exception as e:
                logger.error(e)
                transaction.savepoint_rollback(save_id)
                raise APIException('保存订单失败')

            # 提交事务
            transaction.savepoint_commit(save_id)

            # 更新redis中保存的购物车数据
            print(user.id,'=====================================')
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, *cart.keys())
            pl.srem('cart_selected_%s' % user.id, *cart.keys())
            pl.execute()
            return order


class SKUSerializer(serializers.ModelSerializer):
    """
    SKU商品数据序列化器
    """
    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url')


class OrderGoodsSerializer(serializers.ModelSerializer):
    """
    订单商品数据序列化器
    """
    sku = SKUSerializer()

    class Meta:
        model = OrderGoods
        fields = ('id', 'sku', 'count', 'price')


class DateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        tz = timezone.get_default_timezone()
        value = timezone.localtime(value, timezone=tz)
        return super().to_representation(value)


class OrderInfoSerializer(serializers.ModelSerializer):
    """
    订单数据序列化器
    """
    skus = OrderGoodsSerializer(many=True)
    create_time = DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = OrderInfo
        fields = ('order_id', 'create_time', 'total_amount', 'freight', 'status', 'skus', 'pay_method')


class SaveOrderCommentSerializer(serializers.ModelSerializer):
    """
    保存订单评论数据序列化器
    """
    class Meta:
        model = OrderGoods
        fields = ('sku', 'comment', 'score', 'is_anonymous')
        extra_kwargs = {
            'comment': {
                'required': True
            },
            'score': {
                'required': True
            },
            'is_anonymous': {
                'required': True
            }
        }

    def validate(self, datas):
        order_id = self.context['view'].kwargs['order_id']
        user = self.context['request'].user
        try:
            OrderInfo.objects.filter(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
        except OrderInfo.DoesNotExist:
            raise serializers.ValidationError('订单信息有误')

        return datas

    @transaction.atomic
    def create(self, validated_data):
        order_id = self.context['view'].kwargs['order_id']
        sku = validated_data['sku']

        # 保存评论数据
        OrderGoods.objects.filter(order_id=order_id, sku=sku, is_commented=False).update(
            comment=validated_data['comment'],
            score=validated_data['score'],
            is_anonymous=validated_data['is_anonymous'],
            is_commented=True
        )

        # 累计评论数据
        sku.comments += 1
        sku.save()
        sku.goods.comments += 1
        sku.goods.save()

        # 如果所有订单商品都已评价，则修改订单状态为已完成
        if OrderGoods.objects.filter(order_id=order_id, is_commented=False).count() == 1:
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM['FINISHED'])

        return validated_data


