#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from mongoengine.connection import connect as _connect, disconnect as _disconnect, DEFAULT_CONNECTION_NAME
from .config import MONGODB_CONFIG


def connect(db=None, alias=DEFAULT_CONNECTION_NAME):
    logging.info("Init mongodb with %s", MONGODB_CONFIG)
    return _connect(db, alias, **MONGODB_CONFIG)


def disconnect(alias=DEFAULT_CONNECTION_NAME):
    logging.info('Disconnect mongodb with %s' % MONGODB_CONFIG)
    return _disconnect(alias)
