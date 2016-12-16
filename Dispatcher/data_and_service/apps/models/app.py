#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-02-03 09:40:07
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo

from datetime import datetime

from mongoengine import (Document, StringField, IntField, DateTimeField)

from tools_lib.gmongoengine.utils import field_to_json

PLATFORM_ANDROID = 'android'
PLATFORM_IOS = 'ios'

class Application(Document):
    platform = StringField(default=PLATFORM_ANDROID, choices=(PLATFORM_ANDROID, PLATFORM_IOS))
    version = IntField(default=0)
    app_name = StringField(default="app")
    link = StringField(default="")
    changelog = StringField(default="")
    create_time = DateTimeField(default=datetime.utcnow)
    release_time = DateTimeField(default=datetime.utcnow)
    download_times = IntField(default=0)

    meta = {
        'collection': 'application',
        'ordering': [
            '-release_time'
            '-version',
        ],
        'indexes': [
            'version',
            'app_name',
            'release_time',
            {
                'fields': ('app_name', 'platform', 'version'),
                'unique': True
            },
        ]
    }

    def format_response(self):
        json_data = {}
        for field in self:
            value = self[field]
            json_data[field] = field_to_json(value)
        return json_data
