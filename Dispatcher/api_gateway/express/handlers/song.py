# coding:utf-8
"""
给song.123feng.com用的接口.
"""
import logging

from .apis import express
from .apis import node
from .apis.express import redirect_get_express, redirect_query_express
from schema import Schema, Optional, SchemaError
from tools_lib.bl_expr import ExprState
from tools_lib.common_util import xls
from tools_lib.common_util.archived.gtz import TimeZone
from tools_lib.gtornado import baidumap_api
from tools_lib.gtornado.escape import (schema_utf8, schema_utf8_empty, schema_float)
from tools_lib.gtornado.web2 import ShopHandler, ReqHandler
from tornado import gen


# 前端 聚合查询
class AggregationNode(ShopHandler):
    @gen.coroutine
    def get(self):
        pass


# 根据pkg_id, node_id展开运单列表
class Express(ShopHandler):
    @gen.coroutine
    def get(self):
        # 丢给BL处理
        qs = self.get_query_args()
        qs.update({
            "creator_id": self.shop_info["id"]
        })
        yield self.resp_redirect(redirect_query_express(**qs))

    @gen.coroutine
    def post(self):
        # 批量填单发货
        # if self.shop_info["status"] not in ("STATUS_INFO_YES", "STATUS_VALID"):
        #     self.resp_forbidden("商户审核未通过,不允许下单")
        #     return

        try:
            data = self.get_body_args()
            data = Schema([
                {
                    "address": schema_utf8,
                    "name": schema_utf8,
                    "tel": schema_utf8,
                    "lat": schema_float,
                    "lng": schema_float,
                    Optional("remark", default=""): schema_utf8_empty
                }
            ]).validate(data)
        except SchemaError:
            self.resp_error("请将信息填写完整")
            return
        # 先计算下商户位置所在围栏 todo: 围栏稳定情况下,可以cache商户所在围栏信息
        shop_fence = yield node.query_fence_point_within([self.shop_info['lng'], self.shop_info['lat']])
        # 给每一单填信息
        exprs_to_create = []
        for i in data:
            if not i["lng"] or not i["lat"]:
                # 如果前端传来的经纬度为空则尝试再获取一下
                i["lng"], i["lat"] = yield baidumap_api.async_get_coordinates("", "", i["address"])

            the_fence = yield node.query_fence_point_within([i["lng"], i["lat"]])
            exprs_to_create.append({
                "remark": i["remark"],
                "node": {
                    # 寄方地址 todo: 暂时用商户地址
                    "node_0": {
                        "name": self.shop_info['name'],
                        "tel": self.shop_info['contact_tel'],
                        "addr": self.shop_info['address'],
                        "lng": self.shop_info['lng'],
                        "lat": self.shop_info['lat'],
                        "fence": shop_fence
                    },
                    "node_n": {  # 送达地址
                        "addr": i["address"],
                        "name": i["name"],
                        "tel": i["tel"],
                        "lng": i["lng"],
                        "lat": i["lat"],
                        "fence": the_fence
                    }
                },
                "fee": {}
            })
        creator_info = {
            "id": self.shop_info["id"],
            "name": self.shop_info.get("name", ""),
            "tel": self.shop_info["tel"],
            "m_type": self.get_app_name(),
            "lat": self.shop_info['lat'],
            "lng": self.shop_info['lng']
        }
        yield self.resp_redirect(express.redirect_bulk_create_express(
            creator=creator_info,
            expr_list=exprs_to_create,
            pay=False
        ))


class SingleExpress(ShopHandler):
    @gen.coroutine
    def get(self, number):
        # 丢给BL处理
        qs = self.get_query_args()
        yield self.resp_redirect(redirect_get_express(number=number, **qs))

    @gen.coroutine
    def delete(self, number):
        """
        取消运单
        """
        data = self.get_body_args()
        yield self.resp_redirect(express.redirect_perform_expr_event(
            number,
            operation=ExprState.EVENT_CANCEL,
            operator=self.shop_info,
            msg=data.get("msg", "")
        ))


