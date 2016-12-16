#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-12-01 19:56:43
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo
import logging
from mongoengine.connection import connect as _connect, DEFAULT_CONNECTION_NAME
from .config import MONGODB_CONFIG


def connect(db=None, alias=DEFAULT_CONNECTION_NAME):
    logging.info("Init mongodb with %s", MONGODB_CONFIG)
    return _connect(db, alias, **MONGODB_CONFIG)
