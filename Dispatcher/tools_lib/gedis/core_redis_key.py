# coding:utf-8
__author__ = 'Harrison'

# 统一管理系统内所有redis的键名

#########################################################################
# 配送员
#########################################################################
# 免密码登录帐号集合 type -> set
key_no_password = "no_password"
# 派件员/内部职员token type -> str
key_man_token = "{role}:token:{content}"
# 区域经理二维码 type -> str
key_man_code = "{role}:code:{content}"


#########################################################################
# mall
#########################################################################
# 商户信息  type -> hash
key_shop_info = "mall:shop:{shop_id}"
# 商户token type -> str
key_shop_token = "shop:token:{content}"

#########################################################################
# 微信支付JS-SDK相关
#########################################################################
key_access_token = "wxPay:access_token"
key_jsapi_ticket = "wxPay:jsapi_ticket"

#########################################################################
# GPS相关
#########################################################################
# 最新的GPS记录
key_deliver_last_gps = 'gps:last_gps:{user_id}'


########################################################################
# 线路推荐: 可下单可送达
########################################################################
# type -> str
# 线路: [{id,t,coordinate,name}...]
key_nodes = 'express:route:orbit'
# 今日线路排班: {<driver_id>:{run:[{id,t,coordinate,name}]}}
key_schedule_today = 'express:route:schedule_today'
# 线路解空间
key_solution_space = 'express:route:solution_space'


#########################################################################
# 短信相关
#########################################################################
# 控制短信发送频率
key_sms_rate_limit = "sms:rate:{tel}"
# 短信验证码
key_sms_code = "sms:code:{tel}"


#########################################################################
# 其他
#########################################################################
# type -> str: todo: del me after song.123feng.com changed the login api to new
key_token = "token:{content}"
# type -> hash
key_area_code = "area:province:{province_name}:city:{city_name}:district:{district_name}"
# type -> str 接口调用计数器
key_api_call_count = 'api:count:{method}:{url}'
# type -> str 日志中心-API调用记录
key_api_call_record = 'log_center:api:record'
# 旷工日期
key_deliver_auto_quit_absent_days = "user_center:deliver:{user_id}:quit:absent_days"
