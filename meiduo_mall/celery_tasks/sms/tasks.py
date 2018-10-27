from .yuntongxun.sms import CCP
from celery_tasks.main import celery_app
from . import constants


@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    """

    :param mobile: 手机号
    :param sms_code: 短信验证码
    :return: None
    """
    ccp = CCP()
    time = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
    result = ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_CODE_TEMP_ID)
    print(result)
