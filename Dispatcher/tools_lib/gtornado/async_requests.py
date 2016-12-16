# coding=utf-8

import json
import logging
from tornado.httputil import url_concat
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

json_dumps = json.dumps


def session(method, url, callback=None, raise_error=False,
            params=None, body=None, json=None,
            headers=None,
            **kwargs):
    """Executes a request, asynchronously returning an `HTTPResponse`.

    This method returns a `.Future` whose result is an
    `HTTPResponse`.  By default, the ``Future`` will raise an `HTTPError`
    if the request returned a non-200 response code. Instead, if
    ``raise_error`` is set to False, the response will always be
    returned regardless of the response code.

    If a ``callback`` is given, it will be invoked with the `HTTPResponse`.
    In the callback interface, `HTTPError` is not automatically raised.
    Instead, you must check the response's ``error`` attribute or
    call its `~HTTPResponse.rethrow` method.

    :param method: HTTP method, e.g. "GET" or "POST"
    :param url: URL to fetch
    :param params: (optional) Dictionary or bytes to be sent in the query
        string
    :param body: (optional) HTTP request body as a string (byte or unicode; if unicode
        the utf-8 encoding will be used)
    :param json: (optional) json to send in the body
    :param data: (optional) Deprecated! json to send in the body
    :param headers: (optional) Dictionary of HTTP Headers to send
    """

    # prepare params
    url = url_concat(url, params)

    # prepare body
    headers = headers or {}
    if json is not None:
        headers['Content-Type'] = "application/json"
        body = json_dumps(json)

    # prepare timeout
    kwargs.setdefault('request_timeout', 5)
    kwargs.setdefault('connect_timeout', 5)

    # prepare request
    request = HTTPRequest(url, method=method, body=body, headers=headers, **kwargs)

    return fetch(request, callback=callback, raise_error=raise_error)


def fetch(request, callback=None, raise_error=False):
    # AsyncHTTPClient 与 IOLoop.current() 挂钩, 默认是从缓存里面拿
    # 如果在此之前有人调用过AsyncHTTPClient的话, 则max_clients会是10
    http_client = AsyncHTTPClient(max_clients=100)
    if http_client.max_clients < 100:
        http_client = AsyncHTTPClient(force_instance=True, max_clients=100)

    # 暂时先这样
    # logging.debug("method[%s], url[%s], body[%s].", request.method, request.url, request.body)

    return http_client.fetch(request, callback=callback, raise_error=raise_error)


def get(url, params=None, callback=None, **kwargs):
    # url = url_concat(url, params)
    return session("GET", url, callback=None, params=params, **kwargs)


def post(url, json=None, body=None, callback=None, **kwargs):
    return session("POST", url, callback=None, json=json, body=body, **kwargs)


def patch(url, json=None, body=None, callback=None, **kwargs):
    return session("PATCH", url, callback=None, json=json, body=body, **kwargs)


def put(url, json=None, body=None, callback=None, **kwargs):
    return session("PUT", url, callback=None, json=json, body=body, **kwargs)


def delete(url, params=None, callback=None, **kwargs):
    # url = url_concat(url, params)
    return session("DELETE", url, callback=None, params=params, **kwargs)


def head(url, callback=None, **kwargs):
    return session("HEAD", url, callback=None, **kwargs)
