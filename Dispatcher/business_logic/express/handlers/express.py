# coding: utf-8


import json
import logging
import pickle
import traceback
from collections import defaultdict

import arrow
import psycopg2
from .api import query_fence_point_within
from .fsm_call import CallFSM
from .fsm_expr import ExprFSM
from haversine import haversine
from .models import ApiError, DuplicateDocError
from .models import ClientAddress
from .models import Express, Call, Node, Schedule, Fence
from mongoengine import Q
from schema import Schema, Optional, Use, And, SchemaError
from tools_lib.bl_call import CallState
from tools_lib.bl_expr import ExprState
from tools_lib.common_util import xls, sstring
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.gedis.core_redis_key import key_nodes, key_schedule_today
from tools_lib.gedis.gedis import Redis
from tools_lib.gmongoengine.paginator import paginator
from tools_lib.gtornado.apis import get_fee
from tools_lib.gtornado.apis import shop_pay
from tools_lib.gtornado.escape import (schema_utf8, schema_utf8_empty, schema_unicode, schema_utf8_multi, schema_bool,
                                       schema_int, schema_float_2, schema_receiver, schema_float, schema_objectid,
                                       schema_node_x_unicode, schema_operator_unicode, schema_shop_unicode,
                                       schema_unicode_multi)
from tools_lib.gtornado.web2 import ReqHandler
from tools_lib.host_info import DEBUG, PROD_POSTGRESQL_INNER_IP, PROD_POSTGRESQL_OUTER_IP
from tools_lib.transwarp.escape import schema_unicode_empty
from tools_lib.windchat import http_utils
from tools_lib.windchat import shortcuts, conf
from tornado import gen
from functools import reduce

# == postGre ==
if DEBUG is True:
    IP_POSTGRE = PROD_POSTGRESQL_OUTER_IP
else:
    IP_POSTGRE = PROD_POSTGRESQL_INNER_IP
# == redis ==
redis_client = Redis()


class SearchHandler(ReqHandler):
    def check_search_args(self):
        try:
            data = Schema({
                Optional("number"): schema_utf8,
                Optional("term"): schema_unicode,
                Optional("term_keys", default=["number"]): schema_utf8_multi,

                Optional("status"): And(schema_utf8_multi, Use(lambda l: [_.upper() for _ in l])),
                Optional("sub_status"): And(schema_utf8_multi, Use(lambda l: [_.upper() for _ in l])),

                Optional("creator_id"): schema_utf8_empty,
                Optional("creator_type"): schema_utf8_empty,
                Optional('creator_name'): schema_unicode_empty,  # 这个有可能是中文, 用unicode才可以查询
                Optional('no_test', default=False): schema_bool,

                Optional("assignee_id"): schema_utf8_empty,
                Optional("assignee_type"): schema_utf8_empty,
                Optional("assignee_tel"): schema_utf8_empty,

                Optional("time_type", default='create_time'): schema_utf8,
                Optional("start_time"): Use(TimeZone.str_to_datetime),
                Optional("end_time"): Use(TimeZone.str_to_datetime),

                Optional("third_party_name"): schema_utf8_empty,
                Optional("third_party_order_id"): schema_utf8_empty,

                Optional("fence_id"): schema_utf8_empty,
                Optional("fence_name"): schema_unicode_empty,

                # watcher这两个参数需要一起给
                Optional("watcher_id"): schema_utf8_empty,
                Optional("watcher_tel"): schema_unicode,
                Optional("watcher_type"): schema_utf8_empty,

                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("includes", default=None): schema_utf8_multi,
                Optional("excludes", default=None): schema_utf8_multi,
                Optional("only", default=None): schema_utf8_multi,
                Optional("order_by", default=['-update_time']): schema_utf8_multi,
            }).validate(self.get_query_args())

        except Exception as e:
            logging.exception(e.message)
            self.resp_error("参数解析失败.")
            return None, False

        return data, True

    def build_search_query(self, data):
        base_query_list = []
        status_query_list = []

        # 查询number可以查询两种单号
        term_keys_map = {
            "third_party_order_id": "third_party__order_id__icontains",
            "receiver_tel": "node__node_n__tel__icontains",
            "receiver_name": "node__node_n__name__icontains",
        }

        def parse_terms(term_keys, term):
            query = Q()
            for key in term_keys:
                query_key = term_keys_map.get(key, key + "__icontains")
                query |= Q(**{query_key: term})
            return query

        if data.get("term"):
            base_query_list.append(parse_terms(data['term_keys'], data['term']))
        if data.get('number'):
            base_query_list.append(Q(number__icontains=data['number']))

        # creator 相关
        if data.get('creator_id'):
            base_query_list.append(Q(creator__id=data['creator_id']))
        if data.get('creator_type'):
            base_query_list.append(Q(creator__m_type=data['creator_type']))
        if data.get('creator_name'):
            base_query_list.append(Q(creator__name__icontains=data['creator_name']))
        if data.get("no_test"):
            base_query_list.append(Q(creator__name__not__contains="测试"))

        # assignee/occupant 相关
        if data.get('assignee_id'):
            base_query_list.append(Q(assignee__id=data['assignee_id']) | Q(occupant__id=data['assignee_id']))
        if data.get('assignee_type'):
            base_query_list.append(Q(assignee__m_type=data['assignee_type']))
        if data.get('assignee_tel'):
            base_query_list.append(Q(assignee__tel__icontains=data['assignee_tel']))

        # watcher
        watcher = {}
        if data.get('watcher_id'):
            watcher['id'] = data['watcher_id']
        if data.get('watcher_type'):
            watcher['m_type'] = data['watcher_type']
        if data.get('watcher_tel'):
            watcher['tel'] = {'$regex': data['watcher_tel'], '$options': 'i'}
        if watcher:
            base_query_list.append(Q(watchers__match=watcher))

        # 第三方 相关
        if data.get('third_party_name'):
            base_query_list.append(Q(third_party__name=data['third_party_name']))
        if data.get('third_party_order_id'):
            base_query_list.append(Q(third_party__order_id=data['third_party_order_id']))

        # fence 相关
        if data.get('fence_id'):
            base_query_list.append(Q(node__node_n__fence__id=data['fence_id']))
        if data.get('fence_name'):
            base_query_list.append(Q(node__node_n__fence__name__icontains=data['fence_name']))

        # 时间相关
        time_type = data.pop('time_type', "create_time")
        if time_type not in ("create_time", "update_time"):
            # 除了create_time和update_time其他的时间在times里面
            time_type = "times__" + time_type
        if data.get('start_time'):
            base_query_list.append(Q(**{time_type + "__gte": data['start_time']}))
        if data.get('end_time'):
            base_query_list.append(Q(**{time_type + "__lte": data['end_time']}))

        # status 相关
        if data.get('status'):
            status_query_list.append(Q(status__status__in=data['status']))
        if data.get('sub_status'):
            status_query_list.append(Q(status__sub_status__in=data['sub_status']))

        base_query = reduce(lambda x, y: x & y, base_query_list) if base_query_list else Q()
        status_query = reduce(lambda x, y: x & y, status_query_list) if status_query_list else Q()

        return base_query, status_query


class AggregateStatusHandler(SearchHandler):
    @gen.coroutine
    def get(self):
        data, ok = self.check_search_args()
        if not ok:
            return
        base_query, _ = self.build_search_query(data)

        result = Express.objects(base_query).aggregate(
            {
                "$group": {
                    "_id": {"status": "$status.status", "sub_status": "$status.sub_status",
                            "m_type": "$assignee.m_type"},
                    "expr_count": {"$sum": 1}
                }
            }
        )

        content = defaultdict(lambda: defaultdict(int))
        content['status'] = defaultdict(int)
        content['sub_status'] = defaultdict(int)

        content['status'].update({
            ExprState.STATUS_PRE_CREATED: 0,
            ExprState.STATUS_CREATED: 0,
            ExprState.STATUS_SENDING: 0,
            ExprState.STATUS_FINISHED: 0,
        })
        content['sub_status'].update(
            {status: 0 for status in (ExprState.CREATED | ExprState.SENDING | ExprState.FINISHED)}
        )

        result = list(result)
        t = TimeZone.decrement_hours(TimeZone.utc_now(), 72)

        validating = Express.objects(
            base_query & Q(status__sub_status=ExprState.SUB_STATUS_FINISHED, times__parttime_tt_time__gte=t)).count()
        valid = Express.objects(
            base_query & Q(status__sub_status=ExprState.SUB_STATUS_FINISHED, times__parttime_tt_time__lt=t)).count()
        content['sub_status']["VALIDATING"] = validating
        content['sub_status']["VALID"] = valid

        for doc in result:
            status = doc['_id']['status']
            sub_status = doc['_id']['sub_status']
            m_type = doc["_id"].get('m_type', "")
            count = doc['expr_count']

            content["status"][status] += count
            content["sub_status"][sub_status] += count
            # default dict
            content[m_type][sub_status] += count
            # if m_type in content and sub_status in content[m_type]:
            #     content[m_type][sub_status] += count
            # else:
            #     content[m_type][sub_status] = count
        self.resp(content=content)


