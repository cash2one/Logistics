#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-02-14 15:19:48
# @Author  : Jim Zhang (jim.zoumo@gmail.com)
# @Github  : https://github.com/zoumo
import sys

from tornado import gen

from tools_lib.gtornado.http_code import HTTP_200_OK
from tools_lib.gtornado.web import BaseRequestHandler
from tools_lib.host_info import IP_API, BL_DAS_PORT

reload(sys)
sys.setdefaultencoding("utf-8")

das_url = "http://%s:%s" % (IP_API, BL_DAS_PORT)


class AppHandler(BaseRequestHandler):
    @gen.coroutine
    def get(self):
        """
        @api {get} /apps 应用中心 - 获取所有的版本
        @apiVersion 0.0.1
        @apiName app_all_version
        @apiGroup fe_apps

        @apiParam (Query Parameters) {String} platform 手机平台类型, android, ios
        @apiParam (Query Parameters) {String} app_name 应用名字

        @apiSuccessExample 成功返回示例
            HTTP/1.1 200 OK
            body:
            {
              "content": [
                  {
                    "changelog": "新版本",
                    "create_time": "2016-02-14T06:27:04Z",
                    "download_times": 2,
                    "app_name": "fh",
                    "platform": "android",
                    "version": 91,
                    "link": "http://mrwind.qiniudn.com/windthunder-75.apk",
                    "release_time": "2016-02-14T06:27:04Z",
                    "id": "56c01e39421aa9c0ea8d7bbd"
                  },
                 {
                    "changelog": "新版本",
                    "create_time": "2016-02-14T06:27:04Z",
                    "download_times": 2,
                    "app_name": "fh",
                    "platform": "android",
                    "version": 90,
                    "link": "http://mrwind.qiniudn.com/windthunder-75.apk",
                    "release_time": "2016-02-14T06:27:04Z",
                    "id": "56c01e39421aa9c0ea8d7bbd"
                  },
                  ...
              ],
              "message": "",
              "error_code": 0
            }

        @apiUse ClientError
        """
        yield self.redirect_get(das_url + '/apps', self.get_query_args())

    @gen.coroutine
    def delete(self):
        """
        @api {delete} /apps 应用中心 - 删除对应版本
        @apiVersion 0.0.1
        @apiName app_delete
        @apiGroup fe_apps

        @apiParam (Query Parameters) {String} platform 手机平台类型, android, ios
        @apiParam (Query Parameters) {String} app_name 应用名字
        @apiParam (Query Parameters) {Integer} version 版本号

        @apiSuccessExample 成功返回示例
            HTTP/1.1 204 NO CONTENT
        @apiUse ClientError
        @apiUse NotFoundEntityError
        """
        yield self.redirect_delete(das_url + '/apps', self.get_query_args())


class VersionHandler(BaseRequestHandler):
    @gen.coroutine
    def get(self):
        """
        @api {get} /apps/version 应用中心 - 获取最新版本号
        @apiVersion 0.0.1
        @apiName app_version
        @apiGroup app_apps

        @apiParam (Query Parameters) {String} platform 手机平台类型, android, ios
        @apiParam (Query Parameters) {String} app_name 应用名字

        @apiSuccessExample 成功返回示例
            HTTP/1.1 200 OK
            body:
            {
              "content": {
                "changelog": "新版本",
                "create_time": "2016-02-14T06:27:04Z",
                "download_times": 2,
                "app_name": "fh",
                "platform": "android",
                "version": 90,
                "link": "http://mrwind.qiniudn.com/windthunder-75.apk",
                "release_time": "2016-02-14T06:27:04Z",
                "id": "56c01e39421aa9c0ea8d7bbd"
              },
              "message": "",
              "error_code": 0
            }

        @apiUse ClientError
        @apiUse NotFoundEntityError
        """
        yield self.redirect_get(das_url + '/apps/version', self.get_query_args())


class DownloadHandler(BaseRequestHandler):
    @gen.coroutine
    def get(self):
        """
        @api {get} /apps/download 应用中心 - 下载更新
        @apiVersion 0.0.1
        @apiName app_download
        @apiGroup app_apps

        @apiParam (Query Parameters) {String} platform 手机平台类型, android, ios
        @apiParam (Query Parameters) {String} app_name 应用名字
        @apiParam (Query Parameters) {Integer} version 应用版本号

        @apiSuccessExample 成功返回示例
            HTTP/1.1 302
            header:
            {
                "Location": "http://mrwind.qiniudn.com/windthunder-75.apk"
            }

        @apiUse ClientError
        @apiUse NotFoundEntityError
        """
        # url = url_concat(das_url + '/apps/download', self.get_query_args())
        response = yield self.redirect_get(das_url + '/apps/download', self.get_query_args())
        if response.code == HTTP_200_OK:
            self.clear()
            link = response.content
            self.redirect(link)


