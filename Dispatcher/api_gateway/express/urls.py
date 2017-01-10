# coding:utf-8

from handlers import fh, ps, song, yun, cha, pj, qyjl

urls = []
urls += [
    # ==> APP接口 <==
    # 发货端/ios/h5/song
    # [GET] 查询单个运单
    (r'^/express/(fh|h5)/single/(\w+)$', fh.SingleExpressHandler),
    # [POST] 一键呼叫,不扣钱
    (r'^/express/(fh|h5)/call$', fh.Call),
    # [GET] 运单列表: 配送中/已送达
    (r'^/express/(fh|h5)/multi$', fh.ExpressHandler),
    # [POST] 立即下单,不扣钱  [DELETE] 撤销运单
    (r'^/express/(fh|h5)/single$', fh.SingleExpressHandler),
    # [GET] 运单列表: 待配送员定价收件 [PATCH] 商户支付单个/多个运单
    ('^/express/(fh|h5|song)/multi_with_cash$', fh.ExpressListWithCash),
    # [GET] 各状态运单数目统计
    (r'^/express/(fh|h5)/aggregation/status$', fh.AggregationStatusHandler),
    # [GET] 计费查询器
    (r'^/express/(fh|h5)/pricing$', fh.Pricing),
    # [GET] 查询围栏
    (r'^/express/(fh|h5)/fence$', fh.Fence),

    # ==> 配送系列通用: 环线\派件\区域经理\仓管 <==
    # ps: 表示所有配送端都能调用
    # pj: 派件端, qyjl: 区域经理
    # [GET] 一键呼叫数据
    (r'^/express/ps/call$', ps.Call),
    # [GET] 呼叫内的客户运单列表
    (r'^/express/ps/call/expr_list$', ps.ExprListInCall),

    # [PATCH] 抢呼叫
    (r'^/express/ps/call/assignee$', ps.AssignCallToMe),
    # [PATCH] 加单
    (r'^/express/ps/call/add_expr$', ps.AddExprToCall),
    # [GET] 获取订单基础价格
    (r'^/express/ps/call/fh_base$', ps.FhBase),
    # [PATCH] 发起收款: 获取微信/支付宝收款二维码
    (r'^/express/ps/call/pay_us$', ps.PayUsFromCall),
    # [PATCH] 取消运单: 属于呼叫状态机
    (r'^/express/ps/single/(\w+)/assignee_cancel$', ps.AssigneeCancel),
    # [PATCH] 扫码收件: 属于呼叫状态机
    (r'^/express/ps/single/(\w+)/assignee_sj$', ps.AssigneeSJ),
    # [PATCH] 关闭呼叫入口
    (r'^/express/ps/call/close$', ps.CloseThisCall),
    # [GET] 查询围栏
    (r'^/express/ps/fence$', ps.Fence),
    # [GET] 判断点是否落入任一围栏
    (r'^/express/ps/fence/point_within$', ps.FencePointWithin),


    # [GET] 传递端搜索收寄信息
    ('^/express/ps/client_address/fuzzy_search$', ps.CliAddressFuzzySearch),
    # [GET] 获取重量对应的溢价 [PATCH] 所有角色改价
    (r'^/express/ps/pricing$', ps.Pricing),

    # [GET] 运单详情
    (r'^/express/ps/single/(\w+)$', ps.SingleExpressHandler),
    # [GET] 抢单列表
    (r'^/express/ps/pool$', ps.ExpressPool),
    # [PATCH] 抢占派件的坑
    (r'^/express/ps/expr/assignee$', ps.WillOccupy),
    # [GET] 收派列表(任务列表)
    (r'^/express/ps/sending$', ps.ExpressSending),
    # [GET] 收派列表 - 状态筛选/运单搜索/历史运单
    (r'^/express/ps/multi$', ps.ExpressHandler),
    (r'^/express/ps/map$', ps.ExpressMap),
    # (r'^/express/ps/aggregation/status$', ps.AggregationStatusHandler),
    # [GET] 交接人列表
    (r'^/express/ps/candidates$', ps.Candidates),
    # [PATCH] 扫码派件
    (r'^/express/ps/single/(\w+)/assignee_qj$', ps.AssigneeQJ),

    # [GET] 根据id获取人员签到列表
    ('^/express/ps/my_schedule$', ps.MySchedule),


    # ==> 派件端 <==
    # [GET] 去收件时获取某商户待领取的运单 todo del me
    (r'^/express/pj/multi/filled$', pj.FilledExpressHandler),
    # [PATCH] 领取运单 [GET] 领取运单/代客户下单后, 获取已领取运单列表, 总计运费, 已领单数 todo del me
    (r'^/express/pj/assignee$', pj.AssignToMe),
    # [PATCH] 送达
    (r'^/express/pj/single/(\w+)$', pj.SingleExpressHandler),
    # [PATCH] 标记异常
    (r'^/express/pj/single/(\w+)/error$', pj.ErrorHandler),

]
urls += [
    # ==> WEB接口:song.123feng.com <==
    # [POST] 批量创建运单, [GET] 搜索或者是查询运单列表
    (r"^/express/song/multi$", song.Express),
    # [GET] 获取一个运单的详情
    (r"^/express/song/single/(\w+)$", song.SingleExpress),
    # [GET] 运单导出
    (r"^/express/song/export$", song.ExportHandler),
    # [POST] 上传excel文档parse之后返给前端,用于导入运单
    (r"^/express/song/excel_parse$", song.ExcelParseHandler),
    # [GET] 给前端解析经纬度
    (r"^/express/song/address_parse$", song.GeoLocationHandler),
    # [GET] song上面显示每种状态运单的数
    (r"^/express/song/aggregation/status$", song.AggregationStatusHandler)
]
urls += [
    # ==> WEB接口:yun.123feng.com/cha.123feng.com <==
    # [GET] 搜索或者查询运单列表
    (r"^/express/yun/multi$", yun.Express),
    # [GET] 获取一个运单的详情 [PATCH] 审核不通过
    (r"^/express/yun/single/(\w+)$", yun.SingleExpress),
    # [GET] 获取一个运单的追踪信息
    (r"^/express/cha/single/(\w+)$", cha.SingleExpress),
    # [PATCH] 指派, 相当于派件端扫码收件/扫码派送
    (r'^/express/yun/single/(\w+)/assignee_zp$', yun.AssigneeZP),
    # [GET] 商户下单数据
    (r'^/express/yun/stat/customer_placing_order', yun.StatCustomerPlacingOrder),
    # [GET] 子公司运营数据
    # (r'^/express/yun/op_data', yun.OpDataHandler),
    # [GET] 一键呼叫数据
    (r'^/express/yun/call$', yun.Call),
    # 站点详情
    (r'^/express/yun/node/single$', yun.OneNode),
    # 站点添加/删除/列表
    (r'^/express/yun/node$', yun.Node),
    # 站点名,地址修改/添加时刻(与人)/删除时刻(与人)/修改时刻(与人)
    (r'^/express/yun/node/modify_basic$', yun.NodeModifyBasic),
    (r'^/express/yun/node/add_time$', yun.NodeAddTime),
    (r'^/express/yun/node/del_time$', yun.NodeDelTime),
    (r'^/express/yun/node/modify_time$', yun.NodeModifyMan),
    # [GET] [PATCH] [POST] [DELETE] 围栏
    (r'^/express/yun/fence$', yun.Fence),
]

