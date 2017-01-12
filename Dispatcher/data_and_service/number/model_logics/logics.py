#!/usr/bin/env python
# coding:utf-8
from tools_lib.transwarp.tz import utc_8_now
from .models import TrackingNumber


class TrackingNumberLogic(object):
    """
    Model logic for TrackingNumber.
    """
    @staticmethod
    def gen():
        kw = dict()
        kw["create_time"] = utc_8_now()
        tn = TrackingNumber(**kw)
        r = tn.insert()
        if r == 1:
            num = TrackingNumber.find_first('max(tracking_number) as tracking_number', '')
            return "%012d" % num
        else:
            raise ValueError("Gen tracking number failed.")