class ReleaseHandler(BaseRequestHandler):
    @gen.coroutine
    def post(self):
        """
        @api {post} /apps/release 应用中心 - 发布新版本
        @apiVersion 0.0.1
        @apiName fe_app_release
        @apiGroup fe_apps

        @apiParam (Body Parameters) {String} platform 手机平台类型, android, ios
        @apiParam (Body Parameters) {String} app_name 应用名字
        众包配送员: parttime
        仓库管理: warehouse
        城际司机: city_driver
        干线司机: trunk_driver
        直送司机: direct_driver
        众包司机: parttime_driver
        区域经理: area_manager
        取货点负责人: point_manager
        @apiParam (Body Parameters) {Integer} version 版本号
        @apiParam (Body Parameters) {String} link 安装包下载链接
        @apiParam (Body Parameters) {String} changelog 更新日志
        @apiParam (Body Parameters) {String} [release_time] 生效日期

        @apiSuccessExample 成功返回示例
            HTTP/1.1 201 CREATED
            body:
            {
              "content": {
                "changelog": "新版本",
                "create_time": "2016-02-14T06:27:04Z",
                "download_times": 2,
                "app_name": "fh",
                "platform": "android",
                "version": 90,
                "link": "http://mrwind.qiniudn.com/windthunder-75.apk",
                "release_time": "2016-02-14T06:27:04Z",
                "id": "56c01e39421aa9c0ea8d7bbd"
              },
              "message": "",
              "error_code": 0
            }

        @apiUse ClientError
        @apiUse DuplicateEntryError
        """
        yield self.redirect_post(das_url + '/apps/release', body=self.request.body)

    @gen.coroutine
    def put(self):
        """
        @api {put} /apps/release 应用中心 - 修改发布版本的信息
        @apiVersion 0.0.1
        @apiName fe_app_release
        @apiGroup fe_apps

        @apiParam (Body Parameters) {String} platform 手机平台类型, android, ios
        @apiParam (Body Parameters) {String} app_name 应用名字
        众包配送员: parttime
        仓库管理: warehouse
        城际司机: city_driver
        干线司机: trunk_driver
        直送司机: direct_driver
        众包司机: parttime_driver
        区域经理: area_manager
        取货点负责人: point_manager
        @apiParam (Body Parameters) {Integer} version 版本号
        @apiParam (Body Parameters) {String} link 安装包下载链接
        @apiParam (Body Parameters) {String} changelog 更新日志
        @apiParam (Body Parameters) {String} [release_time] 生效日期

        @apiSuccessExample 成功返回示例
            HTTP/1.1 201 CREATED
            body:
            {
              "content": {
                "changelog": "新版本",
                "create_time": "2016-02-14T06:27:04Z",
                "download_times": 2,
                "app_name": "fh",
                "platform": "android",
                "version": 90,
                "link": "http://mrwind.qiniudn.com/windthunder-75.apk",
                "release_time": "2016-02-14T06:27:04Z",
                "id": "56c01e39421aa9c0ea8d7bbd"
              },
              "message": "",
              "error_code": 0
            }

        @apiUse ClientError
        @apiUse DuplicateEntryError
        """
        yield self.redirect_put(das_url + '/apps/release', body=self.request.body)


class TimeHandler(BaseRequestHandler):
    @gen.coroutine
    def get(self):
        """
            @api {get} /apps/time/now 应用中心 - 获取当前服务器时间
            @apiVersion 0.0.1
            @apiName app_time_now
            @apiGroup app_apps


            @apiSuccessExample 成功返回示例
                HTTP/1.1 200 OK
                body:
                {
                  "content": "2016-03-30T00:00:00Z",
                  "message": "",
                  "error_code": 0
                }

        """
        yield self.redirect_get(das_url + '/apps/time/now')

# class ChargeHandler(BaseRequestHandler):
#     def post(self):
#         data = json.loads(self.request.body)
#         logging.info(data)
#         self.write_response(status_code=201)
#
#
# class CreateChargeHandler(BaseRequestHandler):
#     def post(self):
#         self.set_header("Access-Control-Allow-Origin", "*")
#         self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
#         self.set_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
#         import pingpp
#         data = json.loads(self.request.body)
#         # logging.info(data)
#         logging.info(self.request)
#         client_ip = self.request.remote_ip
#         pingpp.api_key = 'sk_test_1inzPSL8yXzTL0aXz5yHq9a1'
#         ch = pingpp.Charge.create(
#             order_no='no1',
#             amount=1,
#             app=dict(id='app_OG88400CGOqHzb14'),
#             channel='alipay_pc_direct',
#             currency='cny',
#             client_ip=client_ip,
#             subject='Your Subject',
#             body='Your Body',
#             extra={
#                 "success_url": "http://127.0.0.1:5000/apps/charge",
#             },
#             # **data
#         )
#         logging.info(ch)
#         self.write_response(content=ch, status_code=201)
