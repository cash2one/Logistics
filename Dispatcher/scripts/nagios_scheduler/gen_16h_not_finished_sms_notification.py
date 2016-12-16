#!/usr/bin/env python
# coding:utf-8
from __future__ import print_function
# optparse is Python 2.3 - 2.6, deprecated in 2.7
# For 2.7+ use http://docs.python.org/library/argparse.html#module-argparse
from optparse import OptionParser
import requests
import platform
import datetime
import sys

# Exit statuses recognized by Nagios
UNKNOWN = -1
OK = 0
WARNING = 1
CRITICAL = 2

# Template for reading parameters from commandline
parser = OptionParser()
parser.add_option("-m", "--message", dest="message", default='passed', help="A message to print after OK - ")
(options, args) = parser.parse_args()

# INIT
today = datetime.date.fromordinal(datetime.date.today().toordinal())
check_date = '{}-{}-{}'.format(today.year, today.month, today.day)

node = platform.node()
TIMEOUT = 60 * 1  # 1 minute
# 除非是209(iZ255xsf5qrZ)或者本机, 否则就连PROD的服务.
service_host = "http://dev.api.gomrwind.com" if node in ('iZ255xsf5qrZ', 'localhost') else "http://10.171.103.109"
# 拿端口号
url = service_host + ':5000/port'
resp = requests.get(url, timeout=TIMEOUT)
port = resp.json()
ok, timed_out = True, False
url = service_host + ":" + unicode(port).encode('utf-8') + "/schedule/logic/wholesale_ec/check_unfinished_expr"

try:
    r = requests.post(url, json=None, headers=None, timeout=TIMEOUT)
except UserWarning:
    r = None
    timed_out = True
else:
    print("[POST] [%s]: [%d] [%s]" % (url, r.status_code, r.text[:20] if r.text else '0'), file=sys.stderr)
    if r.status_code / 100 == 2:
        ok, timed_out = True, False
    else:
        ok, timed_out = False, False

# Return output to nagios
# Using the example -m parameter parsed from commandline
if timed_out:
    print('WARN - POST [%s] timed out.' % url)
    raise SystemExit, WARNING
elif not ok:
    print('CRITICAL - POST [%s] failed.' % url)
    raise SystemExit, CRITICAL
else:
    print('OK - POST [%s] done. Sent to [%s] mans.' % (url, r.json() if r and r.json() else ''))
    raise SystemExit, OK
