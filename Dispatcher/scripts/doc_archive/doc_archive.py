#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-08-27 00:26:09
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo

"""Archive Apidoc
Usage:
doc_archive.py [-o=<dir>] [--] <docdir>...
doc_archive.py <docdir>... [-o=<dir>]
doc_archive.py -h | --help

Arguments:
    <docdir> 一个或多个有效的apidoc文档目录

Options:
  -h --help     Show this screen.
  --version     Show version.
  -o <dir>      output dir [default: ./apidoc]
"""

import sys
import os
import json
import shutil
from docopt import docopt

reload(sys)
sys.setdefaultencoding('utf-8')


config = {
    "app": {
        'prefixs': ['ps', 'fh', 'common', 'app'],
        'project': {
            "name": "聚合层 - APP接口",
            "version": "0.1.0",
            "description": "",
            "title": "APP",
        }
    },
    "open": {
        'prefixs': ['open'],
        'project': {
            "name": "聚合层 - 对外接口",
            "version": "0.1.0",
            "description": "",
            "title": "OPEN",
        }
    },
    "front_end": {
        'prefixs': ['fe', 'cloud', 'common'],
        'project': {
            "name": "聚合层 - 前端接口",
            "version": "0.1.0",
            "description": "",
            "title": "FRONT_END",
        }
    },

}

raw_json_path = {
    'api_data': [],
    'api_project': []
}

api_data_js = 'define({ "api": %s });'
api_project_js = 'define( %s );'

api_data_json = {key: [] for key in config}
api_project_json = {key: {} for key in config}

args = docopt(__doc__, version='Archive Apidoc 1.0')
docdir = set(args['<docdir>'])
output_dir = args['-o']


def check():
    global docdir, output_dir

    not_apidoc_dir = set()
    for directory in docdir:
        if not os.path.isdir(directory):
            not_apidoc_dir.add(directory)
            continue
        if not os.path.isfile(directory+'/api_data.js') \
                or not os.path.isfile(directory+'/api_project.js') \
                or not os.path.isfile(directory+'/api_data.json') \
                or not os.path.isfile(directory+'/api_project.json'):
            not_apidoc_dir.add(directory)
            continue

    docdir -= not_apidoc_dir
    if not docdir:
        print("请输入足够多的由apidoc生成的文件夹")
        exit(1)

    if output_dir == './':
        print u"不能指定输出为本文件夹, 请指定一个有效文件夹"
        exit(1)

    if os.path.isfile(output_dir):
        print u"已经存在" + output_dir + u", 并不是一个文件夹"
        exit(1)

    docdir = list(docdir)


def prepare():

    global docdir
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    # 创建template
    template = output_dir + '/template'
    shutil.copytree(docdir[0], template)
    os.unlink(template+'/api_data.js')
    os.unlink(template+'/api_project.js')
    os.unlink(template+'/api_data.json')
    os.unlink(template+'/api_project.json')
    for name in api_data_json:
        path = output_dir + '/' + name
        shutil.copytree(template, path)
    shutil.rmtree(template)

    for directory in docdir:
        raw_json_path['api_data'].append(directory+'/api_data.json')
        raw_json_path['api_project'].append(directory+'/api_project.json')


def main():
    check()
    prepare()

    # archive api_data.json
    for path in raw_json_path['api_data']:
        with open(path) as file_data:
            json_data = json.load(file_data)
            for data in json_data:
                group = data['group'].upper()
                data['groupTitle'] = data['groupTitle'].upper()
                data['group'] = group
                for key in config:
                    value = config[key]
                    for prefix in value['prefixs']:
                        prefix = prefix.upper()
                        if group.startswith(prefix):
                            api_data_json[key].append(data)

    # archive api_project.json
    order = []
    project_json = {}
    for path in raw_json_path['api_project']:
        with open(path) as file_data:
            json_data = json.load(file_data)
            order.extend(json_data['order'])
            project_json = json_data

    # archive api_data.js
    for key in api_project_json:
        data = project_json
        data.update(config[key]['project'])
        data['order'] = order
        with open(output_dir+'/'+key+'/api_project.js', 'w') as output:
            json_str = json.dumps(data, ensure_ascii=False, indent=4)
            outstr = api_project_js % json_str
            output.write(outstr)

    # archive api_project.js
    for key in api_data_json:
        data = api_data_json[key]
        with open(output_dir+'/'+key+'/api_data.js', 'w') as output:
            json_str = json.dumps(data, ensure_ascii=False, indent=4)
            outstr = api_data_js % json_str
            output.write(outstr)

if __name__ == '__main__':
    main()
