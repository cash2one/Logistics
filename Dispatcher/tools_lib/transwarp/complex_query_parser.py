#!/usr/bin/env python
# coding:utf-8
import re

UNARY_OPS = ('=', '>', '<', '<=', '>=', 'like', 'regexp', 'regexp binary')
BINARY_OP = 'between'
MULTI_OP = 'in'


def parse_atom_expr(expr, args):
    # 只处理正确的子查询
    if 'is_not' in expr or len(expr) == 1:
        has_not = False
        for key in expr:
            if key == 'is_not':
                has_not = True if expr[key] == 1 else False
            else:
                col = key
                col_op = expr[col].keys()[0]
                col_val = expr[col][col_op]
                # 检查col_op, 看是单元操作符(支持=,<>,>,<,<=,>=,like,regexp,regexp binary), 还是多元操作符(in,between)
                if col_op.strip() in ('=', '<>', '>', '<', '<=', '>=', 'like', 'regexp', 'regexp binary'):
                    expr_str = '%s %s ?' % (col.strip(), col_op.strip())
                    args.append(col_val[0] if isinstance(col_val, list) else col_val)
                elif col_op.strip() == 'in':
                    if not isinstance(col_val, list):
                        raise TypeError("Wrong values for column[%s], should be a list." % col)
                    expr_str = '%s in (%s)' % (col.strip(), ','.join(['?' for _ in xrange(len(col_val))]))
                    args.extend(col_val)
                elif col_op.strip() == 'between':
                    if not isinstance(col_val, list) or (isinstance(col_val, list) and len(col_val) != 2):
                        raise TypeError("Wrong values for column[%s], should be a list of length 2." % col_val)
                    expr_str = '%s between ? and ?' % col.strip()
                    args.extend(col_val)
                else:
                    raise ValueError("Wrong column operation [%s]." % col_op)
        expr_str = 'NOT %s' % expr_str if has_not else expr_str
        return expr_str
    else:
        raise ValueError("Wrong expression json")


def json_to_query_str(expr_json, args):
    op = expr_json['op']
    expr_list = expr_json['exprs']

    if not expr_list:
        return ''

    first_expr = expr_list[0]
    is_atom, expr_str_list = 'is_not' in first_expr or len(first_expr) == 1, []
    for expr in expr_list:
        if is_atom:
            expr_str_list.append(parse_atom_expr(expr, args))
        else:
            # 递归处理非原子子查询
            expr_str = json_to_query_str(expr, args)
            expr_str_list.append(expr_str)
    return '(%s)' % (' %s ' % str(op).strip()).join(expr_str_list)


def build_atom_expr(expr_str):
    # 去掉所有引号. "NOT id = 'str with space' "
    expr_str = re.sub(r'\'|\"|`', '', expr_str).strip()
    atom_json = {}

    # 支持nOT,Not等大小写混用
    ignore_case_not = re.compile(re.escape('not'), re.IGNORECASE)
    if ignore_case_not.search(expr_str):
        atom_json['is_not'] = 1
        # 去掉NOT
        expr_str = ignore_case_not.sub('', expr_str).strip()

    # 去掉not以后的部分
    ignore_case_unary = re.compile(r'(=|>|<|<=|>=|like|regexp|regexp binary)', re.IGNORECASE)
    ignore_case_binary = re.compile(r'(between|and)', re.IGNORECASE)
    ignore_case_mul = re.compile(r'(in|\(|\))', re.IGNORECASE)
    # 如果是一元操作符 'id = ? '
    if ignore_case_unary.search(expr_str):
        col_op_val = ignore_case_unary.split(expr_str)
        # print ("col_op_val=%s" % col_op_val)
        if len(col_op_val) != 3:
            raise ValueError("Invalid expr atom[%s]." % expr_str)
        else:
            col, op, val = col_op_val[0].strip(), col_op_val[1].strip().upper(), col_op_val[2].strip()
            atom_json[col] = {}
            atom_json[col][op] = val
            return atom_json
    # 如果是二元操作符 'create_time between ? and ? '
    elif ignore_case_binary.search(expr_str):
        col_op_val = ignore_case_binary.split(expr_str)
        if len(col_op_val) != 5:
            raise ValueError("Invalid expr atom[%s]." % expr_str)
        else:
            col, op = col_op_val[0].strip(), col_op_val[1].strip().upper()
            v1, v2 = col_op_val[2].strip(), col_op_val[4].strip()
            atom_json[col] = {}
            atom_json[col][op] = [v1, v2]
            return atom_json
    # 如果是多元操作符 'id in (?,?,?) '
    elif ignore_case_mul.search(expr_str):
        col_op_val = ignore_case_mul.split(expr_str)
        for token in col_op_val:
            if not token or token.isspace():
                col_op_val.remove(token)
        if len(col_op_val) < 5 or col_op_val[2].strip() != '(' or col_op_val[-1].strip() != ')':
            raise ValueError("Invalid expr atom[%s]." % expr_str)
        else:
            col, op = col_op_val[0].strip(), col_op_val[1].strip().upper()
            val = col_op_val[3].split(',')
            val = [x.strip() for x in val if x and x.strip()]
            atom_json[col] = {}
            atom_json[col][op] = val
            return atom_json


