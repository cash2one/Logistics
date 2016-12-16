# coding=utf-8


def dot_string_to_list(s, dot=",", item_type=str, allow_spaces=False):
    """
    逗号分割字符串转list
    :param s: 文本
    :param dot:分割的符号
    :param item_type:输出list的每个item的类型,默认文本
    :param allow_spaces:允许输出的list每个item带有可能的前导或者后置空格,默认不允许
    """
    if allow_spaces:
        return [item_type(i) for i in s.split(dot) if i]
    else:
        return [item_type(i.strip()) for i in s.split(dot) if i]


def list_to_dot_string(l, dot=",", serializer=str):
    """
    list转逗号分割字符串
    :param l: list
    :param dot: 分割的符号
    :param serializer: 序列化
    """
    return dot.join([serializer(i) for i in l if i])


def bool_vs_query_string(val):
    """
    转换bool和query string里面的bool
    "1" <=> True
    "0" <=> False
    :param val:
    :return:
    """
    if isinstance(val, str) or isinstance(val, unicode):
        val = val.lower().strip()
        if val in ("true", "1", u"true", u"1"):
            return True
        elif val in ("false", "0", u"false", u"0"):
            return False
        else:
            raise Exception("bad value, can't be converted into bool")

    else:
        if val:
            return "1"
        else:
            return "0"
