# coding:utf-8


import hashlib
import logging
import pickle
import random

import shortuuid
from bson import ObjectId
from model_logics.fsm import ManFSM
from model_logics.logics import FlowLogic, FlowStatisticsLogic, ManLogic, ManFSMLogLogic
from model_logics.models import Man, SignIn, Staff
from schema import Schema, Optional
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.common_util.archived.utils import check_tel
from tools_lib.common_util.third_party.sms_api import send_code, SEND_SMS_SUCCESS, async_send_sms, SMS_TYPE_NORMAL
from tools_lib.gedis.core_redis_key import key_man_token, key_no_password, key_sms_code, key_man_code
from tools_lib.gedis.gedis import Redis
from tools_lib.transwarp.complex_query_parser import complex_query, parse_page_count
from tools_lib.transwarp.escape import schema_int
from tools_lib.transwarp.tz import utc_8_now, utc_8_day
from tools_lib.transwarp.web import Dict, ctx, post, api, get

# 风信账户注册用
from tornado.httpclient import HTTPClient
import tools_lib.windchat.account
import tools_lib.windchat.conf

# === 缓存 ===
redis_client = Redis()
# === 派件员基本信息相关 ===
BYS = Dict(**{x: x for x in ('id', 'tel', 'id_card_num', 'man_id')})
OPERATIONS = Dict(**{x: x for x in ('ADD_ACCOUNT', 'ADD_FAMILIAR', 'DEL_FAMILIAR', 'ADD_PICKUP', 'DEL_PICKUP')})
WHATS = Dict(**{x: x for x in ("BASIC", "STATUS", "ACCOUNT_LIST", "FAMILIAR_LIST", "PICKUP_LIST",
                               "CODE", "MAN_LIST", "SIGN_IN_COUNT")})

# === 派件员提现相关 ===
CASH_FLOW = Dict(**{x: x for x in ("VALIDATED", "APPLY_WITHDRAW", "PAID", "DECLINE")})


# === 基本信息相关 ===
@api
@get('/deliveryman/sms_code')
def api_man_sms_code():
    params = ctx.request.input()
    tel = str(params.get("tel", "")).strip()
    if not tel:
        raise ValueError("Should provide me with [tel] in params.")
    elif not check_tel(tel):
        raise ValueError("[tel] should be of length 11 and starts with digit 1.")

    sms_code = random.randrange(100000, 999999)
    # 同步发短信: 确保发送成功再改redis.
    send = send_code(tel, sms_code)
    if send == SEND_SMS_SUCCESS:
        sms_key = key_sms_code.format(tel=tel)
        # 插入验证码到redis中, 10分钟有效期: get sms:code:13245678901 => 123456
        redis_client.setex(sms_key, sms_code, 600)
        return sms_code
    else:
        raise ValueError("运营商发送验证码失败,请重试.")


