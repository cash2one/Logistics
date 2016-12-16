# coding: utf-8

from schema import And, Use
from tornado.escape import to_unicode, utf8

schema_unicode_multi = And(Use(utf8), Use(lambda x: [to_unicode(_.strip()) for _ in x.split(',') if _ != ""]))
schema_unicode = And(Use(to_unicode), len)
schema_unicode_empty = Use(to_unicode)  # 允许为空
schema_int = Use(int)
schema_float = And(Use(float), Use(lambda x: round(x, 10)))
schema_float_2 = And(Use(float), Use(lambda x: round(x, 2)))
schema_bool = And(Use(int), Use(bool))
schema_object_id = And(schema_unicode, lambda x: len(x) == 24)

