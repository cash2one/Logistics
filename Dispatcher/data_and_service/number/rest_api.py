#!/usr/bin/env python
# coding:utf-8

from tools_lib.transwarp.web import get, api
from model_logics.logics import TrackingNumberLogic


@api
@get('/tracking_number/gen')
def api_create_payroll_attendance():
    """
    @api {GET} /tracking_number/gen 获取12位面单号
    @apiName tracking_number
    @apiGroup TRACKING_NUMBER

    @apiParamExample Success-Response
        {
            "tracking_number": "000000000026"
        }
    """
    tn = TrackingNumberLogic.gen()
    return {
        "tracking_number": tn
    }
