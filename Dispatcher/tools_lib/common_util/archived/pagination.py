# coding:utf-8
import math

PAGE_ITEM_NUM = 20
PAGE_MAX_ITEM_NUM = 500


def paginator(request, array, func, cursor=None, page=None, count=None):
    if count is None:
        count = PAGE_MAX_ITEM_NUM
    count = int(count)
    if count > PAGE_MAX_ITEM_NUM or count <= 0:
        count = PAGE_MAX_ITEM_NUM
    else:
        count = int(count)
    if cursor is None and page is None:
        rst = split_with_cursor(array, cursor, count, func)
    if cursor is not None and page is not None:
        rst = split_with_page(array, page, count)
    if cursor is None and page is not None:
        rst = split_with_page(array, page, count)
    if cursor is not None and page is None:
        rst = split_with_cursor(array, cursor, count, func)
    if request is not None:
        url = request.path
        url = request.build_absolute_uri(url)
        link_head = rst[2].replace('HOST', url)
    else:
        link_head = ''
    return (rst[0], rst[1], link_head)


def split_with_cursor(array, cursor, count, func):
    if isinstance(array, list):
        array_len = len(array)
    else:
        array_len = array.count()
    link_head_first = '<HOST?cursor=&count=%s>; rel="first",' % (count)
    if cursor == '' or cursor is None:
        rst_list = array[0:count]
        rst_list = list(rst_list)
        link_head_prev = ''
        if array_len <= count:
            link_head_next = ''
            link_head_last = ''
        elif count < array_len <= count * 2:
            link_head_next = '<HOST?cursor=%s&count=%s>; rel="next",' % (func(rst_list[-1]),
                                                                         count)
            link_head_last = '<HOST?cursor=%s&count=%s>; rel="last"' % (func(rst_list[-1]),
                                                                        count)
        elif count * 2 < array_len <= count * 3:
            link_head_next = '<HOST?cursor=%s&count=%s>; rel="next",' % (func(rst_list[-1]),
                                                                         count)
            link_head_last = '<HOST?cursor=%s&count=%s>; rel="last"' % (func(array[count * 2 - 1]),
                                                                        count)
        else:
            link_head_next = '<HOST?cursor=%s&count=%s>; rel="next",' % (func(rst_list[-1]),
                                                                         count)
            if isinstance(array, list):
                array.sort(key=lambda x: x.get("id"), reverse=True)
                _cursor = array[count + 1]
            else:
                total_count = array.count()
                _cursor = array[total_count - count]
            link_head_last = '<HOST?cursor=%s&count=%s>; rel="last"' % (func(_cursor), count)
        link_head = link_head_first + link_head_prev + link_head_next + link_head_last
        rst = (rst_list, array_len, link_head)
        return rst
    cursor = int(cursor)
    index = cursor_find(array, cursor, func)
    if index is None:
        link_head_first = '<HOST?cursor=&count=%s>; rel="first",' % (count)
        if array_len == 0:
            link_head_last = ''
        elif array_len > count:
            if isinstance(array, list):
                array.sort(key=lambda x: x.get("id"), reverse=True)
                _cursor = array[count + 1]
            else:
                total_count = array.count()
                _cursor = array[total_count - count]
            link_head_last = '<HOST?cursor=%s&count=%s>; rel="last"' % (func(_cursor), count)
        else:
            link_head_last = ''
        return ([], array_len, link_head_first + link_head_last)

    rst_list = array[index + 1:index + count + 1]
    rst_list = list(rst_list)
    if index < count:
        link_head_prev = ''
    else:
        link_head_prev = '<HOST?cursor=%s&count=%s>; rel="prev",' % (func(array[index - count]),
                                                                     count)
    if (index + count) >= array_len:
        link_head_next = ''
        link_head_last = '<HOST?cursor=%s&count=%s>; rel="last"' % (cursor,
                                                                    count)
    elif (array_len - (index + 1 + count)) <= count:
        link_head_next = '<HOST?cursor=%s&count=%s>; rel="next",' % (func(rst_list[-1]),
                                                                     count)
        link_head_last = '<HOST?cursor=%s&count=%s>; rel="last"' % (func(rst_list[-1]),
                                                                    count)
    elif (array_len - (index + 1 + count + count)) <= count:
        link_head_next = '<HOST?cursor=%s&count=%s>; rel="next",' % (func(rst_list[-1]),
                                                                     count)
        link_head_last = '<HOST?cursor=%s&count=%s>; rel="last"' % (func(array[index + count * 2]),
                                                                    count)
    else:
        link_head_next = '<HOST?cursor=%s&count=%s>; rel="next",' % (func(rst_list[-1]),
                                                                     count)
        if isinstance(array, list):
            array.sort(key=lambda x: x.get("id"), reverse=True)
            _cursor = array[count + 1]
        else:
            total_count = array.count()
            _cursor = array[total_count - count]
        link_head_last = '<HOST?cursor=%s&count=%s>; rel="last"' % (func(_cursor), count)

    link_head = link_head_first + link_head_prev + link_head_next + link_head_last
    rst = (rst_list, array_len, link_head)
    return rst


def split_with_page(array, page, count):
    if isinstance(array, list):
        array_len = len(array)
    else:
        array_len = array.count()
    page_num = int(math.ceil(array_len / float(count)))
    link_head_first = '<HOST?page=&count=%s>; rel="first",' % count
    link_head_last = '<HOST?page=%s&count=%s>; rel="last"' % (page_num, count)
    try:
        page = int(page)
    except:
        pass
    if page == '' or page is None or page == 1:
        link_head_prev = ''
        rst_list = array[0:count]
        rst_list = list(rst_list)
        if page_num == 1:
            link_head_next = ''
        else:
            link_head_next = '<HOST?page=2&count=%s>; rel="next",' % count
    elif page == page_num and page_num != 1:
        rst_list = array[(page - 1) * count:]
        rst_list = list(rst_list)
        link_head_next = ''
        link_head_prev = '<HOST?page=%s&count=%s>; rel="prev",' % (page - 1,
                                                                   count)
    elif 1 < page < page_num:
        index = (page - 1) * count
        rst_list = array[index:(index + count)]
        rst_list = list(rst_list)
        link_head_next = '<HOST?page=%s&count=%s>; rel="next",' % (page + 1,
                                                                   count)
        link_head_prev = '<HOST?page=%s&count=%s>; rel="prev",' % (page - 1,
                                                                   count)
    elif (page - page_num) == 1:
        rst_list = []
        link_head_next = ''
        link_head_prev = '<HOST?page=%s&count=%s>; rel="prev",' % (page_num,
                                                                   count)
    elif (page - page_num) > 1:
        rst_list = []
        link_head_next = ''
        link_head_prev = ''
    elif page == 0:
        rst_list = []
        link_head_prev = ''
        link_head_next = '<HOST?page=1&count=%s>; rel="next",' % (count)
    elif page < 0:
        rst_list = []
        link_head_next = ''
        link_head_prev = ''
    link_head = link_head_first + link_head_prev + link_head_next + link_head_last
    rst = (rst_list, array_len, link_head)
    return rst


def cursor_find(array, cursor, func):
    for index, obj in enumerate(array):
        if func(obj) == cursor:
            return index
    else:
        return None
