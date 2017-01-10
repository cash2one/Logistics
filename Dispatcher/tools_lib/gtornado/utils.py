# coding:utf-8

import json
import logging
from tornado.web import gen
from . import async_requests


# == 生成短链接服务 ==
@gen.coroutine
def tiny_url(long_url):
    shorten_service_url = "http://dwz.cn/create.php"
    my_link = {"url": long_url}
    resp_obj = yield async_requests.session("POST", shorten_service_url, callback=None, data=my_link)
    resp = json.loads(resp_obj.body)
    if resp['status'] == 0:
        raise gen.Return(resp["tinyurl"])
    else:
        logging.warning('Shorten url=[%s] error, msg=[%s]' % (long_url, resp["err_msg"]))
        raise gen.Return(None)


if __name__ == '__main__':
    from tornado.ioloop import IOLoop
    from functools import partial

    f = partial(tiny_url, 'http://cha.123feng.com/sllsdjalsldlakdfaksflkasjfas;fklasjf;alskjfl')
    ret = IOLoop.current().run_sync(f)
    print(("tiny_url: %s" % (ret)))