# coding:utf-8
"""
给cha.123feng.com用的接口.
"""
from __future__ import unicode_literals

from apis.express import (redirect_get_express)
from tools_lib.gtornado.web2 import ReqHandler
from tornado import gen


class SingleExpress(ReqHandler):
    @gen.coroutine
    def get(self, number):
        """
        @api {GET} /express/cha/single/:expr_number cha.123feng.com查询运单信息
        @apiName cha_single
        @apiVersion 0.0.1
        @apiGroup cha_cha

        @apiParam (body param) {object} status 状态
        @apiParam (body param) {string} remark 备注
        @apiParam (body param) {string} update_time 更新时间
        @apiParam (body param) {array} trace 轨迹

        @apiSuccessExample {json} 返回示例
        {
            "status": {
                "status": "FINISHED",
                "sub_status": "FINISHED"
            },
            "remark": "例：下午5点30前送达",
            "update_time": "2016-06-16T21:06:22",
            "trace": [
                {
                    "event_source": "",
                    "number": "000000099348",
                    "to_status": "FINISHED",
                    "operator": {
                        "tel": "13245678901",
                        "id": "56c2e7d97f4525452c8fc23c",
                        "m_type": "parttime",
                       "name": "测试黄硬结"
                    },
                    "create_time": "2016-06-16T21:06:22",
                    "from_status": "DELAY",
                   "msg": "本人签收",
                    "event": "EVENT_TT",
                    "operating_loc": { // 操作当时的地理位置信息
                        "lat":
                        "lng":
                       "addr": "江南大道"
                    }
                }, ...
            ]
        }
        """
        # 丢给BL处理
        qs = {'only': 'status,remark,update_time,trace'}
        yield self.resp_redirect(redirect_get_express(number=number, **qs))
        # resp = resp_obj.content
        # if 'node' in resp:
        #     node_0 = resp['node']['node_0']
        #     node_n = resp['node']['node_n']
        #     node_0['tel'] = mask_tel(node_0['tel'])
        #     node_n['tel'] = mask_tel(node_n['tel'])
        #     filtered_node = {
        #         'node_0': {
        #             'name': node_0['name'],
        #             'tel': node_0['tel'],
        #             'addr': node_0['addr'],
        #         },
        #         'node_n': {
        #             'name': node_n['name'],
        #             'tel': node_n['tel'],
        #             'addr': node_n['addr'],
        #         }
        #     }
        #     resp['node'] = filtered_node
        #     self.resp(resp)
        # else:
        #     self.resp_not_found()
