#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-09-07 15:19:48
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo
import json
import logging
import sys

from models.app import Application

from mongoengine import NotUniqueError
from schema import Schema, And, Use, SchemaError, Optional
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.gmongoengine.paginator import paginator
from tools_lib.gtornado.escape import schema_utf8
from tools_lib.gtornado.http_code import HTTP_201_CREATED
from tools_lib.gtornado.web import BaseRequestHandler
import imp

imp.reload(sys)
sys.setdefaultencoding("utf-8")


class AppHandler(BaseRequestHandler):
    def get(self):
        try:
            data = self.get_query_args()
            data = Schema({
                'app_name': schema_utf8,
                Optional('platform', default='android'): schema_utf8,
                Optional('page', default=1): Use(int),
                Optional('count', default=20): Use(int),
                Optional('limit', default=True): And(Use(int), Use(bool)),
            }).validate(data)
            page = data.pop('page')
            count = data.pop('count')
            limit = data.pop('limit')
        except (SchemaError, Exception):
            logging.exception("参数解析出错")
            self.write_parse_args_failed_response()
            return
        # apps = Application.objects(**data)
        count, apps = paginator(Application.objects(**data), page, count, limit)
        content = [app.format_response() for app in apps]
        self.set_header('X-Resource-Count', count)
        self.write_response(content=content)

    def delete(self):
        try:
            data = self.get_query_args()
            data = Schema({
                'app_name': schema_utf8,
                'platform': schema_utf8,
                'version': Use(int),
            }).validate(data)
        except (SchemaError, Exception):
            logging.exception("参数解析出错")
            self.write_parse_args_failed_response()
            return

        app = Application.objects(**data).delete()
        self.write_no_content_response()


class VersionHandler(BaseRequestHandler):
    def get(self):
        try:
            data = self.get_query_args()
            data = Schema({
                'app_name': schema_utf8,
                'platform': schema_utf8
            }).validate(data)
            app_name = data['app_name']
            platform = data['platform']
        except (SchemaError, Exception):
            logging.exception("参数解析出错")
            self.write_parse_args_failed_response()
            return
        utc_now = TimeZone.utc_now()
        app = Application.objects(
            app_name=app_name,
            platform=platform,
            release_time__lte=utc_now
        ).order_by("-release_time").first()
        if not app:
            self.write_not_found_entity_response()
            return
        self.write_response(content=app.format_response())


class DownloadHandler(BaseRequestHandler):
    def get(self):
        try:
            data = self.get_query_args()
            data = Schema({
                'app_name': schema_utf8,
                'platform': schema_utf8,
                Optional('version', default=0): Use(int),
            }).validate(data)
            app_name = data['app_name']
            platform = data['platform']
            version = data['version']
        except (SchemaError, Exception):
            logging.exception("参数解析出错")
            self.write_parse_args_failed_response()
            return

        utc_now = TimeZone.utc_now()
        if version == 0:
            app = Application.objects(
                app_name=app_name, platform=platform, release_time__lte=utc_now
            ).order_by("-release_time").first()
        else:
            app = Application.objects(app_name=app_name, platform=platform, version=version).first()
        if not app:
            self.write_not_found_entity_response()
            return

        app.update(inc__download_times=1)
        self.write_response(content=app.link)


class ReleaseHandler(BaseRequestHandler):
    def post(self):
        try:
            data = json.loads(self.request.body)
            data = Schema({
                'app_name': schema_utf8,
                'platform': schema_utf8,
                'version': Use(int),
                'link': schema_utf8,
                'changelog': schema_utf8,
                Optional('release_time'): And(schema_utf8, Use(TimeZone.str_to_datetime)),
            }).validate(data)
        except (SchemaError, Exception):
            logging.exception("参数解析出错")
            self.write_parse_args_failed_response()
            return
        try:
            app = Application(**data).save()
            self.write_response(content=app.format_response(), status_code=HTTP_201_CREATED)
            return
        except NotUniqueError:
            self.write_duplicate_entry_response()
            return

    def put(self):
        try:
            data = json.loads(self.request.body)
            data = Schema({
                'app_name': schema_utf8,
                'platform': schema_utf8,
                'version': Use(int),
                'link': schema_utf8,
                'changelog': schema_utf8,
                Optional('release_time'): And(schema_utf8, Use(TimeZone.str_to_datetime)),
            }).validate(data)
            app_name = data.pop('app_name')
            platform = data.pop('platform')
            version = data.pop('version')
        except (SchemaError, Exception):
            logging.exception("参数解析出错")
            self.write_parse_args_failed_response()
            return
        app = Application.objects(app_name=app_name, platform=platform, version=version).first()
        if not app:
            self.write_not_found_entity_response()
            return

        app.modify(**data)
        self.write_response(content=app.format_response(), status_code=HTTP_201_CREATED)


class TimeHandler(BaseRequestHandler):
    def get(self):
        now = TimeZone.utc_now()
        self.write_response(content=TimeZone.datetime_to_str(now))
