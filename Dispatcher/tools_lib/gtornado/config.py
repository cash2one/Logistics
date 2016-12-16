# coding=utf-8
# __author__ = 'mio'


# >>>>> 各种订单的类型 <<<<<
WHOLESALE_EC_NUMBER_TYPE = "wholesale_ec"   # 电商发货



# 电商发货订单状态

# 已创建, 待分拣
EXPR_STATUS_CREATED = "CREATED"
# 城际司机已揽件
EXPR_STATUS_SORTED = "SORTED"
# 城内司机已揽件
EXPR_STATUS_ADOPTED = "ADOPTED"
# 配送员已取货, 配送中, 待完成
EXPR_STATUS_SENDING = "SENDING"
# 待上传凭证
EXPR_STATUS_WAIT_EVIDENCE = "WAIT_EVIDENCE"
# 妥投
EXPR_STATUS_FINISHED = "FINISHED"
# 关闭, 取消
EXPR_STATUS_CLOSED = "CLOSED"
# 异常
EXPR_STATUS_ERROR = "ERROR"

# ---------------------------------------- 第三方订单配置 ------------------------------------------------

# 普通电商发货单
NORMAL_ORDER_TYPE = "WM"

# >>>>>> 拼好货 PHH <<<<<<
# 截止订单时间, local_time
PHH_ORDER_TYPE = "PHH"
# PHH_END_WAIT_TIME = {"hour": 23}
PHH_SHOP_ID = 15081
PHH_SHOP_TEST_ID = 15530
# 拼好货secret_key
PHH_SECRET_KEY = "4d5e6d38595a552bcbf6f2433e4324f1"

hz_nodes = {
    "西湖区": "567a5a37421aa971b1f100aa",   # 杭州西湖华星网点
    "拱墅区": "567cafb3421aa991d8a4ae22",   # 杭州大关二网点
    "上城区": "567a5a37421aa971b1f100a9",   # 杭州上城庆春网点
    "下城区": "567cafb3421aa991d8a4ae21",   # 杭州西湖文化广场网点
    "江干区": "567a5a37421aa971b1f100a2",   # 杭州中沙网点
    "滨江区": "567a5a38421aa971b1f100b0",   # 杭州滨江长河网点
}

# 众包配送员默认id
MASS_COURIER_ID = 2
# 众包类型
MASS_COURIER_TYPE = "MASS"
# 审核状态
MASS_EXPRESS_VALID = "VALID"
MASS_EXPRESS_INVALID = "INVALID"
MASS_EXPRESS_WAIT = "WAIT"

# 全职配送员类型
FULL_TIME_COURIER_TYPE = "FULL-TIME"

# 仓库默认id
WAREHOUSE_ID = 3

# ------------------------ 一米鲜 ------------------------
YMX_ORDER_TYPE = "YMX"
YMX_SHOP_ID = '56cd130e421aa973b8ccb32b'
YMX_SHOP_USER = 7817088

YMX_TEST_SHOP_ID = 17066
YMX_TEST_SHOP_USER = 7817089

YMX_USER_KEY = "fxs"
YMX_TOKEN = "2f4458bcaf025ea85720b01af0ab3cf3"

YMX_CREATE_KEY = "1mxian"
YMX_CREATE_TOKEN = "348aaddb21d380cae0b12fa0ae5d63c3"
