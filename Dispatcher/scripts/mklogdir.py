#!/usr/bin/env python
# coding: utf-8

"""Archive Apidoc
Usage:
mklogdir.py <file> [-o=<dir>]
mklogdir.py -h | --help

Arguments:
    <file> supervisor配置文件

Options:
  -h --help     Show this screen.
  --version     Show version.
"""

import sys
from os import makedirs
from os.path import dirname, isdir, abspath
from docopt import docopt
import imp

imp.reload(sys)
sys.setdefaultencoding('utf-8')

# args = docopt(__doc__, version="make log dir from supervisor config 1.0")
# config = args['<file>']

if __name__ == '__main__':
    args = docopt(__doc__, version="make log dir from supervisor config 1.0")
    config = args['<file>']

    with open(config, 'r') as f:
        for line in f:
            token = line.strip().split('=')
            if len(token) != 2 or token[0] != 'stdout_logfile':
                continue

            logfile = token[1]
            logdir = abspath(dirname(logfile))
            if isdir(logdir):
                continue
            else:
                print(("mkdir: %s" % (logdir)))
                makedirs(logdir)