@api
@get('/deliveryman/login')
def api_deliveryman_login():
    """
    @api {get} /deliveryman/login?man_id=&password= 登录
    @apiDescription 风先生派件员登录成功则返回token,失败则报错.
    @apiName api_deliveryman_login
    @apiGroup man

    @apiParam {string(11)} [man_id] 派件员工号, 如 7748657.
    @apiParam {string(11)} [tel] 派件员手机号, 如 150687929321.
    @apiParam {string(32)} password 派件员密码hash(如果是工号+密码登录), 验证码(如果是手机号+验证码登录).

    @apiParamExample {json} 请求url示例:
          /deliveryman/login?man_id=7740959&password=0192023a7bbd73250516f069df18b500
    OR    /deliveryman/login?tel=150687929321&password=123456
    @apiSuccessExample {json} 手机号验证码登录成功示例:
        HTTP/1.1 200 OK
        {
          "tel": "150687929321",
          "token": "36dc92e290f334aaa96466d3ee9b9efa"
        }
    @apiSuccessExample {json} 工号密码登录成功示例:
        HTTP/1.1 200 OK
        {
          "man_id": "7740959",
          "token": "36dc92e290f334aaa96466d3ee9b9efa"
        }
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
          "message": "No such deliveryman=[774095999]."
        }
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
          "message": "Password validation for [7740959]=[012023a7bbd73250516f069df18b500] failed."
        }
    """
    allowed_jd = {'parttime', 'city_driver', 'area_manager'}

    def set_token(inner_who, inner_role='man'):
        token = hashlib.md5('%s%s' % (inner_who, utc_8_now())).hexdigest()
        key = key_man_token.format(role=inner_role, content=token)
        # 插入token到redis中, 30天有效期: get token:fe11ad907e2fa779ed2f363ef589d3f9 => 7740959
        redis_client.setex(key, inner_who, 30 * 24 * 3600)
        return token

    params = ctx.request.input()
    tel = str(params.get("tel", "")).strip()
    password_or_sms_code = str(params.password).strip()
    role = str(params.get("role", "")).strip()
    # ==> 首先检查是不是免密码[优先级为: 免密码>手机]
    if not tel:
        logging.error("Should provide me with [tel] in params%s." % params)
        raise ValueError("需要提供手机号登录.")
    # 存放: 免密码名单和token(30天)
    # 登录成功: smembers no_password => set(7740959,...); sismember(key_login, man_id)
    elif redis_client.sismember(key_no_password, tel):
        # 根据电话找人员记录
        man = Man.objects(tel=tel).first()
        man_id = str(man.pk)
        content = set_token(man_id)
        jd = man.job_description[0] if man.job_description and man.job_description[0] in allowed_jd else 'parttime'
        return dict(token=content, man_id=man_id, tel=tel, jd=jd)

    # ==> 职工登录: 手机号+密码
    if role:
        password = password_or_sms_code
        staff = Staff.objects(tel=tel).first()
        # 如果此人不存在,直接报错
        if not staff:
            # todo 删除我,改成报错.
            staff = Staff(tel=tel, password=hashlib.md5('123456').hexdigest(),
                          create_time=utc_8_now(ret='datetime')).save()
            content = set_token(tel, inner_role='staff')
            return dict(token=content, man_id=str(staff.pk))
            # raise ValueError("No such staff with tel=[%s]." % tel)

        # 登录成功: 密码与数据库中值匹配
        staff_id = str(staff.pk)
        password_in_db = staff.password
        if password == password_in_db:
            content = set_token(tel, inner_role='staff')
            return dict(token=content, man_id=staff_id)
        # 登录失败
        else:
            logging.warn("Password validation for [%s]=[%s] failed, expected[%s]." % (tel, password, password_in_db))
            raise ValueError('登录名或密码错误.')

    # ==> 派件员登录: 手机号+验证码
    if tel:
        sms_code = password_or_sms_code
        sms_key = key_sms_code.format(tel=tel)
        # 登录成功: 验证码匹配 get sms:code:13245678901 => 123456
        sms_code_in_redis = redis_client.get(sms_key)
        if sms_code_in_redis == sms_code:
            # 根据电话找人员记录
            man = Man.objects(tel=tel).first()
            # 取header里面的app-name
            app_name = ctx.request.header('app-name')
            # 无记录人员: 记录派件员到mongodb: status=ManFSM.STATUS_INIT, job_description=[app-name]
            if not man:
                jd = [app_name] if app_name else []
                man = Man(tel=tel, job_description=jd, create_time=utc_8_now(ret="datetime")).save()

                # ===== 注册风信账户 =====
                http_client = HTTPClient()
                http_client.fetch(tools_lib.windchat.account.req_create(
                    account_type=tools_lib.windchat.conf.ACCOUNT_TYPE_MAN,
                    account_id=str(man.id)
                ), raise_error=False)

            # 有记录人员:
            else:
                jd = man.job_description
                jd = set(jd) if isinstance(jd, list) else set()
                if app_name:
                    jd.add(app_name)
                man.job_description = list(jd)
                man.save()
            man_id = str(man.pk)
            content = set_token(man_id)
            jd = man.job_description[0] if man.job_description and man.job_description[0] in allowed_jd else 'parttime'
            logging.info('[%s][%s][%s]登录成功.' % (man.name, tel, jd))
            return dict(token=content, man_id=man_id, tel=tel, jd=jd)
        # 登录失败
        else:
            logging.warn("SMS code validation for [%s]=[%s] failed, expected[%s]." % (tel, sms_code, sms_code_in_redis))
            raise ValueError("验证码不匹配.若您获取过多次验证码,请输入最新一条短信的验证码")


