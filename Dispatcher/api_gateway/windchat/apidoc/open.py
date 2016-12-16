#coding=utf-8
__author__ = 'kk'


def SERVER_DEFINITION():
    """
    @api {definition} overall/definition 综合定义
    @apiDescription 风信通用接口综合定义
    @apiName open_wc4_overall_definition
    @apiGroup open_windchat
    @apiParamExample 定义

    服务IP: 182.92.240.69(外) 10.171.103.109(内)
    端口: 5000
    cli: 指的是频道在 leancloud 的 id,即频道 id
    client_id: 任何参与聊天的人的 id, 特殊的 client_id 是"SYSTEM_ANSWERER", 表示是系统通知消息, 不是任何人发出的消息
    业务账户: 跟业务逻辑相关的账户体系,现有的账户: man配送线 shop发货线 staff职能线, account_type是用于区分不同账户体系的命名空间
    风信账户: 风信用 client_id标识账户, 一个 client_id可能可以关联多个业务账户,然而一个业务账户只能有一个 client_id

    """
    pass


def GET_DAS_PORT():
    """
    @api {GET} http://PYTHON-SERVER:5000/port 获取 python 服务核心层生产端口
    @apiDescription 获取 python 服务核心层生产端口
    @apiName open_wc4_get_das_port
    @apiGroup open_windchat
    @apiSuccessExample 成功返回
    HTTP/1.1 200 OK
    9099 (或者9199)
    """
    pass


def GET_MQ_EXCHANGE():
    """

    """
    pass


def SENDING_WC4_MESSAGE():
    """
    @api {POST} http://PYTHON-SERVER:5000/windchat/open/message/channel 发消息
    @apiDescription 消息发送接口
    @apiName open_wc4_sending_channel_message
    @apiGroup open_windchat

    @apiParam (json body) {string} type 发送类型
    @apiParam (json body) {string} scheduled_time 发送时间
    @apiParam (json body) {string} token 定时发送凭证
    @apiParam (json body) {array} data 消息体

    @apiParamExample {json} 即刻发送消息
    {
        "type": "SEND-NOW"
        "data":[
            {windchat-object},...
        ]
    }

    @apiParamExample {json} 定时发送消息(暂时未实现)
    {
        "type": "SCHEDULE"
        "scheduled_time": // 定时发送的时间(如果是定时发送的话),utc,形如"2016-12-12T12:12:12Z"
        "data":[
            {windchat-object},...
        ]
    } // 这种情况下,请求的返回会带有token, 可以凭 token 撤销此次预约
    ret: {
        "token": "tofjsopg24tj" // 此次预约的 token
    }

    @apiParamExample {json} 撤销定时发送预约(暂时未实现)
    {
        "type": "SCHEDULE-CANCEL"
        "token": "fhwe0t2v" // 给出预约时返回的 token,用以撤销此次预约
    }

    @apiParamExample {json} {windchat-object}
    {
        "from_peer":                                                // 发出方, 通常如果用作系统消息, 缺省为"SYSTEM_ANSWERER"
        "to_peers":                                                 // 用户client_id的 array
        "message": {
            "message_type": 1,                                      // 消息类型(缺省1, 即普通文本,其他类型见消息类型定义)
            "message": {...},                                       // 消息实体(见消息结构定义)
            "talker_avatar": "",                                    // 头像图 url(缺省展示默认客服头像)
            "talker_name": "姓名",                                   // 显示名(缺省显示系统通知)
            "talker_id": "talker account id",                       // 原本账户的 id(缺省为匿名客服)
            "talker_type": "man" "shop" "staff"                     // 账户类型(缺省"staff",如果是系统消息,这个字段无意义)
        }
        "conv_id": "cnz1cmc9cbeowgh"                                // 频道cli(缺省为当前用户类型的默认频道)
    }
    """
    pass


def ACCOUNT_CREATE():
    """
    @api {POST} http://PYTHON-SERVER:核心层端口/windchat/das/account 注册风信
    @apiDescription 创建风信账户, 所有参与聊天的账户必须注册风信账户以获得client_id
    @apiName open_wc4_account_create
    @apiGroup open_windchat

    @apiParam (json body) {string} account_id 账户id
    @apiParam (json body) {string} account_type 账户类型(man配送线 shop发货线 staff职能线)

    @apiParamExample {json} 请求示例
    {
        "account_id": "7792658",
        "account_type": "man"
    }
    @apiSuccessExample {json} 成功示例
    HTTP/1.1 201 Created
    """
    pass


def ACCOUNT_QUERY():
    """
    @api {POST} http://PYTHON-SERVER:核心层端口/windchat/das/account/query 查询账户
    @apiDescription 查询风信账户,account_id->client_id,或者反过来
    @apiName open_wc4_account_query
    @apiGroup open_windchat

    @apiParam (json body) {string} account 业务账户
    @apiParam (json body) {string} account.account_id 账户id
    @apiParam (json body) {string} account.account_type 账户类型(man配送线 shop发货线 staff职能线)
    @apiParam (json body) {string} client_id 风信账户id
    @apiParam (json body) {bool} full_resp 限制返回的格式

    @apiParamExample {json} 请求全部账户信息
    {
        "full_resp": false // 表示只返回全部的 client_id的列表
    }
    @apiSuccessExample {json} 成功示例
    HTTP/1.1 200 OK
    [
        "5c98403d518da2c5276109938fa4f545",
        "d9d85947fa053dc291646e0baccf023b",
        ...
    ]

    @apiParamExample {json} 请求全部账户信息
    {
        "full_resp": true // 表示返回全部的账户信息
    }
    @apiSuccessExample {json} 成功示例
    HTTP/1.1 200 OK
    [
        {
            "account_type": "man",
            "account_id": "56f1028b2d50c07c80914393",
            "client_id": "5c98403d518da2c5276109938fa4f545"
        },
        {
            "account_type": "man",
            "account_id": "56c2e7d97f4525452c8fc23c",
            "client_id": "17b878f081d5e3f699b63ef972ab1c6c"
        },
        ...
    ]

    @apiParamExample {json} 业务账户->client_id
    {
        "account": {
            "account_id":"56f1028b2d50c07c80914393",
            "account_type": "man"
        },
        "full_resp":true // 如果是 false, 返回的结构是[client_id, ...]
    }
    @apiSuccessExample {json} 成功返回
    [
        {
            "account_type": "man",
            "account_id": "56f1028b2d50c07c80914393",
            "client_id": "5c98403d518da2c5276109938fa4f545"
        }
    ]

    @apiParamExample {json} client_id->业务账户
    {
        "client_id": "5c98403d518da2c5276109938fa4f545"
    }
    @apiSuccessExample {json} 成功返回
    [
        {
            "account_type": "man",
            "account_id": "56f1028b2d50c07c80914393",
            "client_id": "5c98403d518da2c5276109938fa4f545"
        },
        ... // 可能会有多个(通常只有一个)
    ]

    """
    pass


def ACCOUNT_UPDATE():
    """

    """
    pass