def build_atom(atom_str):
    # no (), always 3 splits
    # ['NOT id = ? ', 'AND', ' status in (?,?,?) OR to_status = ?']
    ignore_case_op = re.compile(r'(AND|OR)', re.IGNORECASE)
    expr_list = ignore_case_op.split(atom_str, 3)
    expr_list = [e.strip() for e in expr_list if e and e.strip()]


def parse_page_count(kwargs):
    """
    只能DAS用,因为会改变page和count的原始值
    :param kwargs:
    :return:
    """
    page, count = int(kwargs.get('page', 1)), int(kwargs.get('count', 20))
    # 分页参数必须是数字,否则用默认1; 每页个数也必须是数字,否则用默认20
    try:
        page = int(page) - 1
        _cnt = int(count) - 1
        if page < 0:
            page = 0
        if _cnt < 0:
            count = 20
    except ValueError:
        page = 0
        count = 20
    return page, count


def complex_query(kwargs):
    """
    用于类似下面的接口抽象complex_query部分的处理.
    使用示例:
        filter_col_str, where, group_by_limit, args = complex_query(ctx.request.input())
        return FlowLogic.find_by(filter_col_str, where, group_by_limit, *args)
    @api {post} /shop/flow/complex_query/:page 商户资金流水复杂查询
    @apiDescription 查询商户余额,消费金额等.
    @apiName api_retrieve_flow
    @apiGroup shop

    @apiParam {list} filter_col `["shop_id", "cash" ...]`. 表`flow`中的字段列表. `[]`表示取所有字段.
    @apiParam {str} [group_by] 按照什么来group by. 表`flow`中的字段. 如`shop_id`.
    @apiParam {str} op `AND`或者`OR`. 表示如何组合过滤条件.
    @apiParam {int} is_not 如果有这个key, 则表示该字段上的过滤条件要取非.
    @apiParam {int} page 2. 表示第二页, 从1开始. [1:2147483648), 分页查. <=20条数据, 一次返回所有; >20条, 一次返回20条.

    @apiParamExample {json} 请求body示例:
        {
            "filter_col": ["shop_id", "sum(cash) as paid"],
            "query":
                {
                    "op": "AND",
                    "exprs": [
                        {"shop_id": {"in": ["56c2d708a785c90ab0014d00", "56c2d708a785c90ab0014d00"]}},
                        {"type": {"like": "%PAY%"}},
                        {"is_not":1, "shop_name": {"like": "%测试%"}}
                    ]
                },
            "group_by": "shop_id"
        }
    @apiParamExample {json} 对于"query"部分的解释 expr_json_example:
        expr_json_atom = {
            "op": "AND",
            "exprs": [
                {"shop_id": {"in": ["56c2d708a785c90ab0014d00", "56c2d708a785c90ab0014d00"]}},
                {"type": {"like": "%PAY%"}},
                {"is_not":1, "shop_name": {"like": "%测试%"}}
            ]
        }

        expr_json_level_2 = {
            "op": "OR",
            "exprs": [
                expr_json_atom,
                # expr_json_atom,
            ]
        }

    @apiSuccessExample {json} 成功示例(filter_col列表长度是1,即查询单个值时):
        HTTP/1.1 200 OK
        [0.01, 0.02, 0.5, 0.0]

    @apiSuccessExample {json} 成功示例(filter_col列表长度大于1,即查询多个值时):
        HTTP/1.1 200 OK
        [
            {
                "shop_id": "56c2d708a785c90ab0014d00",
                "paid": 0.23
            }
        ]
    """
    page, count = parse_page_count(kwargs)
    # 处理查询col
    filter_col = kwargs['filter_col']
    if isinstance(filter_col, list) and len(filter_col) != 0:
        filter_col_str = ','.join(filter_col)
    else:
        filter_col_str = '*'
    # 处理查询条件
    query_json = kwargs.query
    group_by = kwargs.get('group_by')
    order_by = kwargs.get('order_by')
    args = []
    query = json_to_query_str(query_json, args)
    where = 'where %s' % query if query else ''
    where = '%s order by %s' % (where, order_by) if order_by else where
    where = '%s group by %s' % (where, group_by) if group_by else where
    limit = 'limit %d,%d' % ((page * count), count)
    # ctx.response.set_header("ALICE", "alice")
    return filter_col_str, where, limit, args