class ExportHandler(ReqHandler):
    @gen.coroutine
    def get(self):
        """
        导出运单
        """
        try:
            data = self.get_query_args()
            creator_id = data["shop_id"]
            start_time = TimeZone.str_to_datetime(data["start_time"])
            end_time = TimeZone.str_to_datetime(data["end_time"])
        except:
            self.resp_error("参数错误")
            return
        yield self.resp_redirect(express.redirect_song_export_express(
            creator_id,
            start_time=start_time,
            end_time=end_time
        ))


class ExcelParseHandler(ShopHandler):
    def post(self):
        """
        上传xls然后读取运单信息返回
        """
        express_data = self.request.files.get('express_excel')
        if not express_data:
            self.resp_error("读取Excel文档失败.")
            return
        express_data = express_data[0]["body"]
        xls_data = xls.xls_reader(express_data)
        data_to_resp = []
        # 序号    第三方单号             收货人     联系电话         收货地址               备注
        # 例：1   DSFDH-123123123123   黄小姐     15878856779     滨江区星耀城2号楼201    12点以前送达
        for row in xls_data[2:]:
            # 从第三行开始parse
            try:
                third_party_order_id = row[1]
                node_n_name = row[2]
                node_n_tel = row[3]
                node_n_addr = row[4]
                remark = row[5]
                if not (node_n_name and node_n_tel and node_n_addr):
                    continue
            except Exception as e:
                logging.error(e.message)
                continue

            data_to_resp.append({
                "source_order_id": third_party_order_id,
                "receiver": {
                    "name": node_n_name,
                    "tel": node_n_tel,
                    "address": node_n_addr,
                },
                "remark": remark
            })
        self.resp({"express": data_to_resp})


class GeoLocationHandler(ShopHandler):
    @gen.coroutine
    def get(self):
        data = self.get_schema()
        if not data: return

        # 根据地址解析经纬度
        lng, lat = yield baidumap_api.async_get_coordinates(
            city=data.get('city', None),
            district=data.get('district'),
            address=data['street']
        )
        if not (lng and lat):
            logging.error("经纬度解析错误")
            self.resp_error("经纬度解析错误, 请稍后再试")
            return
        # 根据经纬度解析具体详细地址
        location = yield baidumap_api.async_get_reverse_location(lng=lng, lat=lat)
        self.resp({"content": location})
        return

    def get_schema(self):
        try:
            data = Schema({
                Optional("city"): schema_utf8,
                Optional("district"): schema_utf8,
                "street": schema_utf8
            }).validate(self.get_query_args())
        except Exception as e:
            logging.error(e)
            self.resp_error(e.message)
            return False
        else:
            return data


class AggregationStatusHandler(ShopHandler):
    @gen.coroutine
    def get(self):
        """
        @api {GET} /express/song/aggregation/status 网页发货端 - 数据页面
        @apiName fe_song_express_aggregation_status
        @apiGroup fe_song
        @apiVersion 0.0.1

        @apiParam (query param) {string} [term] 模糊查询的值
        @apiParam (query param) {string} [term_keys=number] 需要模糊查询的字段, 逗号分隔
        @apiParam (query param) {string} [pkg_id] 包裹id
        @apiParam (query param) {string} [status] 大分类状态
        @apiParam (query param) {string} [sub_status] 细分类的状态
        @apiParam (query param) {string} [time_type=create_time] 需要限制的时间类型
        @apiParam (query param) {string} [start_time] 开始时间
        @apiParam (query param) {string} [end_time] 结束时间
        @apiParam (query param) {string} [assignee_id] 当前运单负责人id
        @apiParam (query param) {string} [assignee_type] 当前运单负责人类型
        @apiParam (query param) {string} [fence_id] 围栏id
        @apiParam (query param) {string} [fence_name] 围栏名称

        @apiSuccessExample {json} 成功返回例子

        {
            "status": {
                "SENDING": 2,
                "FINISHED": 1,
                "CREATED": 0
            },
            "sub_status": {
                "SENDING": 1,
                "REFUSE": 0,
                "CREATED": 0,
                "VALIDATING": 1,
                "DELAY": 1,
                "WAREHOUSE": 0,
                "FINISHED": 1,
                "VALID": 0,
                "CANCEL": 0,
                "TRASH": 0,
                "NO_CASH": 0
            }
        }

        """
        param = self.get_query_args()
        param.update({
            "creator_id": self.shop_info['id']
        })
        yield self.resp_redirect(express.redirect_aggregation_status(param))