@api
@post('/deliveryman/sign_in')
def api_deliveryman_sign_in():
    """
    派件系人员签到
    :param man_id: 根据 id 查出 name, tel, avatar
    :param loc: {name, addr, lng, lat}
    :param device: {mac_id, ...}
    :return: 失败返回400和message
    """
    params = ctx.request.input()
    # ==> 根据id拿基本信息
    man = Man.objects(id=params.man_id).first()
    # ==> 检查今日签到次数
    now = TimeZone.local_now()
    start_time, _end_time = TimeZone.day_range(value=now)
    start_time = TimeZone.datetime_to_str(start_time)
    sign_in_count = SignIn.objects(**{'man_id': params.man_id, 'create_time__gte': start_time}).count()
    if sign_in_count >= 50:
        logging.warn("Man[%s][%s] try to sign in over 10 times." % (params.man_id, man.name))
        raise ValueError("一天最多签到10次")
    # ==> 记录这次签到
    name = man.name if man.name else ''
    avatar = man.avatar if man.avatar else ''
    SignIn(man_id=params.man_id, name=name, tel=man.tel, avatar=avatar,
           loc=params.loc,
           device=params.device,
           create_time=now).save(force_insert=True)
    return {'create_time': TimeZone.datetime_to_str(now, pattern='%Y-%m-%dT%H:%M:%S')}


@api
@get('/deliveryman/token')
def api_get_man_info_from_token():
    req = ctx.request.input()
    if not (req.token and len(req.token) >= 38):
        ctx.response.status = '401 Unauthorized'
        return None
    token = req.token.split()[1]
    key = key_man_token.format(role='man', content=token)
    # 可能值: man_id, user_id, tel
    who = redis_client.get(key)
    if not who:
        ctx.response.status = '401 Unauthorized'
        return None

    elif len(who) == 24:
        man = Man.objects(id=who).first()
        if not man:
            raise ValueError("No such outsource man with id=[%s]." % who)
        packed = ManLogic.pack_man(man, excludes=(
            'id_card_num', 'id_card_back', 'accounts', 'familiars', 'my_man', 'pick_up_locations', 'create_time'))
        return packed
    elif len(who) == 11:
        man = Man.objects(tel=who).first()
        if not man:
            raise ValueError("No such outsource man with tel=[%s]." % who)
        packed = ManLogic.pack_man(man, excludes=(
            'id_card_num', 'id_card_back', 'accounts', 'familiars', 'my_man', 'pick_up_locations', 'create_time'))
        return packed


@api
@post('/deliveryman/complex_query')
def api_retrieve_deliveryman_info():
    """
    @api {post} /deliveryman/complex_query/:page 基本信息复杂查询
    @apiDescription 查询多条派件员详细信息记录(mongodb __raw__).
    @apiName api_retrieve_deliveryman_info
    @apiGroup man

    @apiParamExample {json} 请求body示例:
        {
            "_id": "56c811a27f452563e439bcb6"
        }
    """
    kw = Schema({
        Optional(object): object,
        Optional("query"): object,

        Optional("page", default=1): schema_int,
        Optional("count", default=20): schema_int,

        Optional("only", default=[]): list,
        Optional("order_by", default=['name']): list,
    }).validate(ctx.request.input())

    page = kw.pop('page')
    count = kw.pop('count')
    only = kw.pop('only')
    order_by = kw.pop('order_by')

    page, count = parse_page_count(dict(page=page, count=count))
    if 'query' in kw:
        query = pickle.loads(kw['query'])
    else:
        query = kw
        if '_id' in query:
            query['_id'] = ObjectId(query['_id'])

    mans = Man.objects(__raw__=query).order_by(*order_by).skip((page * count)).limit(count)
    _count = Man.objects(__raw__=query).count()
    ret = []
    for m in mans:
        m_packed = ManLogic.pack_man(m, only=only)
        ret.append(m_packed)
    ctx.response.set_header("X-Resource-Count".encode('utf-8'), _count)
    return ret[0] if len(ret) == 1 else ret if len(ret) > 1 else {}


