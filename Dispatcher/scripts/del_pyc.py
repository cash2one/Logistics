# coding=utf-8
import os


def del_pyc(path):
    what = os.scandir(path)
    for entry in what:
        print(entry)
        if entry.is_file() and entry.name[-4:] == '.pyc':
            os.remove(entry.path)
        elif entry.is_dir():
            del_pyc(entry.path)


if __name__ == '__main__':
    path = '/Users/chenxinlu/Developer/Logistics/'
    del_pyc(path)
