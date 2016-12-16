#coding=utf-8
# @Date    : 2015-08-26 17:28:27
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo


def unauthorized_error():
    """
        @apiDefine UnauthorizedError
        @apiError (Error 4xx) {401} UnauthorizedError 授权信息出错
        @apiErrorExample 401-UnauthorizedError
            HTTP/1.1 401 UNAUTHORIZED
            {
                "message": "授权信息出错",
                "error_code": 0,
                "content": null
            }
    """


def search_error():
    """
        @apiDefine NotFoundEntityError
        @apiError (Error 4xx) {400} NotFoundEntityError 找不到需要操作的对象
        @apiErrorExample 400-NotFoundEntityError
            HTTP/1.1 400 BAD REQUEST
            {
                "message": "找不到需要操作的对象, 请检查参数",
                "error_code": 0,
                "content": null
            }
    """


def client_error():
    """
        @apiDefine ClientError

        @apiError (Error 4xx) {400} ParamsError 参数解析错误
        @apiErrorExample 400-ParamsError
            HTTP/1.1 400 BAD REQUEST
            {
                "message": "参数解析错误",
                "error_code": 0,
                "content": null
            }


        @apiError (Error 4xx) {404} NotFoundError 未找到请求的url
        @apiErrorExample 404-NotFoundError
            HTTP/1.1 404 NOT FOUND
            {
                "message": "404 NOT FOUND",
                "error_code": 0,
                "content": null
            }

        @apiError (Error 4xx) {422} UnprocesableEntityError 当创建一个对象时，发生一个验证错误。
        @apiErrorExample 422-UnprocesableEntityError
            HTTP/1.1 422 UNPROCESABLE ENTITY
            {
                "message": "当创建一个对象时，发生一个验证错误",
                "error_code": 0,
                "content": null
            }
    """


def server_error():
    """
        @apiDefine ServerError
        @apiError (Error 5xx) {500} InternalServerError 服务器发生错误，用户将无法判断发出的请求是否成功。
        @apiErrorExample 500-InternalServerError
            HTTP/1.1 500 INTERNAL SERVER ERROR
            {
                "message": "系统错误",
                "error_code": 0,
                "content": null
            }
    """


def auth_header_mixin():
    """
        @apiDefine AuthHeader

        @apiHeaderExample Auth-Header-Example
            {
                "Authorization": "token 5b42e18555c11dbf2c31403ea6b706a6"
            }
        @apiHeader {string} Authorization 验证身份，格式为"token {token}"，注意"token"后面需要一个空格
    """
    pass


def delete_success_minx():
    """
        @apiDefine DeleteSuccess

        @apiSuccessExample 204-NO-CONTENT
            HTTP/1.1 204 NO CONTENT

    """


def conflict_time():
    """
    @apiDefine ConflictTimeError

    @apiError (Error 4xx) {409} ConflictTimeError 时间冲突错误
    @apiErrorExample 409-ConflictTimeError
        HTTP/1.1 409 Conflict Time Error
        {
            "message": "商户定义的时间内车辆不可用",
            "error_code": 4000,
            "content": null
        }
    """
    pass