@api
@post('/deliveryman/:OPERATION')
def api_trigger_man_event(operation):
    """
    @api {post} /deliveryman/event 事件
    @apiDescription 触发派件员事件, 如果需要, 更新派件员状态和基本信息.
    @apiName api_trigger_man_event
    @apiGroup man

    @apiParam {int} man_id URI中: 派件员工号
    @apiParam {str(32)} event URI中: 派件员事件/操作类型, 支持: `ADD_ACCOUNT`, `ADD_FAMILIAR`, `DEL_FAMILIAR`,
    `COMPLETE_INFO`, `EVENT_RESET`
    @apiParam {int} [operator_id] 操作人id
    @apiParam {str(382)} [remark] 操作备注

    @apiParamExample {json} 请求url示例:
        /deliveryman/event
    @apiParamExample {json} 请求body示例:
        {
            "operator_id": 7774123,
            "remark": "运营拉黑"
        }
    @apiSuccessExample {json} 成功示例:
        HTTP/1.1 200 OK
        {
            "status": "CHECK_WORKING"
        }
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
            "message": "State change failed."
        }
    @apiErrorExample {json} 失败示例:
        HTTP/1.1 400 ValueError
        {
            "message": "Event[EVENT_CITY_SCORE_APP_YE] should be in EMAP..."
        }
    """
    operation = str(operation).upper().strip()
    kw = ctx.request.input()
    # 添加支付宝账户
    if operation == OPERATIONS.ADD_ACCOUNT:
        # required: id, account{name, id}
        result = Man.objects(id=kw.man_id).update_one(add_to_set__accounts=dict(name=kw.name, id=kw.id),
                                                      full_result=True)
        if result['nModified'] == 0:
            logging.warning("Account[%s:%s] already added for man=[%s]." % (kw.id, kw.name, kw.man_id))
            raise ValueError("帐号重复添加.")
    # 添加送单区域
    elif operation == OPERATIONS.ADD_FAMILIAR:
        result = Man.objects(id=kw.man_id).update_one(
            add_to_set__familiars=dict(name=kw.name, city=kw.city, addr=kw.addr, lat=kw.lat, lng=kw.lng),
            full_result=True)
        if result['nModified'] == 0:
            logging.warning("Familiar already added for man=[%s]." % kw.man_id)
            raise ValueError("送单区域重复添加.")
    # 移除送单区域
    elif operation == OPERATIONS.DEL_FAMILIAR:
        Man.objects(id=kw.man_id).update_one(
            pull__familiars=dict(name=kw.name, city=kw.city, addr=kw.addr, lat=kw.lat, lng=kw.lng))
    # 添加取货点(限定是区域经理)
    elif operation == OPERATIONS.ADD_PICKUP:
        pick_up = dict(name=kw.name, city=kw.city, addr=kw.addr, lat=kw.lat, lng=kw.lng)
        result = Man.objects(id=kw.man_id).update_one(add_to_set__pick_up_locations=pick_up, full_result=True)
        if result['nModified'] == 0:
            logging.warning("Pick-up location %s already added for man=[%s]." % (pick_up, kw.man_id))
            raise ValueError("取货点重复添加.")
    # 移除取货点(限定是区域经理)
    elif operation == OPERATIONS.DEL_PICKUP:
        pick_up = dict(name=kw.name, city=kw.city, addr=kw.addr, lat=kw.lat, lng=kw.lng)
        Man.objects(id=kw.man_id).update_one(pull__pick_up_locations=pick_up)
    # 完善资料/修改资料(特殊的事件,不单单是改状态,涉及到基本信息修改)
    elif operation == ManFSM.EVENT_COMPLETE_INFO:
        # 对完善资料特殊添加时间信息
        if 'recommended_by' in kw:
            kw['recommended_by']['time'] = TimeZone.utc_now()
        kw.id_card_num = str(kw.id_card_num).strip().upper()
        man = Man.objects(id_card_num=kw.id_card_num).first()
        # 该身份证号码已经存在且不是本人
        if man and str(man.pk) != str(kw.man_id):
            logging.warning("Man[%s][%s] with id_card_num[%s] already exists." % (man.pk, man.name, kw.id_card_num))
            raise ValueError("该身份证号码已存在")
        # 身份证号可用, 根据man_id找到需要更新资料的人.
        man = Man.objects(id=kw.man_id).first()
        # 此人存在
        if man:
            operator_type = kw.operator_type
            kw.pop('operator_type')
            # 更新参数: name, id_card_num, avatar, id_card_back
            modified_man = ManFSM.update_status(operator_type, man, ManFSM.EVENT_COMPLETE_INFO, **kw)
            # 资料更新失败:
            if not modified_man:
                logging.warning("Update info for man[%s][%s][%s] failed." % (man.pk, man.name, man.status))
                raise ValueError("资料更新失败")
            return ManLogic.pack_man(modified_man)
        # 此人不存在
        else:
            logging.warning("Trying to update a man[%s]'s info that does not exist." % kw.man_id)
            raise ValueError("资料更新失败")
    elif operation in ManFSM.APP_EVENTS or operation in ManFSM.FE_EVENTS:
        # 根据man_id找到需要变更的人.
        man = Man.objects(id=kw.man_id).first()
        # 此人存在
        if man:
            operator_type = kw.operator_type
            kw.pop('operator_type')
            modified_man = ManFSM.update_status(operator_type, man, operation, **kw)
            if not modified_man:
                logging.warning("State transfer for man[%s][%s][%s] using [%s] failed." % (
                    kw.man_id, man.name, man.status, operation))
                raise ValueError("操作失败.")
            return ManLogic.pack_man(modified_man)
    else:
        raise ValueError("OPERATION[%s] should be in %s." % (
            operation, set(OPERATIONS.keys()).union(ManFSM.FE_EVENTS).union(ManFSM.APP_EVENTS)))


