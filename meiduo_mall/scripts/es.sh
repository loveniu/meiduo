#!/bin/bash

docker run -dti --network=host --name=elasticsearch -v /home/python/Desktop/meiduo/meiduo_mall/config/elasticsearch-2.4.6/config:/usr/share/elasticsearch/config delron/elasticsearch-ik:2.4.6-1.0