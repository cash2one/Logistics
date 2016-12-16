#!/usr/bin/env python
# coding:utf-8
from __future__ import unicode_literals

import sys

import arrow
import os

# === 模块自己的PYTHON_PATH, 让代码找到正确的tools_lib. ==>要在所有import前做!!!
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from tools_lib.windchat import shortcuts, conf

if __name__ == '__main__':
    r = [
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "56cc1eceeed0932e60a16967",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 30 20 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "测试01站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "测试01站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56d69b1feed0933e20bd52db",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56c687617f452563e439bca6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56ca62717f452563e439bcbe",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57308687eed09355a9bcd88d",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5722cbc2eed093650ba389fe",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "573531eceed09352ae25b366",
            "node_name": "滨江站",
            "reg_cron": "0 0 1 * * ?"
        },
        {
            "deliver_id": "56cd6144eed0934b1621f25f",
            "node_name": "滨江站",
            "reg_cron": "0 0 1 * * ?"
        },
        {
            "deliver_id": "56c91d817f452563e439bcba",
            "node_name": "滨江站",
            "reg_cron": "0 0 1 * * ?"
        },
        {
            "deliver_id": "5746e300eed093097a440687",
            "node_name": "萧山站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "574664faeed09301c48d75f4",
            "node_name": "萧山站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57465344eed09301c48d75d5",
            "node_name": "萧山站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5746536ceed09301c48d75d6",
            "node_name": "萧山站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "星耀城",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "573140c7eed09355a9bcd8ad",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57302beaeed09355a9bcd872",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56c91d817f452563e439bcba",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "573140c7eed09355a9bcd8ad",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "57302beaeed09355a9bcd872",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "56c91d817f452563e439bcba",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "56cd6144eed0934b1621f25f",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "57302beaeed09355a9bcd872",
            "node_name": "滨江站",
            "reg_cron": "0 0 1 * * ?"
        },
        {
            "deliver_id": "573140c7eed09355a9bcd8ad",
            "node_name": "滨江站",
            "reg_cron": "0 0 1 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "滨江站",
            "reg_cron": "0 0 1 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "星耀城",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "星耀城",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "星耀城",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "星耀城",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "星耀城",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "星耀城",
            "reg_cron": "0 0 24 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "星耀城",
            "reg_cron": "0 0 24 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "星耀城",
            "reg_cron": "0 0 24 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "星耀城",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "星耀城",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "星耀城",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "星耀城",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "星耀城",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 13 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "57159ff2eed0937b8a6f5fb7",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "滨江站",
            "reg_cron": "0 0 1 * * ?"
        },
        {
            "deliver_id": "573140c7eed09355a9bcd8ad",
            "node_name": "滨江站",
            "reg_cron": "0 0 1 * * ?"
        },
        {
            "deliver_id": "57302beaeed09355a9bcd872",
            "node_name": "滨江站",
            "reg_cron": "0 0 1 * * ?"
        },
        {
            "deliver_id": "573c0dd8eed0933252f6d9c2",
            "node_name": "萧山站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5746536ceed09301c48d75d6",
            "node_name": "萧山站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57465344eed09301c48d75d5",
            "node_name": "萧山站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "574664faeed09301c48d75f4",
            "node_name": "萧山站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "573c0dd8eed0933252f6d9c2",
            "node_name": "萧山站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "5746536ceed09301c48d75d6",
            "node_name": "萧山站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "57465344eed09301c48d75d5",
            "node_name": "萧山站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "574664faeed09301c48d75f4",
            "node_name": "萧山站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "5746e300eed093097a440687",
            "node_name": "萧山站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "573c0dd8eed0933252f6d9c2",
            "node_name": "萧山站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "5746536ceed09301c48d75d6",
            "node_name": "萧山站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "57465344eed09301c48d75d5",
            "node_name": "萧山站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "574664faeed09301c48d75f4",
            "node_name": "萧山站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "5746e300eed093097a440687",
            "node_name": "萧山站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "星耀城",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "星耀城",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "星耀城",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "星耀城",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "星耀城",
            "reg_cron": "0 30 15 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "星耀城",
            "reg_cron": "0 30 15 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "星耀城",
            "reg_cron": "0 30 15 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "星耀城",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "星耀城",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "星耀城",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "56cc1eceeed0932e60a16967",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "5719e73beed09376976b367d",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "573531eceed09352ae25b366",
            "node_name": "星耀城",
            "reg_cron": "0 30 15 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "星耀城",
            "reg_cron": "0 30 15 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "星耀城",
            "reg_cron": "0 30 15 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "星耀城",
            "reg_cron": "0 30 15 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 30 20 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 30 20 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 7 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "测试01站",
            "reg_cron": "0 0 13 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 30 20 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "测试01站",
            "reg_cron": "0 0 7 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 12 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 12 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 19 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 19 * * ?"
        },
        {
            "deliver_id": "56c7c2527f452563e439bcb3",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 19 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 19 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 16 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "573c0dd8eed0933252f6d9c2",
            "node_name": "萧山站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "5746536ceed09301c48d75d6",
            "node_name": "萧山站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "57465344eed09301c48d75d5",
            "node_name": "萧山站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "574664faeed09301c48d75f4",
            "node_name": "萧山站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "573c0dd8eed0933252f6d9c2",
            "node_name": "萧山站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "5746536ceed09301c48d75d6",
            "node_name": "萧山站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "57465344eed09301c48d75d5",
            "node_name": "萧山站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "574664faeed09301c48d75f4",
            "node_name": "萧山站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "5746e300eed093097a440687",
            "node_name": "萧山站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56c7c2527f452563e439bcb3",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "测试01站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56c7c2527f452563e439bcb3",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 14 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 14 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 14 * * ?"
        },
        {
            "deliver_id": "56c7c2527f452563e439bcb3",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 14 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 14 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 50 16 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 50 16 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 50 16 * * ?"
        },
        {
            "deliver_id": "56c7c2527f452563e439bcb3",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 50 16 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 50 16 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "57159ff2eed0937b8a6f5fb7",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "测试01站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 13 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "测试01站",
            "reg_cron": "0 0 13 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 13 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "测试01站",
            "reg_cron": "0 0 13 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 30 20 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "测试01站",
            "reg_cron": "0 30 20 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "测试01站",
            "reg_cron": "0 0 8 * * ?"
        },
        {
            "deliver_id": "56f4ac4beed0932e4a19c026",
            "node_name": "测试01站",
            "reg_cron": "0 0 7 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "测试01站",
            "reg_cron": "0 0 7 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56c7c2527f452563e439bcb3",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 0 10 * * ?"
        },
        {
            "deliver_id": "56c7c2527f452563e439bcb3",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 12 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 12 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 12 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 12 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 12 * * ?"
        },
        {
            "deliver_id": "56c7c2527f452563e439bcb3",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 12 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 12 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 12 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 12 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 14 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 14 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 14 * * ?"
        },
        {
            "deliver_id": "56c7c2527f452563e439bcb3",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 14 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 14 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 14 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 50 16 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 50 16 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 50 16 * * ?"
        },
        {
            "deliver_id": "56c7c2527f452563e439bcb3",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 50 16 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 50 16 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 50 16 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 19 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 19 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 19 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 19 * * ?"
        },
        {
            "deliver_id": "56c7c2527f452563e439bcb3",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 19 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 19 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "庆春长堤明苑站",
            "reg_cron": "0 30 19 * * ?"
        },
        {
            "deliver_id": "56c91d817f452563e439bcba",
            "node_name": "滨江站",
            "reg_cron": "0 0 1 * * ?"
        },
        {
            "deliver_id": "56cd6144eed0934b1621f25f",
            "node_name": "滨江站",
            "reg_cron": "0 0 1 * * ?"
        },
        {
            "deliver_id": "56cd6144eed0934b1621f25f",
            "node_name": "滨江站",
            "reg_cron": "0 0 13 * * ?"
        },
        {
            "deliver_id": "56c91d817f452563e439bcba",
            "node_name": "滨江站",
            "reg_cron": "0 0 13 * * ?"
        },
        {
            "deliver_id": "57302beaeed09355a9bcd872",
            "node_name": "滨江站",
            "reg_cron": "0 0 13 * * ?"
        },
        {
            "deliver_id": "573140c7eed09355a9bcd8ad",
            "node_name": "滨江站",
            "reg_cron": "0 0 13 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "滨江站",
            "reg_cron": "0 0 13 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "永裕大厦站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "57465539eed09301c48d75e2",
            "node_name": "永裕大厦站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "5719b1f8eed09376976b367c",
            "node_name": "永裕大厦站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "永裕大厦站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "57465539eed09301c48d75e2",
            "node_name": "永裕大厦站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "5719b1f8eed09376976b367c",
            "node_name": "永裕大厦站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "永裕大厦站",
            "reg_cron": "0 30 15 * * ?"
        },
        {
            "deliver_id": "57465539eed09301c48d75e2",
            "node_name": "永裕大厦站",
            "reg_cron": "0 30 15 * * ?"
        },
        {
            "deliver_id": "5719b1f8eed09376976b367c",
            "node_name": "永裕大厦站",
            "reg_cron": "0 30 15 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "永裕大厦站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "57465539eed09301c48d75e2",
            "node_name": "永裕大厦站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "5719b1f8eed09376976b367c",
            "node_name": "永裕大厦站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 16 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 16 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 16 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "5719b1f8eed09376976b367c",
            "node_name": "永裕大厦站",
            "reg_cron": "0 10 9 * * ?"
        },
        {
            "deliver_id": "57465539eed09301c48d75e2",
            "node_name": "永裕大厦站",
            "reg_cron": "0 10 9 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "永裕大厦站",
            "reg_cron": "0 10 9 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 20 13 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 50 2 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 50 14 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 50 8 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 20 11 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 0 18 * * ?"
        },
        {
            "deliver_id": "56cd6144eed0934b1621f25f",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "573140c7eed09355a9bcd8ad",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57302beaeed09355a9bcd872",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56c91d817f452563e439bcba",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56cd6144eed0934b1621f25f",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "滨江站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "573140c7eed09355a9bcd8ad",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "57302beaeed09355a9bcd872",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "56c91d817f452563e439bcba",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "56cd6144eed0934b1621f25f",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "滨江站",
            "reg_cron": "0 30 11 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "573140c7eed09355a9bcd8ad",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "57302beaeed09355a9bcd872",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "56c91d817f452563e439bcba",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "56cd6144eed0934b1621f25f",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "573140c7eed09355a9bcd8ad",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "57302beaeed09355a9bcd872",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "56c91d817f452563e439bcba",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "56cd6144eed0934b1621f25f",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "滨江站",
            "reg_cron": "0 30 13 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "滨江站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "滨江站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "滨江站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "滨江站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "56fb30b5eed093338d22a919",
            "node_name": "滨江站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "56fb5435eed0931146f39762",
            "node_name": "滨江站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "573c0dd8eed0933252f6d9c2",
            "node_name": "萧山站",
            "reg_cron": "0 20 13 * * ?"
        },
        {
            "deliver_id": "5746536ceed09301c48d75d6",
            "node_name": "萧山站",
            "reg_cron": "0 20 13 * * ?"
        },
        {
            "deliver_id": "57465344eed09301c48d75d5",
            "node_name": "萧山站",
            "reg_cron": "0 20 13 * * ?"
        },
        {
            "deliver_id": "574664faeed09301c48d75f4",
            "node_name": "萧山站",
            "reg_cron": "0 20 13 * * ?"
        },
        {
            "deliver_id": "5746e300eed093097a440687",
            "node_name": "萧山站",
            "reg_cron": "0 20 13 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 20 13 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 16 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 16 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 16 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 16 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 11 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 11 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 11 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 11 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 13 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 13 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 13 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 13 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "56e17b28eed093310861162b",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 18 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 18 * * ?"
        },
        {
            "deliver_id": "56c6f9207f452563e439bcb2",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 18 * * ?"
        },
        {
            "deliver_id": "572dcb4eeed0932ce1cac122",
            "node_name": "九堡客运中心站",
            "reg_cron": "0 50 18 * * ?"
        },
        {
            "deliver_id": "5746e300eed093097a440687",
            "node_name": "萧山站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "573c0dd8eed0933252f6d9c2",
            "node_name": "萧山站",
            "reg_cron": "0 50 8 * * ?"
        },
        {
            "deliver_id": "5746536ceed09301c48d75d6",
            "node_name": "萧山站",
            "reg_cron": "0 50 8 * * ?"
        },
        {
            "deliver_id": "57465344eed09301c48d75d5",
            "node_name": "萧山站",
            "reg_cron": "0 50 8 * * ?"
        },
        {
            "deliver_id": "574664faeed09301c48d75f4",
            "node_name": "萧山站",
            "reg_cron": "0 50 8 * * ?"
        },
        {
            "deliver_id": "5746e300eed093097a440687",
            "node_name": "萧山站",
            "reg_cron": "0 50 8 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 50 8 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 50 8 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 50 8 * * ?"
        },
        {
            "deliver_id": "573c0dd8eed0933252f6d9c2",
            "node_name": "萧山站",
            "reg_cron": "0 20 11 * * ?"
        },
        {
            "deliver_id": "5746536ceed09301c48d75d6",
            "node_name": "萧山站",
            "reg_cron": "0 20 11 * * ?"
        },
        {
            "deliver_id": "57465344eed09301c48d75d5",
            "node_name": "萧山站",
            "reg_cron": "0 20 11 * * ?"
        },
        {
            "deliver_id": "574664faeed09301c48d75f4",
            "node_name": "萧山站",
            "reg_cron": "0 20 11 * * ?"
        },
        {
            "deliver_id": "5746e300eed093097a440687",
            "node_name": "萧山站",
            "reg_cron": "0 20 11 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 20 11 * * ?"
        },
        {
            "deliver_id": "5746e300eed093097a440687",
            "node_name": "萧山站",
            "reg_cron": "0 0 15 * * ?"
        },
        {
            "deliver_id": "573c0dd8eed0933252f6d9c2",
            "node_name": "萧山站",
            "reg_cron": "0 50 14 * * ?"
        },
        {
            "deliver_id": "5746536ceed09301c48d75d6",
            "node_name": "萧山站",
            "reg_cron": "0 50 14 * * ?"
        },
        {
            "deliver_id": "57465344eed09301c48d75d5",
            "node_name": "萧山站",
            "reg_cron": "0 50 14 * * ?"
        },
        {
            "deliver_id": "574664faeed09301c48d75f4",
            "node_name": "萧山站",
            "reg_cron": "0 50 14 * * ?"
        },
        {
            "deliver_id": "5746e300eed093097a440687",
            "node_name": "萧山站",
            "reg_cron": "0 50 14 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 50 14 * * ?"
        },
        {
            "deliver_id": "573c0dd8eed0933252f6d9c2",
            "node_name": "萧山站",
            "reg_cron": "0 0 18 * * ?"
        },
        {
            "deliver_id": "5746536ceed09301c48d75d6",
            "node_name": "萧山站",
            "reg_cron": "0 0 18 * * ?"
        },
        {
            "deliver_id": "57465344eed09301c48d75d5",
            "node_name": "萧山站",
            "reg_cron": "0 0 18 * * ?"
        },
        {
            "deliver_id": "574664faeed09301c48d75f4",
            "node_name": "萧山站",
            "reg_cron": "0 0 18 * * ?"
        },
        {
            "deliver_id": "5746e300eed093097a440687",
            "node_name": "萧山站",
            "reg_cron": "0 0 18 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 0 18 * * ?"
        },
        {
            "deliver_id": "56f4e40ceed0932e4a19c027",
            "node_name": "萧山站",
            "reg_cron": "0 0 0 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "笕桥物美站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56cbc7d57f45254a62bd8d22",
            "node_name": "笕桥物美站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "5732dcd5eed0934f5b378325",
            "node_name": "笕桥物美站",
            "reg_cron": "0 30 9 * * ?"
        },
        {
            "deliver_id": "56cbc7d57f45254a62bd8d22",
            "node_name": "笕桥物美站",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "笕桥物美站",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "5732dcd5eed0934f5b378325",
            "node_name": "笕桥物美站",
            "reg_cron": "0 0 12 * * ?"
        },
        {
            "deliver_id": "5732dcd5eed0934f5b378325",
            "node_name": "笕桥物美站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "56cbc7d57f45254a62bd8d22",
            "node_name": "笕桥物美站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "笕桥物美站",
            "reg_cron": "0 0 14 * * ?"
        },
        {
            "deliver_id": "5732dcd5eed0934f5b378325",
            "node_name": "笕桥物美站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56cbc7d57f45254a62bd8d22",
            "node_name": "笕桥物美站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "笕桥物美站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "5732dcd5eed0934f5b378325",
            "node_name": "笕桥物美站",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "56cbc7d57f45254a62bd8d22",
            "node_name": "笕桥物美站",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "56c66f1c7f452563e439bca4",
            "node_name": "笕桥物美站",
            "reg_cron": "0 0 19 * * ?"
        },
        {
            "deliver_id": "5719b1f8eed09376976b367c",
            "node_name": "永裕大厦站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "57465539eed09301c48d75e2",
            "node_name": "永裕大厦站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "5705d790eed093542eb1ea11",
            "node_name": "永裕大厦站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "573531eceed09352ae25b366",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56c69a547f452563e439bca8",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56c7feb07f452563e439bcb5",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56e77a2beed09357197042b6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "574654a4eed09301c48d75dc",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56e3958beed0937dd471ea73",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 0 9 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "56e77a2beed09357197042b6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "56c7feb07f452563e439bcb5",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "56e3958beed0937dd471ea73",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "56c69a547f452563e439bca8",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "56e77a2beed09357197042b6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "56c7feb07f452563e439bcb5",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "56e3958beed0937dd471ea73",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "56c69a547f452563e439bca8",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "574654a4eed09301c48d75dc",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 11 * * ?"
        },
        {
            "deliver_id": "56e77a2beed09357197042b6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "56c7feb07f452563e439bcb5",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "56e3958beed0937dd471ea73",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "56c69a547f452563e439bca8",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "56e77a2beed09357197042b6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "56c7feb07f452563e439bcb5",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "56e3958beed0937dd471ea73",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "56c69a547f452563e439bca8",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "574654a4eed09301c48d75dc",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 13 * * ?"
        },
        {
            "deliver_id": "56e3958beed0937dd471ea73",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56e77a2beed09357197042b6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56c7feb07f452563e439bcb5",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "574654a4eed09301c48d75dc",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56e3958beed0937dd471ea73",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56e77a2beed09357197042b6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56c7feb07f452563e439bcb5",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "574654a4eed09301c48d75dc",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56c69a547f452563e439bca8",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 40 15 * * ?"
        },
        {
            "deliver_id": "56c811a27f452563e439bcb6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "574654a4eed09301c48d75dc",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "56e3958beed0937dd471ea73",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "56c69a547f452563e439bca8",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "56c7feb07f452563e439bcb5",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "56e77a2beed09357197042b6",
            "node_name": "黄龙国际中心站",
            "reg_cron": "0 20 18 * * ?"
        },
        {
            "deliver_id": "56cc0f9aeed0932e60a16966",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "5732a5d7eed0934f5b37831b",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "57346c8beed09352ae25b357",
            "node_name": "测试01站",
            "reg_cron": "0 0 23 * * ?"
        },
        {
            "deliver_id": "573d1de2eed093128e9c743d",
            "node_name": "测试01站",
            "reg_cron": "0 0 12 * * ?"
        }
    ]

    ret = {}
    for it in r:
        ts = it['reg_cron'].split(' ')
        hour = int(ts[2])
        mi = int(ts[1])
        t = arrow.now().replace(hour=hour if hour != 24 else 0, minute=int(mi))
        # print it['deliver_id'], it['node_name'], t.format(fmt='HH:mm')

        man_id = it['deliver_id']
        node_name = it['node_name']
        t = t.format(fmt='HH:mm')

        if man_id not in ret:
            ret[man_id] = set()

        msg = '%s  %s' % (t, node_name)
        # msg = msg.encode('utf-8')
        ret[man_id].add(msg)

    for man, msgs in ret.iteritems():
        # print man
        ret[man] = sorted(msgs)
        # for msg in ret[man]:
        #     print msg

    # mans = ret.keys()
    mans = ['57495a7213be31882eea2c3e']
    # 发风信
    for one_id in mans:
        try:
            client_id = shortcuts.account_query(account={"account_id": one_id, "account_type": conf.ACCOUNT_TYPE_MAN})
            msg = '\n'.join(ret[one_id])
            if client_id:
                shortcuts.channel_send_message(
                    client_id,
                    message_type=conf.MSG_TYPE_DELIVERY_ALERT,
                    content=msg,
                    summary=msg,
                    description="线路提醒"
                )
                print("Sending windchat to driver(%s):\n%s" % (client_id, msg))
            else:
                print("Windchat not sent because client_id_list is empty.")
        except Exception as e:
            print(e)
    # for one_id in mans:
    #     man = get_man_info_from_id(one_id)
    #     tel = man.get('tel')
    #     if tel:
    #         msg = '\n'.join(ret[one_id])
    #         print("Sending sms to driver(%s):\n%s" % (tel, msg))
    #         async_send_sms(tel, msg, SMS_TYPE_NORMAL)
    #         with open("dada.txt", 'a+') as f:
    #             lines = "\nSending sms to driver(%s):\n%s" % (tel, msg)
    #             f.write(lines.encode('utf-8'))