@api
@get('/deliveryman/outsource/get/:WHAT')
def api_retrieve_man_info(what):
    what = str(what).upper().strip()
    request = ctx.request.input()
    # 如果传入what,by不是允许的值,直接报错
    if what not in WHATS:
        raise ValueError("WHAT[%s] should be in WHATS%s." % (what, list(WHATS.keys())))
    params = set([str(k).lower().strip() for k in request])
    bys = set(BYS.keys())
    by = params.intersection(bys)
    if not by:
        raise ValueError("BY%s should be in BYS%s." % (list(params), list(bys)))
    by_key = next(iter(by))
    by_val = request[by_key]
    if by_key == 'id' and by_val and len(by_val) != 24:
        raise ValueError('find man with id=%s, id should be of length 24.' % by_val)
    # 判断是要什么类型的返回
    if what == WHATS.BASIC:
        excludes = ('accounts', 'create_time', 'my_man')
        man = Man.objects(**{by_key: by_val}).exclude(*excludes).first()
        if not man:
            raise ValueError("Can't find man with[%s]=[%s]." % (by_key, by_val))
        packed = ManLogic.pack_man(man, excludes=excludes)
        ret_cnt = ('familiars', 'pick_up_locations')
        for k in ret_cnt:
            if k in packed:
                packed[k] = len(packed[k]) if packed[k] else 0
        return packed
    elif what == WHATS.ACCOUNT_LIST:
        man = Man.objects(**{by_key: by_val}).only('accounts').first()
        return man.accounts
    elif what == WHATS.FAMILIAR_LIST:
        man = Man.objects(**{by_key: by_val}).only('familiars').first()
        return man.familiars
    elif what == WHATS.STATUS:
        man = Man.objects(**{by_key: by_val}).only('status').first()
        return man.status
    elif what == WHATS.MAN_LIST:
        man = Man.objects(**{by_key: by_val}).only('my_man').first()
        if man and man.my_man:
            only = ('status', 'id', 'name', 'tel', 'avatar')
            my_man = {m['id']: m['bind_time'] for m in man.my_man}
            mans = Man.objects(id__in=list(my_man.keys())).only(*only)
            ret = []
            for m in mans:
                packed_man = ManLogic.pack_man(m, only=only)
                packed_man['bind_time'] = my_man[str(m.pk)]
                ret.append(packed_man)
            return ret
        else:
            return []
    elif what == WHATS.CODE:
        # 取header里面的app-name, 没给的话就给man
        app_name = ctx.request.header('app-name', 'man')
        man_id = by_val
        code = shortuuid.ShortUUID().random(length=8)
        # role是区域经理app端header里面的app-name
        key = key_man_code.format(role=app_name, content=code)
        # 存放: 二维码(360秒): get <app-name>:code:fe11ad907e2fa779ed2f363ef589d3f9 => 56f1028b2d50c07c80914393
        redis_client.setex(key, man_id, 360)
        logging.info('Setting Code [%s] => [%s].' % (key, man_id))
        return key
    elif what == WHATS.PICKUP_LIST:
        man = Man.objects(**{by_key: by_val}).only('pick_up_locations').first()
        return man.pick_up_locations
    elif what == WHATS.SIGN_IN_COUNT:
        # 获取人员名字
        man = Man.objects(id=by_val).only('name').first()
        name = man.name if man.name else ''
        # 获取今天凌晨以后的签到记录次数
        now = TimeZone.local_now()
        start_time, _end_time = TimeZone.day_range(value=now)
        start_time = TimeZone.datetime_to_str(start_time)
        sign_in_count = SignIn.objects(**{by_key: by_val, 'create_time__gte': start_time}).count()
        return dict(name=name,
                    sign_in_count=sign_in_count,
                    server_time=TimeZone.datetime_to_str(now, pattern='%Y-%m-%dT%H:%M:%S'))


