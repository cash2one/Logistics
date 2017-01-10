# coding:utf-8
"""
Utilities for reading and writing xls/xlsx sheets
"""
__all__ = ["xls_reader", "xls_writer",
           "xlsx_reader", "xlsx_writer",
           "SheetNotFound", ]

import time
from hashlib import md5
from logging import info

import os
import xlrd
import xlwt
from tools_lib.common_util.sstring import safe_unicode

# a temporary folder to save files
TMP_DIR = "/tmp"

# filename template
XLS_FILENAME_TMPL = "md-%s.xls"
XLSX_FILENAME_TMPL = "md-%s.xlsx"


# 表未找到异常
class SheetNotFound(Exception): pass


def _generate_filename(x):
    """
    产生一个文件名
    :param x: 是否为xlsx后缀
    :return: 文件绝对路径
    """
    if x:
        name = XLSX_FILENAME_TMPL
    else:
        name = XLS_FILENAME_TMPL
    return os.path.join(
        TMP_DIR,
        name % md5("%s" % time.time()).hexdigest()
    )


def _save_to_file(x, byte_content):
    """
    将xls/xlsx内容存入文件
    :param byte_content: 文件内容
    :return: 文件绝对路径
    """
    full_filename = _generate_filename(x)
    with open(full_filename, mode="w") as z:
        z.write(byte_content)
    return full_filename


def _read_from_file(filename):
    """
    读取文件的二进制内容
    :param filename: 文件绝对路径
    :return: 二进制内容
    """
    with open(filename, "rb") as z:
        ret = z.read()
    return ret


def xls_reader(xls_file_content, sheet=0):
    """
    将一个xls文件读成包含列表的列表

    [
        ["a0", "b0", ...], ...
        ["a1", "b1", ...], ...
    ]

    :param xls_file_content: xls文件的二进制内容
    :param sheet: 读取表的顺序,0表示第一张
    :return: list of list
    """
    filename = _save_to_file(x=False, byte_content=xls_file_content)
    info("wrote xls to: " + filename)
    info("=========================")
    xls_file_obj = xlrd.open_workbook(filename)
    try:
        the_sheet = xls_file_obj.sheets()[sheet]
    except:
        raise SheetNotFound("sheet %s not found." % sheet)
    rest = []
    for row_num in range(the_sheet.nrows):
        rest.append(the_sheet.row_values(row_num))
    return rest


def xls_writer(list_of_list, sheet_name="Sheet1"):
    """
    将一个包含列表的列表写成xls文件

    [
        ["a0", "b0", ...], ...
        ["a1", "b1", ...], ...
    ]

    :param list_of_list: list of list
    :return: xls文件的二进制内容
    """
    xls_file_obj = xlwt.Workbook()
    the_sheet = xls_file_obj.add_sheet(sheet_name, cell_overwrite_ok=True)
    current_row = 0
    for row in list_of_list:
        current_column = 0
        for column in row:
            the_sheet.write(current_row, current_column, safe_unicode(column))
            current_column += 1
        current_row += 1

    filename = _generate_filename(x=False)
    xls_file_obj.save(filename)
    info("wrote xls to: " + filename)
    info("=========================")
    return _read_from_file(filename)


def xlsx_reader(xlsx_file_content, sheet=0):
    """
    将一个xlsx文件读成包含列表的列表

    [
        ["a0", "b0", ...], ...
        ["a1", "b1", ...], ...
    ]

    :param xlsx_file_content: xlsx文件的二进制内容
    :param sheet: 读取表的顺序,0表示第一张
    :return: list of list
    """
    # FIXME
    return []


def xlsx_writer(list_of_list):
    """
    将一个包含列表的列表写成xlsx文件

    [
        ["a0", "b0", ...], ...
        ["a1", "b1", ...], ...
    ]

    :param list_of_list: list of list
    :return: xlsx文件的二进制内容
    """
    # FIXME
    return b""
