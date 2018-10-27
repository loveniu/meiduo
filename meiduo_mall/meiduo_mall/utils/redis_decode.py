from django_redis.pool import ConnectionFactory as CF

class ConnectionFactory(CF):
    def make_connection_params(self, url):
        kwargs = super().make_connection_params(url)
        kwargs['decode_responses'] = True
        return kwargs