class AggregationHandler(SearchHandler):
    @gen.coroutine
    def post(self):
        data, ok = self.check_search_args()
        if not ok:
            return
        base_query, status_query = self.build_search_query(data)

        try:
            pipeline = pickle.loads(self.request.body)
        except Exception as e:
            logging.exception(e.message)
            self.resp_args_error(e.message)
            return
        result = Express.objects(base_query & status_query).aggregate(*pipeline)

        content = [doc for doc in result]
        self.resp(content=content)


# ==> 更强大的列表/搜索
class PickleSearchHandler(ReqHandler):
    @gen.coroutine
    def post(self):
        try:
            data = pickle.loads(self.request.body)

            data = Schema({
                Optional(object): object,
                Optional("Q", default=Q()): object,
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("includes", default=None): list,
                Optional("excludes", default=None): list,
                Optional("only", default=None): list,
                Optional("order_by", default=['-update_time']): list,
            }).validate(data)

            page = data.pop('page')
            count = data.pop('count')
            limit = data.pop('limit')
            includes = data.pop('includes')
            excludes = data.pop('excludes')
            only = data.pop('only')
            order_by = data.pop('order_by')
            query = data.pop("Q")

        except Exception as e:
            logging.exception(e.message)
            self.resp_args_error()
            return
        try:
            q = Q(**data) & query
            logging.debug(q.to_query(Express))
            count, expr_list = paginator(Express.objects(q).order_by(*order_by), page, count, limit)
        except Exception:
            logging.exception(data)
            self.resp_args_error()
            return

        self.set_header('X-Resource-Count', count)
        self.resp([expr.pack(includes=includes, excludes=excludes, only=only)
                   for expr in expr_list])


