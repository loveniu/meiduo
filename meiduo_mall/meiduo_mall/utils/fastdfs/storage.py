from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client


class FastDFSStorage(Storage):
    def __init__(self, client_conf=None, base_url=None):
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf
        if base_url is None:
            base_url = settings.FDFS_BASE_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        """
        保存文件
        :param name:  前端传递的文件名
        :param context: 文件数据
        :return: 存储到数据库中的文件名
        """
        # 保存到FastDFS
        client = Fdfs_client(self.client_conf)

        ret = client.upload_by_buffer(content.read())

        if ret.get("Status") != "Upload successed.":
            raise Exception("upload file failed")

        file_name = ret.get("Remote file_id")

        return file_name

    def exists(self, name):
        return False

    def url(self, name):
        """
        在获取ImageFIled字段数据的url属性时，django会调用url方法获取文件的完整路径
        :param name: 从数据库中读出的字段值 也就是之前保存的file_name  Remote file_id
        :return:
        """
        return self.base_url + name
