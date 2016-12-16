# coding: utf-8
from __future__ import unicode_literals

import logging
from tornado import gen
from schema import SchemaError, Schema, Optional, Or

from tools_lib.gtornado.escape import schema_unicode, schema_unicode_empty, schema_objectid
from tools_lib.gtornado.web2 import ReqHandler

from models import Evaluate


# ===> 发货端、收货者评价 <===
class EvaluateHandler(ReqHandler):
    @gen.coroutine
    def post(self):
        try:
            data = Schema({
                Optional("call_id"): schema_objectid,
                "number": schema_objectid,
                "origin": {
                    "origin_type": Or(lambda x: x in ("node_0", "node_n")),
                    Optional("id"): schema_unicode,
                    "name": schema_unicode_empty,
                    "tel": schema_unicode
                },
                "rate": Or(lambda x: x in (1,2,3,4,5)),
                "comment": schema_unicode_empty
            }).validate(self.get_body_args())
            
            number = data["number"]
            origin_type = data["origin"]["origin_type"]
            tel = data["origin"]["tel"]
            the_id = data["origin"].get("id", None)
        except SchemaError as e:
            self.resp_error(e.message)
            return
        if origin_type=="node_0":
            # 如果是发货端
            if_has_posted = Evaluate.objects(number=number, origin__origin_type=origin_type, origin__id=the_id, origin__tel=tel).first()
        elif origin_type=="node_n":
            # 如果是收货人
            if_has_posted = Evaluate.objects(number=number, origin__origin_type=origin_type, origin__tel=tel).first()
        else:
            return
        if if_has_posted:
            # 防止重复打分
            self.resp_forbidden("您已经评价过了。")
            return
        Evaluate(**data).save()
        self.resp_created({"message": "评价成功。"})
