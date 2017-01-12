#!/usr/bin/env python
# coding: utf-8
# @Date    : 2015-11-09 19:56:43
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo

from bson import ObjectId
from datetime import datetime
from mongoengine import EmbeddedDocument, Document

UTC_DATE_TIME_PATTERN = '%Y-%m-%dT%H:%M:%SZ'


def field_to_json(value):
    ret = value
    if isinstance(value, ObjectId):
        ret = str(value)
    elif isinstance(value, datetime):
        ret = value.strftime(UTC_DATE_TIME_PATTERN)
    elif isinstance(value, EmbeddedDocument):
        if hasattr(value, "format_response"):
            ret = value.format_response()
        elif hasattr(value, "pack"):
            ret = value.pack()
    elif isinstance(value, Document):
        if hasattr(value, "format_response"):
            ret = value.format_response()
        elif hasattr(value, "pack"):
            ret = value.pack()
        else:
            ret = str(value.id)
    elif isinstance(value, list):
        ret = [field_to_json(_) for _ in value]
    elif isinstance(value, dict):
        ret = {k: field_to_json(v) for k, v in list(value.items())}
    elif isinstance(value, float):
        ret = round(value, 2)
    return ret


def field_to_json_no_round(value):
    ret = value
    if isinstance(value, ObjectId):
        ret = str(value)
    elif isinstance(value, datetime):
        ret = value.strftime(UTC_DATE_TIME_PATTERN)
    elif isinstance(value, EmbeddedDocument):
        if hasattr(value, "format_response"):
            ret = value.format_response()
        elif hasattr(value, "pack"):
            ret = value.pack()
    elif isinstance(value, Document):
        if hasattr(value, "format_response"):
            ret = value.format_response()
        elif hasattr(value, "pack"):
            ret = value.pack()
        else:
            ret = str(value.id)
    elif isinstance(value, list):
        ret = [field_to_json_no_round(_) for _ in value]
    elif isinstance(value, dict):
        ret = {k: field_to_json_no_round(v) for k, v in list(value.items())}
    elif isinstance(value, float):
        ret = round(value, 10)
    return ret

def deduce_expect_fields(all_fields, excludes, includes, only):
    excludes = excludes if excludes else ()
    includes = includes if includes else ()
    only = only if only else ()

    if not only:
        # 如果only为空, 不返回 <excludes> + watchers, 额外返回 includes
        expected = (set(all_fields) | set(includes)) - set(excludes)
    else:
        expected = set(only)

    return expected
