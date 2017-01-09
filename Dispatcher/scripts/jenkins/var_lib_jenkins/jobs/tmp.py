#!/usr/bin/env python
# coding:utf-8
import os
import shutil


def remove_depth():
    for e in os.scandir(os.curdir):
        if e.is_dir():
            print(f"processing [{e.name}]...")
            for f in os.scandir(e.path):
                if f.is_file() and f.name == 'config.xml':
                    pass
                else:
                    print(f'remove [{f.path}]')
                    shutil.rmtree(f)


if __name__ == '__main__':
    remove_depth()
