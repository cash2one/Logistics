# coding:utf-8
from __future__ import unicode_literals
import sys
import math
from copy import deepcopy
from operator import eq
from ConfigParser import ConfigParser

__all__ = ['ConfUtil', 'ProcessPrint', 'ifnone', 'absolute_round']


class ConfUtil(object):
    def __init__(self, file_path='system.cfg'):
        self.conf = ConfigParser()
        self.conf.read(file_path)

    def get_conf(self):
        return self.conf

    def parse_conf(self, section_name='', option_name='', value_type=str, default_value=None):
        """
        解析配置文件
        @param section_name:    配置节
        @param option_name:     选项名
        @param value_type:      值类型
        @param default_value:   默认值
        @return:
        """
        try:
            if value_type == int:
                return self.conf.getint(section_name, option_name)
            elif value_type == float:
                return self.conf.getfloat(section_name, option_name)
            elif value_type == bool:
                return self.conf.getboolean(section_name, option_name)
            else:
                return self.conf.get(section_name, option_name)
        except:
            return default_value


# 处理进度打印工具
class ProcessPrint(object):
    def __init__(self, total_count, step=50):
        """
        :param total_count: 总量
        :param step: 步长
        :return:
        """
        self.total_count = total_count
        self.step = step
        self.cursor = 0

    def forward(self):
        """
        前进
        :return:
        """
        self.cursor += 1
        if self.cursor > 1 and eq(self.cursor % self.step, 0):
            print '%.1f%%' % (100.0 * self.cursor / self.total_count)


def ifnone(value, unexpected=(None,), default=""):
    return default if value in unexpected else value


def absolute_round(f, n):
    """
    浮点数截断(不四舍五入)
    @param f:
    @param n: 保留的小数位数
    @return:
    """
    return int(f * math.pow(10, n)) * 1.0 / math.pow(10, n)


def convert_string_with_comma_to_list(s, func=None):
    """
    将逗号分隔的字符串转化为列表，去除列表中可能出现的空格并去重
    @param s:
    @param func: callable对象, 对列表中每个元素需要执行的操作
    @return:
    """
    s_list = list(set(s.split(',')))
    if '' in s_list:
        s_list.remove('')
    if callable(func):
        s_list = map(func, s_list)
    return s_list


# 动态加载函数
def get_func(module_name, func_name):
    if module_name not in sys.modules:
        __import__(module_name)
    return getattr(sys.modules[module_name], func_name)


class ReplaceSysPath(object):
    def __init__(self, sys_path):
        self.sys_path = sys_path
        self.old_sys_path = deepcopy(sys.path)

    def __enter__(self):
        # 替换 sys.path 列表
        sys.path = self.sys_path

    def __exit__(self, *args):
        # 恢复原sys.path
        sys.path = self.old_sys_path


def mask_tel(tel):
    """
    将输入的形如 '13245678902' 手机号转化为 '*** *** *** 88'
    :param tel: '13245678902'
    :return: '*** *** *** 88'
    """
    if not tel:
        return ''
    length = len(tel)
    l1 = ['***'] * (length / 3) + [tel[((length / 3) * 3):]]
    return ' '.join(l1)

