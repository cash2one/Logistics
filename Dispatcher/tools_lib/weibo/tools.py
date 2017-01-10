# coding: utf-8


import logging

import weibo
from .conf import WEIBO_CONF


def tiny_url(long_url):
    """
    产生短链接
    :param long_url:
    :return:
    """
    # cli = weibo.Client(**WEIBO_CONF)
    # if isinstance(long_url,(str, unicode)):
    #     params = {"url_long": long_url}
    # elif isinstance(long_url, (list, tuple)):
    #     params = {"url_long": i for i in long_url}
    # else:
    #     assert 0
    #     return
    # ret = cli.get("short_url/shorten", **params)
    # return ret
    return long_url