@api
@post('/deliveryman/fsm_log/complex_query')
def api_retrieve_man_fsm_log_info():
    """
    @api {post} /man_fsm_log/complex_query/:page 状态变迁复杂查询
    @apiDescription 查询派件员状态变迁详细记录.
    @apiName api_retrieve_man_fsm_log_info
    @apiGroup man

    @apiParam {list} filter_col `["man_id", "event" ...]`. 表`man_fsm_log`中的字段列表. `[]`表示取所有字段.
    @apiParam {str} [group_by] 按照什么来group by. 表`man_fsm_log`中的字段. 如`man_id`.
    @apiParam {str} op `AND`或者`OR`. 表示如何组合过滤条件.
    @apiParam {int} is_not 如果有这个key, 则表示该字段上的过滤条件要取非.
    @apiParam {int} page 2. 表示第二页, 从1开始. [1:2147483648), 分页查. <=2000条数据, 一次返回所有; >2000条, 一次返回2000条.

    @apiParamExample {json} 请求body示例:
        {
            "filter_col": ["man_id", "remark"],
            "query":
                {
                    "op": "AND",
                    "exprs": [
                        {"from_status": {"in": ["CHECK_WORKING", "CHECK_BINDING_TEAM"]}},
                        {"event": {"like": "%APPLY_RESIGN%"}},
                        {"is_not":1, "remark": {"like": "%测试%"}}
                    ]
                },
            "group_by": "man_id"
        }
    @apiParamExample {json} 对于"query"部分的解释 expr_json_example:
        expr_json_atom = {
            "op": "AND",
            "exprs": [
                {"from_status": {"in": ["CHECK_WORKING", "CHECK_BINDING_TEAM"]}},
                {"event": {"like": "%APPLY_RESIGN%"}},
                {"is_not":1, "remark": {"like": "%测试%"}}
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
        [7811907, 7792622, 7792648, 7792648, 7812168, 7812168, 7812168, 7812168]

    @apiSuccessExample {json} 成功示例(filter_col列表长度大于1,即查询多个值时):
        HTTP/1.1 200 OK
        [
            {
                "man_id": 7794966,
                "real_name": "频繁更换商家导致工资减少"
            },
            {
                "man_id": 7770322,
                "real_name": "没有商家预约"
            }
        ]
    """
    filter_col_str, where, group_by_limit, args = complex_query(ctx.request.input())
    return ManFSMLogLogic.find_by(filter_col_str, where, group_by_limit, *args)