def query_str_to_json(atom_str):
    atom = {'op': None, 'exprs': []}

    # 简单校验
    # if len(expr_list) % 2 == 0:
    #     raise ValueError("Invalid expr json atom str(no (), same op):[%s]." % atom_str)
    # 真正的处理
    # else:
    #     return atom


def test_json_to_sql():
    expr_json_atom = {
        'op': 'AND',
        'exprs': [
            {'is_not': 0, 'staff_id': {'=': 0}},
            {'status': {'in': ['FIN', 'ERR', 'ERR_VALID']}},
            {'to_status': {'=': ['CHECK_RESIGN']}},

        ]
    }

    expr_json_level_2 = {
        'op': 'AND',
        'exprs': [
            expr_json_atom,
            expr_json_atom,
        ]
    }

    expr_json_example = {
        'op': 'OR',
        'exprs': [
            expr_json_level_2,
            # expr_json_level_2,
            # expr_json_level_2,
        ]
    }
    put_my_args_here = []

    print "In [1]:\n %s\n\n" % expr_json_example
    print "Out [1]:\n %s\n" % json_to_query_str(expr_json_example, put_my_args_here)
    print "Out [2]:\n %s\n" % put_my_args_here


def test_sql_to_json():
    print build_atom_expr('NOT id = 0 ')
    print build_atom_expr('NOT id=1 ')
    print build_atom_expr("Not create_time BeTween '2015-11-21' And '2015-11-30' ")
    print build_atom_expr("Not id in (0 , 1,'str with space' )")
    print build_atom_expr(" id Not in (0 , 1,'str with space' )")
    print build_atom_expr(" id in (0 , 1,'str with space' )")
    print build_atom_expr("DATE(`create_time`)='2015-11-23' ")

    print build_atom(" id in (0 , 1,'str with space' )")
    print build_atom("DATE(`create_time`)='2015-11-23' AND `to_status`='CHECK_RESIGN'")


# 跑我
if __name__ == '__main__':
    # SELECT to_status, create_time, `deliveryman_id` FROM
    # (SELECT max(`id`) AS latest_id FROM `deliveryman_fsm_log` GROUP BY `deliveryman_id`) AS la
    # INNER JOIN `deliveryman_fsm_log` ON la.latest_id=id WHERE DATE(`create_time`)='2015-11-23'
    # AND `to_status`='CHECK_RESIGN';

    # select deliveryman_id, to_status from deliveryman_fsm_log
    # where id in (select max(id) from deliveryman_fsm_log group by deliveryman_id) and to_status = 'CHECK_RESIGN'
    test_json_to_sql()
