# coding: utf-8
import platform
from tools_lib.host_info import DEV_NODE, PROD_API_NODE
from qiniu import Auth

node = platform.node()

access_key = 'zVxhvVY8ggEUftanwKVdmqNLvoi2IXrOTZG9NwMT'
secret_key = 'IIiL9fdiVOHqmiixrF6NYY-pRMVU5Gjo5UfnYPUE'
q = Auth(access_key, secret_key)

# 七牛的空间域名
IMAGE_URL_DOMAINS = {
    'localhost': "7qnajq.com1.z0.glb.clouddn.com",
    DEV_NODE: "7qnajq.com1.z0.glb.clouddn.com",
    PROD_API_NODE: "mrwind.qiniudn.com"
}

IMAGE_URL_DOMAIN = IMAGE_URL_DOMAINS.get(node, IMAGE_URL_DOMAINS['localhost'])

BUCKETS = {
    'localhost': "dev-mrwind",
    DEV_NODE: "dev-mrwind",
    PROD_API_NODE: "mrwind"
}

BUCKET = BUCKETS.get(node, BUCKETS['localhost'])


def get_image_url(hash):
    """
    获取文件在七牛的URL
    """
    if not hash:
        return ""
    url_tmpl = "http://{domain}/{hash}"
    return url_tmpl.format(domain=IMAGE_URL_DOMAIN, hash=hash)


def get_up_token(key):
    """
    生成上传Token，可以指定过期时间等
    :return:
    """
    token = q.upload_token(BUCKET, key=key, expires=3600, strict_policy=True)
    return {'uptoken': token}