# === 解绑/绑定/申请解绑工作关系相关 ===
@api
@post('/deliveryman/working_relation/del_man')
def api_working_relation_del_man():
    # 输入: manager_id, man_id
    kw = ctx.request.input()
    manager = Man.objects(id=kw.manager_id).first()
    man = Man.objects(id=kw.man_id).first()
    err_str = "Unbind man[%s][%s] for manager[%s][%s] failed." % (kw.man_id, man.name, kw.manager_id, manager.name)
    # 检查从属关系
    if not man or not manager:
        raise ValueError("解绑工作关系失败:找不到相关人员.")
    if not man.my_manager or not manager.my_man:
        logging.error(err_str)
        raise ValueError("解绑工作关系失败:关联人员不一致.")
    if str(man.my_manager['id']) != str(manager.pk):
        logging.error(err_str)
        raise ValueError("解绑工作关系失败:关联人员不一致.")
    if str(Man.objects(my_man__id=kw.man_id).first().pk) != str(manager.pk):
        logging.error(err_str)
        raise ValueError("解绑工作关系失败:关联人员不一致.")

    # 我是区域经理:
    bind_time = man.my_manager['bind_time']
    one_man = dict(id=kw.man_id, name=man.name, tel=man.tel, bind_time=bind_time)
    # 1. 去掉我的Document下的那个小弟
    # result = Man.objects(my_man__id=kw.man_id).update_one(full_result=True, **{'unset__my_man__$': 1})
    result = manager.update(pull__my_man__id=kw.man_id, full_result=True)
    if result['nModified'] == 0:
        logging.error(err_str)
        raise ValueError("解绑工作关系失败.")
    # 2. 去掉小弟Document下的my_manager
    result = man.update(my_manager=None, full_result=True)
    if result['nModified'] == 0:
        manager.update(add_to_set__my_man=one_man)
        logging.error(err_str)
        raise ValueError("解绑工作关系失败.")
    # 移除小弟成功: 发短信通知小弟
    async_send_sms(man.tel, '您好，您与区域经理%s %s 的工作关系已解除，请知悉.' % (manager.name, manager.tel), sms_type=SMS_TYPE_NORMAL)


@api
@post('/deliveryman/working_relation/bind_manager')
def api_working_relation_bind_manager():
    # 输入: code=>从redis取到manager_id, man_id
    kw = ctx.request.input()
    manager_id = redis_client.get(kw.code)
    if not manager_id:
        raise ValueError("绑定工作关系失败:无效二维码.")
    manager = Man.objects(id=manager_id).first()
    man = Man.objects(id=kw.man_id).first()
    err_str = "Bind man[%s][%s] for manager[%s][%s] failed." % (kw.man_id, man.name, manager_id, manager.name)
    # 检查从属关系
    if not man or not manager:
        raise ValueError("绑定工作关系失败:找不到相关人员.")
    if man.my_manager:
        logging.error(err_str)
        raise ValueError("绑定工作关系失败:您已绑定过.")
    if Man.objects(my_man__id=kw.man_id).first():
        logging.error(err_str)
        raise ValueError("绑定工作关系失败:重复绑定.")

    # 我是小弟:
    now = utc_8_now(ret=str('datetime'))
    one_man = dict(id=kw.man_id, name=man.name, tel=man.tel, bind_time=now)
    one_manager = dict(id=manager_id, name=manager.name, tel=manager.tel, bind_time=now)
    # 1. 将小弟加入manager的那个Document里面
    result = Man.objects(id=manager_id).update_one(add_to_set__my_man=one_man, full_result=True)
    if result['nModified'] == 0:
        logging.error(err_str)
        raise ValueError("绑定工作关系失败.")
    # 2. 将小弟Document加入my_manager
    result = Man.objects(id=kw.man_id).update_one(set__my_manager=one_manager, full_result=True)
    if result['nModified'] == 0:
        Man.objects(id=kw.manager_id).update_one(pull__my_man=one_man)
        logging.error(err_str)
        raise ValueError("绑定工作关系失败.")