def vehicle_return_object():
    """
    @apiDefine VEHICLE_RETURN_OBJECT

    @apiSuccess (Success-Response) {int} error_code=0 错误状态码
    @apiSuccess (Success-Response) {string} message='""' 请求处理结果说明信息
    @apiSuccess (Success-Response) {list/dict} content 查询返回列表,创建或修改返回字典

    @apiSuccess (Success-Response) {string} content.id 车辆ID
    @apiSuccess (Success-Response) {string} content.image 照片
    @apiSuccess (Success-Response) {string} content.plate_number 车牌号
    @apiSuccess (Success-Response) {string} content.licence_number 行驶证
    @apiSuccess (Success-Response) {float} content.distance 里程数, 单位: 公里
    @apiSuccess (Success-Response) {int='1: 电动汽车', '2: 燃油汽车', '3: 冷链车'} content.car_type 车型
    @apiSuccess (Success-Response) {int='1: 自营', '2: 外包'} content.affiliation 归属
    @apiSuccess (Success-Response) {string} content.annual_inspection_effective_date 年检开始时间
    @apiSuccess (Success-Response) {string} content.annual_inspection_expiry_date 年检结束时间

    @apiSuccess (Success-Response) {dict} content.city 所在城市
    @apiSuccess (Success-Response) {string} content.city.name 城市名
    @apiSuccess (Success-Response) {int} content.city.code 城市编码

    @apiSuccess (Success-Response) {dict} content.insurance 保险
    @apiSuccess (Success-Response) {string} content.insurance.name 保险名称
    @apiSuccess (Success-Response) {float} content.insurance.limit 保险金额, 单位: 万
    @apiSuccess (Success-Response) {string} content.insurance.effective_date 有效期开始时间
    @apiSuccess (Success-Response) {string} content.insurance.expiry_date 有效期结束时间

    @apiSuccess (Success-Response) {dict} content.driver 驾驶员
    @apiSuccess (Success-Response) {int} content.driver.id ID
    @apiSuccess (Success-Response) {string} content.driver.name 名字
    @apiSuccess (Success-Response) {int='1: 男', '2: 女'} content.driver.sex 性别
    @apiSuccess (Success-Response) {int} content.driver.age 年龄
    @apiSuccess (Success-Response) {int='1: A照', '2: B照', '3: C照'} content.driver.licence_type 驾照类型
    @apiSuccess (Success-Response) {int} content.driver.driving_experience 驾龄
    @apiSuccess (Success-Response) {string} content.driver.tel 电话
    @apiSuccess (Success-Response) {string} content.driver.avatar 头像

    @apiSuccess (Success-Response) {list} content.shops 绑定的商户信息,列表格式
    @apiSuccess (Success-Response) {int} content.shops.id 商户ID
    @apiSuccess (Success-Response) {string} content.shops.name 商户名
    @apiSuccess (Success-Response) {string} content.shops.tel 商户电话
    @apiSuccess (Success-Response) {list} content.shops.timetable 时间表,列表格式
    @apiSuccess (Success-Response) {string} content.shops.timetable.arrive_time 到点时间
    @apiSuccess (Success-Response) {string} content.shops.timetable.leave_time 离店时间
    @apiSuccess (Success-Response) {int} content.shops.timetable.duration 停留时间
    @apiSuccess (Success-Response) {list} content.shops.timetable.period 每周的服务日期, 0: 未勾选, 1: 勾选

    @apiSuccess (Success-Response) {list} content.tasks 车辆的任务列表
    @apiSuccess (Success-Response) {string} content.tasks.arrive_time 到达时间
    @apiSuccess (Success-Response) {string} content.tasks.leave_time 离开时间
    @apiSuccess (Success-Response) {string} content.tasks.duration 停留时间
    @apiSuccess (Success-Response) {list} content.tasks.period 每周的服务日期
    @apiSuccess (Success-Response) {string} content.tasks.name 商户名或站点名
    @apiSuccess (Success-Response) {int} content.tasks.id 商户ID或站点ID
    """
    pass


def vehicle_path_return_object():
    """
    @apiDefine VEHICLE_PATH_RETURN_OBJECT

    @apiSuccess (Success-Response) {int} error_code=0 错误状态码
    @apiSuccess (Success-Response) {string} message='""' 请求处理结果说明信息
    @apiSuccess (Success-Response) {list/dict} content 查询返回列表,创建或修改返回字典
    @apiSuccess (Success-Response) {string} content.name 线路的名字/编号
    @apiSuccess (Success-Response) {int='0: 关闭', '1: 开启'} content.status 线路的状态
    @apiSuccess (Success-Response) {dict} content.city 线路所属的城市
    @apiSuccess (Success-Response) {string} content.city.name 城市名
    @apiSuccess (Success-Response) {int} content.city.code 城市编号
    @apiSuccess (Success-Response) {dict} content.vehicle 线路中绑定的车辆,未绑定为None,具体字段解释见车辆接口
    @apiSuccess (Success-Response) {list} content.nodes 线路中绑定的网点
    @apiSuccess (Success-Response) {string} content.nodes.arrive_time 到达网点的时间
    @apiSuccess (Success-Response) {string} content.nodes.leave_time 离开网点的时间
    @apiSuccess (Success-Response) {dict} content.nodes.node 网点信息,具体字段解释见网点接口
    """
    pass
