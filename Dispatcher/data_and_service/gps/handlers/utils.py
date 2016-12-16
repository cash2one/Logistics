#! /usr/bin/env python
# -*- coding: utf-8 -*-
import arrow
from pymongo import GEOSPHERE
from pymongo import MongoClient

from tools_lib.gmongoengine.config import MONGODB_CONFIG

mongo_client = MongoClient(**MONGODB_CONFIG)


def mongodb_router(city_code, day=None):
    if day is None:
        day = arrow.now()
    else:
        day = arrow.get(day, "local")

    db = "city_%s_%s" % (str(city_code), day.strftime("%Y%m"))
    collection = day.strftime("%Y%m%d")
    cdb = mongo_client[db]

    if not collection in cdb.collection_names():
        client = cdb.create_collection(collection)
        client.ensure_index([('loc', GEOSPHERE)])
    else:
        client = cdb[collection]

    return client