@api
@get('/deliveryman/working_relation/apply_unbind_manager')
def api_working_relation_apply_unbind_manager():
    # 输入: man_id
    kw = ctx.request.input()
    man = Man.objects(id=kw.man_id).first()
    if man and man.my_manager:
        manager_id = man.my_manager['id']
        manager = Man.objects(id=manager_id).first()
        if manager and manager.tel:
            # 给manager发短信
            async_send_sms(manager.tel, '派件员%s %s 申请解除绑定关系，请尽快处理！' % (man.name, man.tel), sms_type=SMS_TYPE_NORMAL)
    else:
        raise ValueError("找不到相关人员.")


# === 提现相关 ===
@api
@post('/deliveryman/outsource/:CASH_FLOW')
def api_outsource_cash_flow(cash_flow_type):
    # 参数处理
    cash_flow_type = str(cash_flow_type).upper().strip()
    kw = ctx.request.input()
    transact_num = utc_8_day().replace('-', '') + shortuuid.ShortUUID().random(length=6)
    kw['transact_num'] = kw.get('transact_num', transact_num)
    kw['type'] = cash_flow_type

    # 数据1: 可提现can_cash = VALIDATED - APPLY_WITHDRAW
    # 数据2: 待财务处理finance = APPLY_WITHDRAW - PAID - DECLINE
    # 数据3: 财务已打款paid = PAID
    # 数据4: 财务已拒绝decline = DECLINE
    # 后台已审核的派件员运单
    if cash_flow_type == CASH_FLOW.VALIDATED:
        # 提现流水 {transact_num, man_id, type, cash, expr_num, operator, create_time}
        FlowLogic.push_validated(**kw)
    # 申请提现
    elif cash_flow_type == CASH_FLOW.APPLY_WITHDRAW:
        # 限制1: 如果是系统有效全职,不可提现. ==>暂时通过登录来控制
        # 限制2: 限额设为sum(VALIDATED)-sum(APPLY_WITHDRAW)
        # 提现流水 {transact_num, man_id, type, cash, create_time}
        FlowLogic.push_apply_withdraw(**kw)
    # 财务打款
    elif cash_flow_type == CASH_FLOW.PAID:
        # 根据transact_num拿对应的man_id
        # 提现流水更新 {transact_num, "PAID", cash, <operator>, update_time}
        FlowLogic.paid(**kw)
    # 财务拒绝
    elif cash_flow_type == CASH_FLOW.DECLINE:
        # 提现流水更新 {transact_num, "DECLINE", cash, <operator>, update_time, remark}
        FlowLogic.decline(**kw)
    else:
        raise ValueError("CASH_FLOW[%s] should be in CASH_FLOW%s." % (cash_flow_type, CASH_FLOW))
    return kw['transact_num']


@api
@post('/deliveryman/flow/complex_query')
def api_retrieve_flow():
    filter_col_str, where, group_by_limit, args = complex_query(ctx.request.input())
    return FlowLogic.find_by(filter_col_str, where, group_by_limit, *args)


@api
@post("/deliveryman/flow_statistics/complex_query")
def api_retrieve_flow_statistics():
    filter_col_str, where, group_by_limit, args = complex_query(ctx.request.input())
    return FlowStatisticsLogic.find_by(filter_col_str, where, group_by_limit, *args)


if __name__ == "__main__":
    print((set(OPERATIONS.keys()).union(ManFSM.FE_EVENTS).union(ManFSM.APP_EVENTS)))
