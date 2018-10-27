from celery import Celery

import os

if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

# 生成celery对象
celery_app = Celery('meiduo')
# 加载配置文件
celery_app.config_from_object('celery_tasks.config')
# 自动注册任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.emails', 'celery_tasks.html'])  # 注意：传递的参数是任务列表

# celery -A celery_tasks worker -l info
