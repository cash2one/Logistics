# -*- coding:utf-8 -*-
import sys
from .celery_worker import app


def normal_task(func, func_args=None, func_kwargs=None, **kwargs):
    """
    :param func: 函数对象
    :param func_args: 函数的参数 list
    :param func_kwargs: 函数的参数 dict
    :param args: celery send_task方法的参数
    :param kwargs: celery send_task方法的参数
    :return:
    """
    # 参数检查
    if func_args is not None and not isinstance(func_args, list):
        raise Exception('invalid func_args type')
    if func_kwargs is not None and not isinstance(func_kwargs, dict):
        raise Exception('invalid func_kwargs type')

    args_list = [sys.path, func.__module__, func.__name__]
    if func_args is None:
        func_args = []
    func_args = args_list + func_args
    app.send_task('common_async_task', args=func_args, kwargs=func_kwargs, **kwargs)


def async_http_request(method, url, func_kwargs=None, **kwargs):
    """
    异步http请求
    :param method: 请求类型: "GET","POST","PATCH",...
    :param url: 请求的地址
    :param func_kwargs: requests参数
    :param kwargs: celery参数
    :return:
    """
    if func_kwargs is not None and not isinstance(func_kwargs, dict):
        raise Exception('invalid func_kwargs type')
    app.send_task("async_http_request", args=(method, url), kwargs=func_kwargs, **kwargs)
