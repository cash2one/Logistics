#!/usr/bin/env python
# coding:utf-8
import logging

RECORD_NORMAL = 0
RECORD_DELETED = 1
RECORD_CHOICE = (
    (RECORD_NORMAL, u'正常'),
    (RECORD_DELETED, u'已删除'),
)


def is_valid_kw(obj, is_update=False, **kw):
    mappings = obj.__mappings__
    if is_update and kw.get('deleted', None) == RECORD_DELETED:
            raise ValueError("Illegal operation: Try to mark %s as deleted with update api." % obj.__name__)
    elif is_update:
        pass
    # 检查是否要求存在的参数都存在
    else:
        args = set(kw.keys())
        required = {key_name for key_name, orm_val in mappings.iteritems() if orm_val.nullable is False and orm_val.primary_key is False}
        required -= {'deleted', 'create_time', 'update_time'}
        if not required.issubset(args):
            raise ValueError("Not providing required args: %s." % list(required-args))
    # 检查参数类型
    for key_name, kv in kw.iteritems():
        if key_name in mappings:
            orm_val = mappings[key_name]
            if orm_val.ddl.find('int') != -1:
                try:
                    int(kv)
                except ValueError:
                    raise ValueError("[%s]:[%s][%s] should be type of [%s]." % (key_name, unicode(kv), type(kv), orm_val.ddl))
            elif orm_val.ddl.find('char') != -1:
                char_len = int(orm_val.ddl[orm_val.ddl.find('(') + 1:orm_val.ddl.find(')')])
                if (not kv) and orm_val.nullable is True:  # 参数值设置可以为空且传入参数就是空
                    continue
                elif not isinstance(kv, unicode) and not isinstance(kv, str):
                    raise ValueError("[%s]:[%s][%s] should be type of str." % (key_name, unicode(kv), type(kv)))
                elif kv and len(kv) > char_len:
                    raise ValueError("[%s]:[%s] should be str of length[%s]." % (key_name, unicode(kv), char_len))
        else:
            logging.warning("[%s]:[%s] won't be passed since [%s] is not valid." % (key_name, unicode(kv), key_name))