# ==> 发货端: 可下单, 可送达
class CanBeServed(ReqHandler):
    # == 以下从于昕那里取: 放redis,ttl=24h ==
    @staticmethod
    def _get_orbit_and_schedule():
        orbit_str = redis_client.get(key_nodes)
        schedule_today_str = redis_client.get(key_schedule_today)
        # 如果站点信息或者今日线路信息任一一个过期, 重新取一遍数据库
        if (not orbit_str) or (not schedule_today_str):
            try:
                conn = psycopg2.connect(host=IP_POSTGRE, port='5432', database='tlbs', user='postgres',
                                        password='feng123')
            except Exception as e:
                print((e.message))
                return None, None

            cursor = conn.cursor()
            cursor.execute("""select
            c.node_id,c.deliver_id,c.reg_cron,d.node_name,ST_AsGeoJSON(d.loc) as loc,d.node_address
            from
                (select a.node_id,a.deliver_id,b.reg_cron from trans.bs_trans_bind_node_info as a
                left join trans.bs_trans_reg_time as b
                on a.cron_id=b.id
                where a.status = 1 and a.deliver_id is not NULL) as c
            left join trans.bs_trans_node_info as d
            on c.node_id=d.node_id;""")
            # node_id                              deliver_id                   reg_cron        node_name loc                                                        node_address
            # 11e603b4722edfd025342a53cbd7fae9    56fb30b5eed093338d22a919    0 30 9 * * ?    星耀城    {"type":"Point","coordinates":[120.221344,30.219355]}    杭州市滨江区星耀城
            _orbit = []
            _schedule_today = {}

            nodes = {}
            for record in cursor:
                ts = record[2].split(' ')
                hour = int(ts[2])
                mi = int(ts[1])
                t = arrow.now().replace(hour=hour if hour != 24 else 0, minute=int(mi))

                unicode_record = []
                for col in record:
                    if isinstance(col, str):
                        unicode_record.append(col.decode('utf-8'))
                    else:
                        unicode_record.append(col)

                man_id = unicode_record[1]
                node_id = unicode_record[0]
                node_name = unicode_record[3]
                node_address = unicode_record[5]
                t = t.format(fmt='HH:mm')
                coordinates = json.loads(unicode_record[4])['coordinates']
                coordinates = (coordinates[1], coordinates[0])  # (30.0, 120.0)把纬度放在前面

                # 捞nodes来算orbit: t没排序
                if node_id not in nodes:
                    nodes[node_id] = dict(coordinates=coordinates, name=node_name, id=node_id, t=[t])
                else:
                    nodes[node_id]['t'].append(t)

                # 算schedule_today: run没排序
                footprint = dict(coordinates=coordinates, name=node_name, id=node_id, t=t)
                if man_id not in _schedule_today:
                    _schedule_today[man_id] = dict(run=[footprint])
                else:
                    _schedule_today[man_id]['run'].append(footprint)

            conn.close()

            # 算orbit, 给t排序
            for key in nodes:
                node = nodes[key]
                t_list = node['t']
                node['t'] = sorted(t_list)
                _orbit.append(node)

            # 给schedule_today[man_id][run]排序
            for key in _schedule_today:
                schedule = _schedule_today[key]
                schedule['run'] = sorted(schedule['run'], cmp=lambda x, y: cmp(x['t'], y['t']))
        else:
            _orbit = json.loads(orbit_str)
            _schedule_today = json.loads(schedule_today_str)
            return _orbit, _schedule_today

        # print(json.dumps(_orbit, ensure_ascii=False, indent=2))
        # print(json.dumps(_schedule_today, ensure_ascii=False, indent=2))
        return _orbit, _schedule_today

    # == 解空间: 放redis,ttl=24h ==
    @staticmethod
    def _pre_calculated(_schedule_today):
        # Tn: t_pn+T派件; t_p0 > t0+T收件
        _answers = {}
        for driver in _schedule_today:
            run = _schedule_today[driver]['run']
            M = len(run)
            for i in range(M):
                for j in range(i, M):
                    px = run[i]
                    py = run[j]
                    # u'p1 p2'
                    key = '%s %s' % (px['id'], py['id'])
                    if key not in _answers:
                        _answers[key] = []
                    _answers[key].append({'driver': driver, 'x': px, 'y': py})
        for a_key in _answers:
            # print(a_key, len(_answers[a_key]))
            pass
        # print(json.dumps(answers[a_key], ensure_ascii=False, indent=2, default=_dump))
        return _answers

    # == 优先计算服务时间 ==
    @staticmethod
    def _out_of_service_time(place_order_time, _orbit, prompts):
        service_s, service_e = '09:00', '17:00'
        for p in _orbit:
            start = min(p['t'])
            if start < service_s:
                service_s = start
            end = max(p['t'])
            if end > service_e:
                service_e = end
        if place_order_time < service_s or place_order_time > service_e:
            over_time = '已经超过我们的服务时间啦, 请在(%s,%s)内下单哦' % (service_s, service_e)
            logging.info(over_time)
            prompts.append(over_time)
        else:
            in_time = '好棒! 没超过我们的服务时间, 下单时间[%s]在(%s,%s)内哦' % (place_order_time, service_s, service_e)
            logging.info(in_time)
            prompts.append(in_time)

    # == 输出1: 推荐始发站点, 推荐目的站点 ==
    @staticmethod
    def _find_nearby(_node, _orbit, prompts):
        limit_km_sj, limit_km_pj = 3, 5
        limit_count = 5
        _s0, _sn = [], []
        n0 = (_node['node_0']['lat'], _node['node_0']['lng'])
        nn = (_node['node_n']['lat'], _node['node_n']['lng'])
        for p in _orbit:
            # 算始发站点
            dist_0 = haversine(p['coordinates'], n0)
            if dist_0 < limit_km_sj:
                if len(_s0) < limit_count:
                    _s0.append(dict(point=p, dist=dist_0, n0=n0))
                else:
                    _s0 = sorted(_s0, cmp=lambda x, y: cmp(x['dist'], y['dist']))
                    max_dist = _s0[-1]['dist']
                    if dist_0 < max_dist:
                        _s0[-1] = dict(point=p, dist=dist_0, n0=n0)
            # 算目的站点
            dist_n = haversine(p['coordinates'], nn)
            if dist_n < limit_km_pj:
                if len(_sn) < limit_count:
                    _sn.append(dict(point=p, dist=dist_n, nn=nn))
                else:
                    _sn = sorted(_sn, cmp=lambda x, y: cmp(x['dist'], y['dist']))
                    max_dist = _sn[-1]['dist']
                    if dist_n < max_dist:
                        _sn[-1] = dict(point=p, dist=dist_n, nn=nn)
        # print('始发站点:')
        # print(json.dumps(_node['node_0'], ensure_ascii=False, indent=2))
        # print(json.dumps([dict(dist=_s['dist'], name=_s['point']['name']) for _s in _s0], ensure_ascii=False, indent=2))
        # print('目的站点:')
        # print(json.dumps(_node['node_n'], ensure_ascii=False, indent=2))
        # print(json.dumps([dict(dist=_s['dist'], name=_s['point']['name']) for _s in _sn], ensure_ascii=False, indent=2))
        msg = ''
        if _s0 and _sn:
            msg = '找到可用站点, 需要进一步匹配时间和路线信息'
        if not _s0:
            msg = '找不到可用始发站点: 寄件地址太远了, 没法收件哦'
        if not _sn:
            msg = '找不到可用目的站点: 收件地址太远了, 没法派件哦'
        logging.info(msg)
        prompts.append(msg)
        return _s0, _sn

    # == 输出2: 根据解空间推荐线路 ==
    @staticmethod
    def _make_guesses(_s0, _sn, _answers, _t0, prompts):
        recommend = {}
        _cnt = 0
        for i in _s0:
            for j in _sn:
                _cnt += 1
                p0_id, p1_id = i['point']['id'], j['point']['id']
                p = '%s %s' % (p0_id, p1_id)
                if p in _answers:
                    ans_list = _answers[p]
                    last = max([ans['x']['t'] for ans in ans_list])
                    msg = ('[✪✪✪][解%s] 找到一条路线能从[%s]到[%s], 进一步匹配时间信息, 收件站点末班车时间为[%s], 预计收件完成时间为[%s], %s.' % (
                        _cnt, i['point']['name'], j['point']['name'], last, _t0,
                        '您将错过末班车' if last < _t0 else '时间充裕,请尽快联系客户'))
                    logging.info(msg)
                    prompts.append(msg)
                    for ans in ans_list:
                        # 如果s0和sn中存在同一个站点, 优先推荐(不需要上车,直接派件)
                        if p0_id == p1_id:
                            recommend[p] = [
                                dict(confidence=1, driver='', x=i['point'], y=j['point'])]
                        # 需要赶车
                        elif ans['x']['t'] > _t0:  # todo: 改成t0+t收件预计
                            if p not in recommend:
                                recommend[p] = []
                            # ans['confidence'] = 0.9  # todo: 改成根据合理的min(tx),min(ty)来给推荐指数
                            recommend[p].append(ans)
                else:
                    msg = ('[   ][解%s] 没有一条路线能从[%s]到[%s].' % (_cnt, i['point']['name'], j['point']['name']))
                    logging.info(msg)
                    prompts.append(msg)

        if not recommend:
            msg = '找不到任何时段的可行路线: [预计明日送达]'
        else:
            msg = '找到推荐(始发 终点 可选班次)个数为: %s, [预计今日送达]' % len(recommend)
        prompts.append(msg)

        for px_py in recommend:
            print((px_py, len(recommend[px_py])))
            print((json.dumps(recommend[px_py], ensure_ascii=False, indent=2)))
        return recommend

    @gen.coroutine
    def post(self):
        try:
            kw = Schema({
                # 'node_0': schema_acceptance_unicode
                'node_0': {
                    'addr': schema_unicode_empty,
                    'lat': schema_float,
                    'lng': schema_float,
                },
                'node_n': {
                    'addr': schema_unicode_empty,
                    'lat': schema_float,
                    'lng': schema_float,
                }
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        _t0 = arrow.now()
        prompts = []
        t0 = _t0.replace(minutes=+90).to("local").format('HH:mm')
        orbit, schedule_today = self._get_orbit_and_schedule()
        answers = self._pre_calculated(schedule_today)
        self._out_of_service_time(_t0.to('local').format('HH:mm'), orbit, prompts)
        s0, sn = self._find_nearby(kw, orbit, prompts)
        recommend = self._make_guesses(s0, sn, answers, t0, prompts)
        _t1 = arrow.now()

        msg = '搜寻解空间耗时: %s ' % (_t1 - _t0)
        logging.info(msg)
        prompts.append(msg)

        self.resp(dict(orbit=orbit, s0=s0, sn=sn, recommend=recommend, prompts=prompts))


# ==> 发货端: 一键呼叫
class OneKeyCall(ReqHandler):
    @gen.coroutine
    def post(self):
        try:
            kw = Schema({
                'shop': schema_shop_unicode,
                'count': schema_int
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        try:
            shop = kw['shop']
            loc = {
                'lat': shop['lat'],
                'lng': shop['lng'],
                'address': shop['address'],
                'fence': {
                    "id": "x",
                    "name": "___",
                    "node": {}
                }
            }
            # 0. 百度定位失败
            if kw['shop']['lat'] == 0.0 or kw['shop']['lng'] == 0.0:
                c = Call(shop_id=shop['id'], shop_name=shop['name'], shop_tel=shop['tel'], loc=loc, count=kw['count'],
                         status=CallState.STATUS_CLOSED, msg='呼叫失败，无法定位')
                c.save()
                self.resp_error('抱歉！呼叫失败，无法定位')
                return
            # 1. 找到收件围栏
            fence = Fence.objects(node__id__exists=True, points__geo_intersects=[shop['lng'], shop['lat']]).first()
            # 2. 收件地址不在围栏内: 关闭呼叫, 提示失败.
            if not fence:
                msg = '找不到客户[%s][%s]%s 所在的收件围栏.' % (shop['name'], shop['address'], (shop['lat'], shop['lng']))
                logging.info(msg)

                c = Call(shop_id=shop['id'], shop_name=shop['name'], shop_tel=shop['tel'], loc=loc, count=kw['count'],
                         status=CallState.STATUS_CLOSED, msg='呼叫失败，超出服务范围')
                c.save()
                self.resp_error('抱歉！呼叫失败，超出服务范围')
                return
            else:
                fence_id = str(fence.id)
                # 3. 重复呼叫: 尚有 未被响应的 同一围栏的 呼叫
                any_c = Call.objects(shop_id=shop['id'], status=CallState.STATUS_ALL).limit(1).first()
                if any_c and any_c.loc['fence']['id'] == fence_id:
                    self.resp_error('您已呼叫成功，请耐心等待派件员上门')
                    return
                loc = {
                    'lat': shop['lat'],
                    'lng': shop['lng'],
                    'address': shop['address'],
                    'fence': {
                        'id': fence_id,
                        'name': fence['name'],
                        'node': {
                            'id': fence['node']['id'],
                            'name': fence['node']['name'],
                            'loc': fence['node']['loc']
                        }
                    }
                }
                # 3.1 找到该客户没付钱的前20单(如有), 塞到这个呼叫里面
                es = Express.objects(creator__id=shop['id'], status__status=ExprState.STATUS_PRE_CREATED).only('number').limit(20).all()
                if es:
                    number_list = [e['number'] for e in es]
                    c = Call(shop_id=shop['id'], shop_name=shop['name'], shop_tel=shop['tel'], loc=loc, count=kw['count'], number_list=number_list)
                else:
                    c = Call(shop_id=shop['id'], shop_name=shop['name'], shop_tel=shop['tel'], loc=loc, count=kw['count'])
                c.save()
        except Exception as e:
            logging.exception(e)
            self.resp_error('抱歉！呼叫失败')
            return
        else:
            # 4. 找到围栏内所有配送员的client_id, 推送风信
            logging.info('为客户[%s]找到匹配围栏[%s], 正在过滤所有配送员...' % (shop['name'], fence['name']))
            mans = fence.mans  # [{id,name,tel,m_type,client_id}]
            client_ids = set()
            for man in mans:
                client_ids.add(man['client_id'])
            # 围栏下有人
            if mans:
                # 客户XX，15058771111，下了X单啦，赶紧去响应哦~
                msg = "客户:%s,%s 下了%s单啦，赶紧去响应哦~" % (shop['name'], shop['tel'], kw['count'])
                shortcuts.channel_send_message(
                    client_ids,
                    message_type=conf.MSG_TYPE_DELIVERY_ALERT,
                    content=msg,
                    summary=msg,
                    description="收件提醒"
                )
                msg = "最近围栏[%s], 推送给: %s" % (fence['name'], ','.join([m['name'] for m in mans]))
                logging.info(msg)
                c.modify(msg=msg, watchers=mans)
                self.resp(c.pack())
                return
            # 围栏下没配送员
            else:
                msg = "最近围栏[%s], 未推送: 围栏内无服务人员" % fence['name']
                logging.warn(msg)
                c.modify(set__status=CallState.STATUS_CLOSED, msg='呼叫失败，附近无服务人员')
                self.resp_error('抱歉！呼叫失败, 区域未开通服务')
                return


class OneKeyCallPickle(ReqHandler):
    @gen.coroutine
    def post(self):
        try:
            data = pickle.loads(self.request.body)

            data = Schema({
                Optional(object): object,
                Optional("Q", default=Q()): object,
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("only", default=[]): list,
                Optional("order_by", default=['-update_time']): list,
            }).validate(data)

            page = data.pop('page')
            count = data.pop('count')
            limit = data.pop('limit')
            only = data.pop('only')
            order_by = data.pop('order_by')
            query = data.pop("Q")
        except Exception as e:
            logging.exception(e.message)
            self.resp_args_error()
            return
        try:
            q = Q(**data) & query
            # logging.info(q.to_query(Call))
            count, call_list = paginator(Call.objects(q).order_by(*order_by), page, count, limit)
        except Exception as e:
            logging.exception(data)
            self.resp_args_error()
            return

        self.set_header('X-Resource-Count', count)
        self.resp([call.pack(only=only) for call in call_list])
        return


# ==> 收派端: 该次呼叫中尚未完成收件的运单列表
class ExprListInCall(ReqHandler):
    @gen.coroutine
    def get(self):
        try:
            kw = Schema({
                'call_id': schema_objectid,
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("only", default=[]): schema_unicode_multi,
                Optional("order_by", default=['-status.status', '-update_time']): schema_unicode_multi,
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error()
            return
        # 先找到对应的呼叫, 没有的话, 直接报错
        call = Call.objects(id=kw['call_id']).first()
        if not call:
            self.resp_not_found('找不到对应的呼叫')
            return
        # 再根据呼叫里面记录的number_list到运单中去找运单们
        page = kw.pop('page')
        count = kw.pop('count')
        limit = kw.pop('limit')
        only = kw.pop('only')
        order_by = kw.pop('order_by')
        count, expr_list = paginator(Express.objects(number__in=call.number_list,
                                                     status__status__in=[ExprState.STATUS_PRE_CREATED,
                                                                         ExprState.STATUS_CREATED]).order_by(*order_by),
                                     page, count, limit)
        self.set_header('X-Resource-Count', count)
        self.resp([expr.pack(only=only) for expr in expr_list])
        return


# ==> 收派端: [PATCH] 立即响应(抢呼叫)/ 关闭呼叫入口/ 加单(打印,定价)/ 取消/ 生成收款码/ 收件
class OneKeyCallSingle(ReqHandler):
    @gen.coroutine
    def patch(self, call_id):
        """
        对单个呼叫的操作.
        详见fsm_call.py.
        :param call_id: 呼叫id
        :return:
        """
        try:
            kw = Schema({
                "operation": schema_unicode,
                "operator_type": schema_unicode,
                "operator": schema_operator_unicode,
                Optional(object): object,
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error(e.message)
            return

        operation = kw.pop('operation')
        operator_type = kw.pop('operator_type')
        operator = kw.pop('operator')

        call = Call.objects.get(id=call_id)
        if not call:
            self.resp_not_found('找不到对应的呼叫任务')
            return
        # 操作不在允许的范围内
        if not (operation in CallState.INSIDE_EVENTS or operation in CallState.OUTSIDE_EVENTS):
            self.resp_forbidden()
            return

        # ==> 运单事件
        # 0. 错误预判
        status = call.status
        err = {
            (CallState.STATUS_ALL, CallState.EVENT_CLOSE): '请先应答来获得此次呼叫哦',
            (CallState.STATUS_ASSIGNED, CallState.EVENT_ASSIGN_TO_ME): '应答失败, 该次呼叫已被其他收派员抢走',
            # (CallState.STATUS_ASSIGNED, CallState.EVENT_SJ): '请先加单哦',
            (CallState.STATUS_BE_IN_PROCESS, CallState.EVENT_CLOSE): '请完成收件或取消运单后再关闭入口哦',
        }
        msg = err.get((status, operation))
        if msg:
            self.resp_error(msg)
            return

        # 1. 统一处理事件:
        # FSM 调用状态机
        try:
            modified_call = yield CallFSM.update_status(operator_type, call, operation, operator, **kw)
        except ValueError as e:
            logging.warn('State transfer for call[%s][%s][%s] using [%s] failed.' % (
                str(call.pk), call.shop_name, call.status, operation))
            logging.exception(e)
            self.resp_error(e.message)
            return
        except Exception as e:
            logging.exception(e)
            self.resp_error(e.message)
            return
        else:
            self.resp(modified_call.pack(only=['number_list', 'transact_list', 'id', 'assignee', 'loc', 'create_time', 'shop_id']))


# ==> AG-uwsgi: 微信/支付宝 支付成功的首次通知
class FirstSuccessPayNotification(ReqHandler):
    @gen.coroutine
    def patch(self):
        logging.info(self.get_body_args())
        try:
            kw = Schema({
                'ret': schema_unicode,  # generate_xml({'return_code': 'SUCCESS/FAIL'})
                'msg': schema_unicode,  # FlowLogic.MSGS: 现在只处理notify_first_success
                'transact_num': schema_unicode,
                'trade_no': schema_unicode
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.exception(e)
            self.resp_error(e.message)
            return

        """注意: 回调的部分, 要根据transact_num
        1. 改flow_top_up, flow, flow_statistics; ==> 由AG-uwsgi完成
        2.1 改aeolus.call.transact_list的trade_no;
        2.2 改aeolus.express对应于number_list里面的运单的状态们."""
        call = Call.objects(transact_list__transact_num=kw['transact_num']).first()

        # 没找到对应流水号的呼叫
        if not call:
            msg = '未找到流水号为[%s]的呼叫记录' % kw['transact_num']
            logging.error(msg)
            self.resp_error(msg)
            return

        # 找到了, 将对应的记录从列表扒拉出来
        for transact in call.transact_list:
            if transact['transact_num'] == kw['transact_num']:
                c = Call.objects(transact_list__transact_num=kw['transact_num']).update(full_result=True,
                                                                                        set__transact_list__S__trade_no=
                                                                                        kw['trade_no'])
                e = Express.objects(number__in=transact['number_list']).update(full_result=True,
                                                                               set__status={
                                                                                   'status': ExprState.STATUS_CREATED,
                                                                                   'sub_status': ExprState.SUB_STATUS_CREATED})
                if c['nModified'] == 1 and e['nModified'] == len(transact['number_list']):
                    self.resp(transact)
                    return
                else:
                    logging.error('商户[%s]支付[%s]成功, 运单号为%s, 流水号为%s'
                                  ' 但是批量更新运单状态失败(cnModified=%s, enModified=%s),'
                                  ' 请手动更新trade_no和status!' %
                                  (call.shop_name, transact['cash'], transact['number_list'], kw['transact_num'],
                                   c['nModified'], e['nModified']))
                    self.resp_error('检测到数据异常,请联系客服')
                    return


# ==> 代商户下单
class HelpClient(ReqHandler):
    @gen.coroutine
    def post(self):
        try:
            kw = Schema({
                'creator': schema_shop_unicode,
                'node': {
                    'node_0': schema_node_x_unicode,
                    'node_n': schema_node_x_unicode
                },
                Optional('remark', default=''): schema_unicode_empty,
                'operator': schema_operator_unicode
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.exception(e)
            self.resp_args_error(e.message)
            return

        expr = None

        def clean():
            if expr:
                expr.delete()

        try:
            # 1. 预先设置默认运费
            fee = yield get_fee(kw['creator']['id'])
            # 2. 状态预设
            status = dict(status=ExprState.STATUS_PRE_CREATED, sub_status=ExprState.SUB_STATUS_PRE_CREATED)
            # 3. 创建
            expr = yield Express.create(
                creator=kw['creator'],
                status=status, node=kw['node'], remark=kw['remark'], fee=fee,
                assignee=kw['operator']  # 代商户下单预设领取人为 进行这个操作的派件员
            )
        except ApiError as e:
            clean()
            self.resp_error(e.message)
            return
        except DuplicateDocError:
            clean()
            self.resp_error("运单重复创建")
            return
        except Exception as e:
            clean()
            logging.exception(e)
            self.resp_error("系统出错")
            return
        else:
            # 找到aeolus.call中该商户的max(create_time), 如有, 则将expr.number填入number_list
            call = Call.objects(shop_id=kw['creator']['id']).order_by('-create_time').limit(1).first()
            if call:
                call.modify(add_to_set__number_list=expr.number)
            self.resp_created(expr.pack())
            return


# ==> 领取运单
class AssignToMe(ReqHandler):
    @gen.coroutine
    def patch(self):
        try:
            kw = Schema({
                'number': schema_unicode,
                'operator': schema_operator_unicode
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error()
            return
        try:
            expr = Express.objects(number=kw['number']).first()
            if not expr:
                self.resp_error('运单不存在')
                return
            elif expr.assignee:
                self.resp_error('此单已被人抢先领走')
                return
            expr.modify(set__assignee=kw['operator'])
        except Exception as e:
            logging.error(e.message)
            self.resp_error('无法领取此运单')
            return
        else:
            self.resp(expr.pack())


# ==> 批量下单/查询
class ExpressHandler(SearchHandler):
    @gen.coroutine
    def get(self):
        data, ok = self.check_search_args()
        if not ok:
            return

        base_query, status_query = self.build_search_query(data)
        q = base_query & status_query
        logging.debug(q.to_query(Express))
        queryset = Express.objects(base_query & status_query).order_by(*data['order_by'])
        count, expr_list = paginator(queryset, data['page'], data['count'], data['limit'])

        self.set_header('X-Resource-Count', count)
        self.resp([expr.pack(includes=data['includes'], excludes=data['excludes'], only=data['only'])
                   for expr in expr_list])

    @gen.coroutine
    def post(self):
        try:
            kw = Schema({
                Optional("pay", default=False): schema_bool,
                "creator": schema_shop_unicode,
                "expr_list": [
                    {
                        Optional("third_party", default=None): {
                            Optional("name", default=""): schema_unicode_empty,
                            Optional("order_id", default=""): schema_unicode_empty,
                        },
                        Optional("remark", default=""): schema_unicode_empty,
                        "node": {
                            Optional("node_0"): schema_node_x_unicode,
                            "node_n": schema_node_x_unicode,
                        },
                        "fee": {
                            Optional("volume_a"): schema_int,
                            Optional("volume_b"): schema_int,
                            Optional("volume_c"): schema_int,
                            Optional("weight"): schema_float_2,
                        }
                    }
                ]
            }).validate(self.get_body_args())
        except Exception as e:
            logging.exception(e.message)
            self.resp_args_error(e.message)
            return

        creator = kw['creator']
        need_pay = kw['pay']

        cost = 0
        content = []

        # 遇到任何异常, 则清空数据库里面的运单们
        def clean():
            for ex in content:
                ex.delete()

        # 要付费的单,直接进入CREATED; 否则进入PRE_CREATED.
        if need_pay:
            status = {
                'status': ExprState.STATUS_CREATED,
                'sub_status': ExprState.SUB_STATUS_CREATED,
            }
        else:
            status = {
                'status': ExprState.STATUS_PRE_CREATED,
                'sub_status': ExprState.SUB_STATUS_PRE_CREATED,
            }

        try:
            for d in kw['expr_list']:
                # 计算配送费: base + extra(按照体积/重量)
                # d['fee'] = dict(volume_a=a, volume_b=b,volume_c=c, weight=w)
                volume = d['fee'].get('volume_a', 0) * d['fee'].get('volume_b', 0) * d['fee'].get('volume_c',
                                                                                                  0)
                fee = yield get_fee(kw['creator']['id'], volume=volume, weight=0.0)
                d['fee'].update(fee)
                if volume != 0:
                    d['fee']['volume'] = volume

                expr = yield Express.create(creator=creator, status=status, **d)
                # TODO 这里会有问题, 如果已经存在的第三方单号则不会创建新的运单但是会扣钱
                cost += fee['fh']
                content.append(expr)
        except ApiError as e:
            clean()
            self.resp_error(e.message)
            return
        except DuplicateDocError:
            clean()
            self.resp_error("运单重复创建")
            return
        except Exception as e:
            logging.exception(e)
            clean()
            self.resp_error("系统出错")
            return
        # 如果需要, 给商户扣款
        if need_pay and cost > 0:
            paid = yield shop_pay(creator['id'], cost)
            if paid is False:
                clean()
                self.resp_error("扣款失败,请充值.")
                return

        content = [_.pack(only=["number", 'third_party']) for _ in content]

        # 下单通知区域经理: 发短信+风信
        place_order_notify(kw['creator'], len(content), )

        self.resp_created(content)


# ==> 单个运单: 详情/操作
class OneExpressHandler(ReqHandler):
    @gen.coroutine
    def get(self, number):
        """
        对单个运单的查询.
        支持对返回内容的选择性获取: excludes, includes-目前只对trace有用, only.
        :param number: 运单号
        :return:
        """
        kw = Schema({
            Optional("only"): schema_utf8_multi,
            Optional("excludes"): schema_utf8_multi,
            Optional("includes"): schema_utf8_multi
        }).validate(self.get_query_args())
        expr = Express.objects(number=number).first()
        if expr:
            self.resp(expr.pack(**kw))
        else:
            self.resp_not_found('运单[%s]不存在.' % number)

    @gen.coroutine
    def patch(self, number):
        """
        对单个运单的操作.
        详见fsm_expr.py.
        :param number: 运单号
        :return:
        """
        try:
            kw = Schema({
                "operation": schema_unicode,
                "operator_type": schema_unicode,
                "operator": schema_operator_unicode,
                Optional(object): object,
            }).validate(self.get_body_args())
        except Exception as e:
            logging.error(e)
            self.resp_error('参数解析失败')
            return

        operation = kw.pop('operation')
        operator_type = kw.pop('operator_type')
        operator = kw.pop('operator')

        expr = Express.objects(number=number).first()
        if not expr:
            self.resp_not_found()
            return
        # 操作不在允许的范围内
        if not (operation in ExprState.INSIDE_EVENTS or operation in ExprState.OUTSIDE_EVENTS):
            self.resp_forbidden()
            return

        # ==> 运单事件
        # 0. 错误预判
        status = expr.status['status']
        err = {
            (ExprState.STATUS_PRE_CREATED, ExprState.EVENT_SJ): '收件失败, 该运单未付款',
            (ExprState.STATUS_SENDING, ExprState.EVENT_SJ): '收件失败, 该运单已被收件',
            (ExprState.STATUS_FINISHED, ExprState.EVENT_SJ): '收件失败, 该运单已被妥投',

            (ExprState.STATUS_PRE_CREATED, ExprState.EVENT_QJ): '取件失败, 该运单未付款',
            (ExprState.STATUS_CREATED, ExprState.EVENT_QJ): '取件失败, 请先收件',
            (ExprState.STATUS_FINISHED, ExprState.EVENT_QJ): '取件失败, 该运单已被妥投',

            (ExprState.STATUS_PRE_CREATED, ExprState.EVENT_ZP): '指派失败, 该运单未付款',
            (ExprState.STATUS_FINISHED, ExprState.EVENT_ZP): '指派失败, 该运单已被妥投',
        }
        msg = err.get((status, operation))
        if msg:
            logging.warn('%s: %s' % (number, msg))
            self.resp_error(msg)
            return

        # 1. 统一处理事件:
        # FSM 调用状态机
        try:
            modified_expr = ExprFSM.update_status(operator_type, expr, operation, operator, **kw)
        except ValueError as e:
            logging.warn('State transfer for expr[%s][%s] using [%s] failed.' % (expr.number, expr.status, operation))
            logging.exception(e)
            self.resp_error(e.message)
            return
        else:
            self.resp_created(modified_expr.pack())


# ==> 单个/批量: 商户余额支付
class PayExpress(ReqHandler):
    @gen.coroutine
    def patch(self):
        try:
            kw = Schema({
                "shop_id": schema_unicode,
                "cash": schema_float_2,
                "number_list": [
                    schema_unicode
                ]
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e)
            self.resp_args_error()
            return
        # 0.1 待支付运费必须大于0
        if kw['cash'] <= 0:
            self.resp_error('总计待支付必须大于0元')
            return
        # 0.2 校验该商户的单,运费信息是否对应传入的参数
        # 计算该商户总计待支付的运费
        pipeline = [
            # 取待配送员定价收件的运单列表
            {
                "$match": {
                    "number": {"$in": kw['number_list']},  # 传入的这些单
                    "creator.id": kw['shop_id'],  # 是该商户下的单
                    "status.sub_status": ExprState.SUB_STATUS_PRE_PRICED,  # 下单后已定价,尚未成功支付
                    "fee.fh": {"$exists": True, "$ne": None}
                }
            },
            # 加一下, 获得自己总计待支付的运费
            {
                "$group": {
                    "_id": None,
                    "cash": {"$sum": "$fee.fh"}
                }
            }
        ]
        cursor = Express.objects.aggregate(*pipeline)
        _result = [doc for doc in cursor]
        if not _result:
            self.resp_error("运单校验失败, 请尝试刷新页面后重试")
            return
        else:
            cash = _result[0]['cash']
            if round(cash, 2) != kw['cash']:
                self.resp_error("运单和运费校验失败, 请尝试刷新页面或单笔付款")
                return

        # 扣款
        paid = yield shop_pay(kw['shop_id'], kw['cash'])
        if paid is False:
            self.resp_error("扣款失败,请充值")
            return
        else:
            # 扣款成功, 批量修改status
            r = Express.objects(number__in=kw['number_list']).update(full_result=True,
                                                                     set__status=dict(
                                                                         status=ExprState.STATUS_CREATED,
                                                                         sub_status=ExprState.SUB_STATUS_CREATED))
            if r['nModified'] != len(kw['number_list']):
                logging.error('商户[%s]扣款[%s]成功, 运单号为%s. 但是批量更新运单状态失败, 请手动更新status!' %
                              (kw['shop_id'], kw['cash'], kw['number_list']))
                self.resp_error('检测到数据异常,请联系客服')
                return
            else:
                self.resp(kw)
                return


# ==> 补全运单信息: 收件人
class ReceiverHandler(ReqHandler):
    @gen.coroutine
    def patch(self, number):
        try:
            kw = Schema({
                "node_n": schema_receiver,
                Optional("remark", default=""): schema_utf8_empty,
                "operator": schema_operator_unicode,
                # "weight": schema_float
            }).validate(self.get_body_args())
        except Exception as e:
            logging.warning(e)
            self.resp_args_error()
            return

        expr = Express.objects(number=number).first()
        if not expr:
            self.resp_not_found()
            return
        # 0. 错误判断: (a)已经补全过/不需要补全信息 且 已经定过价 (b)已经支付过
        if expr.node['node_n']['tel'] != "":
            self.resp_error("本运单已经补全过信息, 请加价或直接发起收款")
            return
        if expr.status['status'] != ExprState.STATUS_PRE_CREATED:
            self.resp_error("本运单已经支付过, 请直接取件")
            return

        # ==> 只补全: 空单没填信息先定价,之后再补全
        query = {
            # 收货人姓名,电话,地址, 备注
            "set__node__node_n": kw['node_n'],
            "set__remark": kw['remark']
        }
        # # ==> 只定价: 补全运单信息先定价/扫码/录单取件
        # # ==> 补全+定价: 未定价的空单用默认weight补全信息
        # # 1. 根据体积重量计算价格
        # fee = yield get_fee(expr.creator['id'], weight=kw['weight'])
        # # 2. 补充基本信息(如需要), 价格, assignee,watchers
        # old_fh = expr.fee['fh']
        # query.update({
        #     # 发货费用信息
        #     "set__fee__fh": fee['fh'],
        #     "set__fee__fh_base": fee['fh_base'],
        #     "set__fee__fh_extra": fee['fh_extra'],
        #     "set__fee__msg": fee['msg']
        # })
        expr.modify(**query)
        #
        # # 3.1 允许同一个收件员多次定价
        # if expr.status['sub_status'] == ExprState.SUB_STATUS_PRE_PRICED:
        #     logging.info("[%s]对运单[%s]重新定价成功,定价已从[%s]更新为[%s]" %
        #                  (kw['operator']['name'], expr.number, old_fh, expr.fee['fh']))
        # # 3.2 首次定价, 记录assignee,watchers,trace
        # else:
        #     msg = u'收件员{name} {tel} 已定价'.format(name=kw['operator']['name'], tel=kw['operator']['tel'])
        #     fence = expr.node.get('node_0', {}).get('fence', {})
        #     if fence and fence.get('name') and fence.get('id') != 'x':
        #         msg = '[%s] %s' % (fence['name'], msg)
        #     modified_expr = ExprFSM.update_status("OUTSIDE",
        #                                           expr,
        #                                           ExprFSM.EVENT_PRICING,
        #                                           kw['operator'],
        #                                           assignee=kw['operator'],
        #                                           watcher=kw['operator'],
        #                                           msg=msg)
        #     if not modified_expr:
        #         logging.warning('State transfer for expr[%s][%s] using [%s] failed.' %
        #                         (expr.number, expr.status, ExprFSM.EVENT_PRICING))
        #         self.resp_error('操作失败')
        #         return

        self.resp(content=expr.pack())


# ==> 派件员改价
class Fee(ReqHandler):
    @gen.coroutine
    def patch(self):
        try:
            kw = Schema({
                'number': schema_unicode,
                'weight': schema_float_2,
                'operator': schema_operator_unicode
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        expr = Express.objects(number=kw['number']).first()
        # 0. 错误判断: (a)运单不存在 (b)运单已支付或已流转
        if not expr:
            self.resp_not_found()
            return
        if expr.status['status'] != ExprState.STATUS_PRE_CREATED:
            self.resp_error("本运单已经支付过, 请直接取件")
            return
        # 1. 根据体积重量计算价格
        fee = yield get_fee(expr.creator['id'], expr.fee['category'], weight=kw['weight'])
        old_fh = expr.fee['fh']
        # 2. 改发货费用信息
        expr.modify(set__fee__fh=fee['fh'],
                    # set__fee__fh_base=fee['fh_base'],
                    set__fee__fh_extra=fee['fh_extra'],
                    set__fee__msg=fee['msg'])
        # 3. 允许同一个收件员多次定价
        if expr.status['sub_status'] == ExprState.SUB_STATUS_PRE_PRICED:
            logging.info("[%s]对运单[%s]重新定价成功,定价已从[%s]更新为[%s]" %
                         (kw['operator']['name'], expr.number, old_fh, expr.fee['fh']))
        self.resp(expr.pack())


# ==> 派件员批量定价
class Pricing(ReqHandler):
    @gen.coroutine
    def patch(self):
        try:
            kw = Schema({
                "shop_id": schema_unicode,
                "cash": schema_float_2,
                "number_list": [
                    schema_unicode
                ],
                "operator": schema_operator_unicode
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e)
            self.resp_args_error(content=e.message)
            return
        # 0.1 想要发起的收款金额必须大于0
        if kw['cash'] <= 0:
            self.resp_error('总计发起收款的金额必须大于0元')
            return

        cash = Express.objects(
            number__in=kw['number_list'],  # 传入的这些单
            creator__id=kw['shop_id'],  # 是该商户下的单
            status__sub_status=ExprState.SUB_STATUS_PRE_CREATED,  # 必须都没被别人发起过收款(PRE_CREATED.PRE_CREATED)
            node__node_n__tel={"$exists": True, "$ne": ""},  # 都填过收方信息了
            fee__fh={"$exists": True, "$ne": None}
        ).aggregate_sum('fee.fh')
        if cash == 0:
            self.resp_error("运单校验失败, 请尝试刷新页面后重试")
            return
        elif round(cash, 2) != kw['cash']:
            self.resp_error("运单和运费校验失败, 请尝试刷新页面或单笔付款")
            return

        # 发起收款成功, 批量改status和assignee,watchers
        r = Express.objects(number__in=kw['number_list']).update(full_result=True,
                                                                 set__status=dict(
                                                                     status=ExprState.STATUS_PRE_CREATED,
                                                                     sub_status=ExprState.SUB_STATUS_PRE_PRICED),
                                                                 set__assignee=kw['operator'],
                                                                 add_to_set__watchers=kw['operator'])
        if r['nModified'] != len(kw['number_list']):
            logging.error('派件员[%s]向商户[%s]发起收款成功, 运单号为%s. 但是批量更新运单状态失败, 请手动更新status和assignee,watchers!' % (
                kw['operator']['name'], kw['shop_id'], kw['number_list']))
            self.resp_error('检测到数据异常,请联系客服')
            return
        else:
            self.resp(kw)
            return


class ExpressExportHandler(ReqHandler):
    def get(self):
        """
        song上面给商户导出运单信息
        """
        try:
            data = self.get_query_args()
            shop_id = data["shop_id"]
            start_time = TimeZone.str_to_datetime(data["start_time"])
            end_time = TimeZone.str_to_datetime(data["end_time"])
        except:
            self.resp_error("bad query string")
            return
        objs = Express.objects(creator__id=shop_id, create_time__gte=start_time, create_time__lte=end_time)
        values = objs.scalar(
            "third_party",
            "number",
            "node",
            "remark",
            "create_time",
            "status"
        )
        exp = [
            [
                "第三方单号",
                "运单编号",
                "收货者姓名",
                "收货者电话",
                "收货者地址",
                "备注",
                "创建时间",
                "运单状态"
            ]
        ]
        for i in values:
            exp.append([
                i[0].get("order_id", "") if i[0] else "",
                i[1],
                i[2].get("node_n", {}).get("name", ""),
                i[2].get("node_n", {}).get("tel", ""),
                i[2].get("node_n", {}).get("addr", ""),
                i[3],
                TimeZone.utc_to_local(i[4]).strftime("%Y-%m-%d %H:%M:%S"),
                ExprFSM.STATUS_NAME_MAPPING.get(i[5]["sub_status"], "其他状态").decode("utf-8")
            ])

        self.set_header("Content-type", "application/vnd.ms-excel")
        logging.info(exp)
        self.finish(xls.xls_writer(exp))


# ==> 站点 增[POST] 删[DELETE] 改[PATCH] 简单查[GET]
class NodeGen(ReqHandler):
    @gen.coroutine
    def post(self):
        try:
            kw = Schema({
                'name': schema_unicode,
                'loc': {
                    'lat': schema_float,
                    'lng': schema_float,
                    'address': schema_unicode,
                },
                # 'point': {
                #     "type": "Point",
                #     "coordinates": ['lng', 'lat']
                # },
                'time_table': [
                    Optional({
                        't': schema_unicode,
                        Optional('man'): {
                            'id': schema_objectid,
                            'name': schema_unicode,
                            'tel': schema_unicode,
                            Optional('m_type', default='man'): schema_unicode,
                            'client_id': schema_unicode
                        }
                    })
                ]
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        try:
            point = {
                "type": "Point",
                "coordinates": [kw['loc']['lng'], kw['loc']['lat']]
            }
            node = Node(name=kw['name'], loc=kw['loc'], time_table=kw['time_table'], point=point)
            node.save()
            node.reload()
        except Exception as e:
            logging.exception(e)
            self.resp_error('站点生成失败: %s' % e.message)
            return
        else:
            self.resp(node.pack())
            return

    @gen.coroutine
    def delete(self):
        """
        删
        :return:
        """
        try:
            kw = Schema({
                'id': schema_unicode
            }).validate(self.get_query_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        node = Node.objects(id=kw['id']).first()
        if node:
            node.delete()
            self.resp()
            return
        else:
            logging.warn('找不到对应的站点: id=[%s]' % kw['id'])
            self.resp_not_found('找不到对应的站点')
            return

    @gen.coroutine
    def patch(self):
        """
        改
        :return:
        """
        try:
            kw = Schema({
                'Q': object,  # query in modify

                Optional(object): object,  # **kwargs in modify
            }).validate(self.get_body_args())

            query = kw.pop("Q")

        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        # schedule: 第二天生效
        try:
            kw['set__update_time'] = arrow.utcnow().datetime
            query_set = Node.objects(**query)
            if not query_set:
                msg = '找不到对应的站点: %s' % query
                logging.warn(msg)
                self.resp_not_found(msg)
                return
            else:
                result = query_set.update(full_result=True, **kw)
        except Exception as e:
            logging.exception(e.message)
            self.resp_error('修改站点失败: %s' % e.message)
            return

        if result and result['nModified'] > 0:
            # logging.info('修改了%s个站点' % result['nModified'])
            self.resp()
            return
        else:
            logging.warn('修改站点失败: Q=%s, kw=%s' % (query, kw))
            self.resp_error(content='修改站点失败')
            return

    @gen.coroutine
    def get(self):
        """
        返回站点信息
        :return:
        """
        try:
            qs = Schema({
                Optional(object): object,
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("only", default=None): schema_unicode_multi,
                Optional("order_by", default='name'): schema_unicode_multi,
            }).validate(self.get_query_args())

            page = qs.pop('page')
            count = qs.pop('count')
            limit = qs.pop('limit')

            only = qs.pop('only')
            order_by = qs.pop('order_by')

        except SchemaError as e:
            logging.exception(e.message)
            self.resp_args_error()
            return
        try:
            count, node_list = paginator(Node.objects(**qs).order_by(*order_by), page, count, limit)
        except Exception as e:
            logging.exception(e)
            self.resp_error(e.message)
            return
        else:
            self.set_header('X-Resource-Count', count)
            self.resp([node.pack(only=only) for node in node_list])
            return


# ==> 配送系人员时刻表信息
class ScheduleHandler(ReqHandler):
    @gen.coroutine
    def get(self):
        try:
            params = Schema({
                'id': schema_objectid
            }).validate(self.get_query_args())
        except Exception as e:
            logging.warn(e.message)
            self.resp_args_error()
            return

        s = Schedule.objects(man__id=params['id']).only('man.name', 'run').first()
        if s:
            self.resp(s.pack(only=('man', 'run')))
            return
        else:
            self.resp_no_content()
            return


# ==> 围栏 增[POST] 删[DELETE] 改[PATCH] 简单查[GET]
class FenceHandler(ReqHandler):
    @gen.coroutine
    def post(self):
        """增"""
        try:
            kw = Schema({
                'name': schema_unicode,
                'points': {
                    "type": "Polygon",
                    "coordinates": [  # list of line-strings
                        [[schema_float, schema_float]],  # lng, lat
                    ]},
                Optional('node', default=None): {  # 对应的站点信息
                    "id": schema_unicode,
                    'name': schema_unicode,
                    'loc': {
                        'lat': schema_float,
                        'lng': schema_float,
                        'address': schema_unicode,
                    },
                    Optional(object): object
                },
                'mans': [
                    Optional({
                        'id': schema_objectid,
                        'name': schema_unicode,
                        'tel': schema_unicode,
                        'm_type': schema_unicode,
                        'client_id': schema_unicode,
                        Optional(object): object
                    })
                ]
            }).validate(self.get_body_args())
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        # 筛除id重复的mans
        new_mans = []
        collected_man_ids = []
        for m in kw["mans"]:
            if m["id"] in collected_man_ids:
                continue
            collected_man_ids.append(m["id"])
            new_mans.append(m)
        kw["mans"] = new_mans
        # 删除 time_table
        if kw["node"] and "time_table" in kw["node"]:
            kw["node"].pop("time_table")
        # 写数据库
        try:
            fence = Fence(**kw)
            fence.save()
            fence.reload()
        except Exception as e:
            logging.warn(traceback.format_exc())
            self.resp_error(e.message)
            return
        self.resp(fence.pack())

    @gen.coroutine
    def delete(self):
        """删"""
        try:
            kw = Schema({
                Optional(object): object
            }).validate(self.get_query_args())

            query = kw
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        try:
            query_set = Fence.objects(**query)
            if not query_set:
                msg = '找不到对应的围栏: %s' % query
                logging.warn(msg)
                self.resp_not_found(msg)
                return
            else:
                result = query_set.delete()
        except Exception as e:
            logging.exception(e.message)
            self.resp_error('删除围栏失败: %s' % e.message)
            return

        if result and result > 0:
            self.resp_created({"message": '删除了%s个围栏' % result})
        else:
            self.resp_error(content='删除围栏失败')

    @gen.coroutine
    def patch(self):
        """改"""
        try:
            kw = Schema({
                'Q': object,  # query in modify
                Optional(object): object,  # **kwargs in modify

                Optional("only", default=None): list,
            }).validate(self.get_body_args())

            only = kw.pop('only')
            query = kw.pop("Q")

        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return
        # 删除 time_table
        if "node" in kw and "time_table" in kw["node"]:
            kw["node"].pop("time_table")
        try:
            kw['set__update_time'] = arrow.utcnow().datetime
            query_set = Fence.objects(**query)
            if not query_set:
                msg = '找不到对应的围栏: %s' % query
                logging.warn(msg)
                self.resp_not_found(msg)
                return
            else:
                # 筛除id重复的mans
                if "mans" in kw:
                    new_mans = []
                    collected_man_ids = []
                    for m in kw["mans"]:
                        if m["id"] in collected_man_ids:
                            continue
                        collected_man_ids.append(m["id"])
                        new_mans.append(m)
                    kw["mans"] = new_mans
                # 更新数据库
                result = query_set.update(full_result=True, **kw)
        except Exception as e:
            logging.exception(e.message)
            self.resp_error('修改围栏失败: %s' % e.message)
            return

        if result and result['nModified'] > 0:
            logging.info('修改了%s个围栏' % result['nModified'])
            self.resp()
        else:
            self.resp_error(content='修改围栏失败')

    @gen.coroutine
    def get(self):
        """查"""
        try:
            kw = Schema({
                # level 1
                Optional("id"): schema_unicode,
                # level 2
                Optional("name"): schema_unicode,
                # level 3
                Optional("node_name"): schema_unicode,
                # level 4
                Optional("lat"): schema_float,
                Optional("lng"): schema_float,
                # level 5
                Optional("man_id"): schema_unicode,

                Optional("only", default=None): schema_unicode_multi,
                Optional("page", default=1): schema_int,
                Optional("count", default=10): schema_int
            }).validate(self.get_query_args())
            page = kw["page"]
            count = kw["count"]
        except SchemaError as e:
            logging.warn(e.message)
            self.resp_args_error(e.message)
            return

        if kw.get("id"):
            fence_obj = Fence.objects(id=kw["id"]).first()
            if not fence_obj:
                self.resp_not_found("id: 围栏不存在。")
                return
            self.resp(fence_obj.pack(only=kw["only"]))

        elif kw.get("name"):
            fence_obj = Fence.objects(name=kw["name"]).first()
            if not fence_obj:
                self.resp_not_found("name: 围栏不存在。")
                return
            self.resp(fence_obj.pack(only=kw["only"]))

        else:
            if kw.get("node_name"):
                fence_objs = Fence.objects(node__name=kw["node_name"])
            elif 'lat' in kw and 'lng' in kw:
                fence_objs = Fence.objects(node__id__exists=True, points__geo_intersects=[kw["lng"], kw["lat"]])
            elif kw.get("man_id"):
                fence_objs = Fence.objects(mans__match={"id": kw["man_id"]})
            else:
                fence_objs = Fence.objects()
            _amount, _content = paginator(fence_objs, page, count)
            self.set_x_resource_count(_amount)
            self.resp([i.pack(only=kw["only"]) for i in _content])


# ==> 围栏复杂查询
class FencePickle(ReqHandler):
    @gen.coroutine
    def post(self):
        """
        查
        :return:
        """
        try:
            data = pickle.loads(self.request.body)

            data = Schema({
                Optional(object): object,
                Optional("Q", default=Q()): object,
                Optional("page", default=1): schema_int,
                Optional("count", default=20): schema_int,
                Optional("limit", default=1): schema_bool,

                Optional("includes", default=None): list,
                Optional("excludes", default=None): list,
                Optional("only", default=None): list,
                Optional("order_by", default=['-update_time']): list,
            }).validate(data)

            page = data.pop('page')
            count = data.pop('count')
            limit = data.pop('limit')
            includes = data.pop('includes')
            excludes = data.pop('excludes')
            only = data.pop('only')
            order_by = data.pop('order_by')
            query = data.pop("Q")

        except SchemaError as e:
            logging.exception(e.message)
            self.resp_args_error()
            return
        try:
            q = Q(**data) & query
            logging.debug(q.to_query(Fence))
            count, fence_list = paginator(Fence.objects(q).order_by(*order_by), page, count, limit)
        except Exception as e:
            logging.exception(data)
            self.resp_args_error(e.message)
            return

        self.set_header('X-Resource-Count', count)
        self.resp([fence.pack(includes=includes, excludes=excludes, only=only)
                   for fence in fence_list])


@gen.coroutine
def place_order_notify(shop, expr_count):
    # 下单发短信: 通过寄方地址所在围栏取得区域经理联系方式
    try:
        from tools_lib.host_info import DEBUG
        from tools_lib.common_util.third_party.sms_api import async_send_sms, SMS_TYPE_NORMAL
        # TODO 让AG传经纬度过来
        # shop = yield self.get_shop_info_from_kwargs(shop_id=creator['id'])
        tel_list = []
        id_list = []
        if DEBUG:
            tel_list.append("15058115878")  # 庄兵
            id_list.append("56c2e7d97f4525452c8fc23c")  # 测试区域经理,tel 13245678901
            fence = query_fence_point_within([shop['lng'], shop['lat']])
            logging.info(fence)
        else:
            tel_list.append('15858184180')
            fence = query_fence_point_within([shop['lng'], shop['lat']])
            if fence and fence.get("manager"):
                tel_list.append(fence['manager']['tel'])
                id_list.append(fence["manager"].get("id"))

        msg = "商户:%s,%s 下了%s单啦，要及时安排运力哦！" % (shop['name'], shop['tel'], expr_count)

        # 给区域经理短信
        for tel in tel_list:
            async_send_sms(tel, msg, SMS_TYPE_NORMAL)
        logging.info("Sending sms to area manager(s): " + str(tel_list))

        # 给区域经理风信
        client_id_list = yield shortcuts.tornado_account_query(account=[
            {"account_id": one_id, "account_type": conf.ACCOUNT_TYPE_MAN} for one_id in id_list
            ])
        if client_id_list:
            shortcuts.channel_send_message(
                client_id_list,
                message_type=conf.MSG_TYPE_DELIVERY_ALERT,
                content=msg,
                summary=msg,
                description="配送提醒"
            )
            logging.info("Sending windchat to area manager(s): " + str(id_list))
        else:
            logging.warn("Windchat not sent because client_id_list is empty.")
    except Exception as e:
        logging.exception(e)
        # todo 暂时不返回失败
        raise gen.Return(True)
    else:
        raise gen.Return(True)


class FuzzySearchAddressBaseHandler(ReqHandler):
    @gen.coroutine
    def get(self):
        """
        模糊匹配收件地址或派件地址信息(限定在shop_id或者 call_id 所指向的shop_id)
        """
        try:
            data = Schema({
                "term": schema_utf8,
                "search_in": schema_utf8,
                Optional("shop_id", default=None): schema_utf8_empty,
                Optional("call_id", default=None): schema_utf8_empty
            }).validate(self.get_query_args())
            data["search_in"] = http_utils.dot_string_to_list(data["search_in"])
        except SchemaError:
            self.resp_error("failed when parsing schema.")
            return
        if data["shop_id"]:
            cli_addr_obj = ClientAddress.objects(client__id=data["shop_id"]).first()
        elif data["call_id"]:
            call_obj = Call.objects(id=data["call_id"]).first()
            if not call_obj:
                self.resp_not_found("call not found.")
                return
            cli_addr_obj = ClientAddress.objects(client__id=call_obj.shop_id).first()
        else:
            self.resp_error("Either shop_id or call_id is empty.")
            return
        if not cli_addr_obj:
            self.resp_not_found("cli_addr_obj not found.")
            return
        targets = []
        for search_target in data["search_in"]:
            targets += getattr(cli_addr_obj, search_target)
        ret = []
        term = sstring.safe_utf8(data["term"])
        for i in targets:
            if term in sstring.safe_utf8(i["addr"]) or \
                            term in sstring.safe_utf8(i["tel"]) or \
                            term in sstring.safe_utf8(i["name"]):
                ret.append(i)
        self.resp(ret)
