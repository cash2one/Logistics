#coding=utf-8

import logging

import requests
from celery_worker import app


@app.task
def send_mail(to_addrs, title, body, content_type='plain'):
    """
    发送邮件
    @param to_addrs:
    @param title:
    @param body:
    @param content_type:
    @return:
    """
    from tools_lib.common_util.mail import send_mail
    send_mail(to_addrs, title, body, content_type)


@app.task(name="async_http_request")
def async_http_request(method, url, **kwargs):
    logging.info("Request {method} to {url} ...".format(method=method, url=url))
    try:
        response = requests.request(
            method=method,
            url=url,
            **kwargs
        )
        return response
    except:
        pass
