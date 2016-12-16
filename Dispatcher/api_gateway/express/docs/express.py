# coding=utf-8
__author__ = 'kk'


def default_express_structure():
    """
    @apiDefine default_express
    @apiSuccessExample {json} 运单{express}
    {
        "status": {
            "status": "CREATED",
            "sub_status": "CREATED"
        },
        "third_party": {
            "order_id": "ibenben-28976975",
            "name": "PHH"
        },
        "update_time": "2016-03-01 00:30:03",
        "fee": {
            "fh": 4.0,
            "ps": 4.6
        },
        "node": {
            "node_n": {
                "tel": "135****1226",
                "name": "马某某",
                "fence": {
                    "id": "568d0fd8f10f5b15c1c983b2",
                    "name": "-西湖2   文二路"
                },
                "lat": 30.289431618,
                "msg": "",
                "lng": 120.1512401977,
                "addr": "文二路25号1幢4单元301室"
            },
            "node_0": {
                "lat": 0.0,
                "lng": 0.0,
                "tel": "",
                "name": "",
                "addr": ""
            }
        },
        "creator": {
            "tel": "4008700080",
            "id": 15081,
            "m_type": "",
            "name": "拼好货"
        },
        "remark": "",
        "number": "000000069227",
        "assignee": null,
        "create_time": "2016-03-01 00:30:03",
        "pkg_id": "",
        "times": {},
        "id": "570cbc16421aa9422e6b3a15"
    }

    """
    pass


def default_trace_structure():
    """
    @apiDefine default_trace
    @apiSuccessExample {json} 轨迹{trace}
    {
        "event_source": "PHH",
        "number": "000000074933",
        "to_status": "CANCEL",
        "msg": "发件人取消运单",
        "create_time": "2016-04-11 14:05:13",
        "from_status": "PAID",
        "operator": {
            "tel": "13245678901",
            "name": "测试虾饼"
        },
        "event": "EVENT_CANCEL"
    }
    """
    pass
