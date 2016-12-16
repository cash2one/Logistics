#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
from tornado.httpclient import HTTPRequest

import settings


def redirect_op_data_search(query):
    url = settings.BL_DAS_API_PREFIX + "/express/op_data"
    return HTTPRequest(
        url,
        method="POST",
        body=pickle.dumps(query),
    )

# def redirect_aggregation(pipeline=None):
#     url = settings.BL_DAS_API_PREFIX + "/express/rewards/aggregation"
#     return HTTPRequest(
#         url,
#         method="POST",
#         body=pickle.dumps(pipeline),
#     )
