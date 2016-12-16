# coding=utf-8
import json
from logging import warn

from models.fence import Fence
from pymongo.errors import OperationFailure
from schema import Schema, Optional, Use, And

from tools_lib.gmongoengine.paginator import paginator
from tools_lib.gtornado.escape import schema_utf8
from tools_lib.gtornado.http_code import HTTP_201_CREATED
from tools_lib.gtornado.web import BaseRequestHandler as BRH


class BaseRequestHandler(BRH):
    def __init__(self, *args, **kwargs):
        super(BaseRequestHandler, self).__init__(*args, **kwargs)

        self.set_header("Access-Control-Allow-Origin", "*")

    def options(self, *args, **kwargs):
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, PATCH, DELETE")
        self.set_header("Access-Control-Allow-Headers",
                        "X-Requested-With,Accept,Content-Type, Origin, Authorization, X-File-Name")
        self.finish("GET,POST,PUT,PATCH,DELETE")


class FenceHandler(BaseRequestHandler):
    """
    栅栏增删查改
    """

    def get(self):
        try:
            data = self.get_query_args()
            data = Schema({
                Optional('page', default=1): Use(int),
                Optional('count', default=100): Use(int),
                Optional('limit', default=True): And(Use(int), Use(bool)),
            }).validate(data)
            page = data['page']
            count = data['count']
            limit = data['limit']
        except:
            self.write_parse_args_failed_response()
            return
        objs = Fence.objects.all()
        warn(objs)
        amount, mission_list = paginator(objs, page, count, limit)
        self.set_X_Resource_Count(amount)
        self.write_response([i.format_response() for i in mission_list])

    def post(self):
        try:
            data = json.loads(self.request.body)
            data = Schema({
                'points': list,
                Optional('name'): schema_utf8,
                Optional('loc'): schema_utf8,
                Optional('color'): schema_utf8,
                Optional('manager'): dict,
            }).validate(data)
        except:
            self.write_parse_args_failed_response()
            return
        fence = Fence(**data).save()

        self.write_response(fence.format_response(), status_code=HTTP_201_CREATED)


class OneFenceHandler(BaseRequestHandler):
    """
    一个栅栏增删查改
    """

    def get(self, fence_id):

        obj = Fence.objects(id=fence_id).first()
        if not obj:
            self.write_not_found_entity_response()
            return
        self.write_response(obj.format_response())

    def patch(self, fence_id):
        try:
            data = json.loads(self.request.body)
            data = Schema({
                Optional('points'): list,
                Optional('name'): schema_utf8,
                Optional('loc'): dict,
                Optional('color'): schema_utf8,
                Optional('manager'): dict,
            }).validate(data)
        except:
            self.write_parse_args_failed_response()
            return

        fence = Fence.objects(id=fence_id).first()
        if not fence:
            self.write_not_found_entity_response()
            return

        for field in data:
            value = data[field]
            fence[field] = value

        fence.save()
        fence.reload()
        self.write_response(fence.format_response(), status_code=HTTP_201_CREATED)

    def delete(self, fence_id):
        fence = Fence.objects(id=fence_id).first()
        if not fence:
            self.write_not_found_entity_response()
            return

        fence.delete()
        self.write_no_content_response()


class FencePointCompareHandler(BaseRequestHandler):
    def post(self):
        """
        @api {post} /schedule/logic/fence/point_cmp 寻找该点落入的栅栏
        @apiName PointCompare
        @apiGroup LOGIC_NETWORK_FENCE
        @apiDescription 查找点落入的栅栏
        @apiVersion 0.1.0

        @apiParam (BODY PARAMETERS) {array} point 点

        """
        try:
            data = json.loads(self.request.body)
            point = data["point"]
        except:
            self.write_parse_args_failed_response()
            return
        p = point
        try:
            r = [i.format_response() for i in Fence.objects(points__geo_intersects=p)]
            self.write_response(r)
        except OperationFailure:
            msg = "BadValue: longitude/latitude%s is out of bounds or invalid." % data["point"]
            warn(msg)
            self.write_error_response(message=msg)


class IfInsideFenceHandler(BaseRequestHandler):
    def post(self):
        """
        @api {post} /schedule/logic/fence/inout 判断这些点中在栅栏内的
        @apiName IfPointInsideFence
        @apiGroup LOGIC_NETWORK_FENCE
        @apiDescription 查找点落入的栅栏
        @apiVersion 0.1.0

        @apiParam (BODY PARAMETERS) {array} point_list 点经纬度列表


        @apiSuccessExample Success-Response
            HTTP/1.1 200
            {
                "message": "",
                "error_code": 0,
                "content": {
                    "in": [[123,321], ...] // 在任何一个栅栏内部的点列表
                    "out": [[132,312], ...] // 不在任何一个栅栏内部的点列表
                }
            }
        """
        try:
            data = json.loads(self.request.body)
            points = data["point_list"]
        except:
            self.write_parse_args_failed_response()
            return
        ret = {
            "in": [],
            "out": []
        }
        for p in points:
            if Fence.objects(points__geo_intersects=p).first():
                ret["in"].append(p)
            else:
                ret["out"].append(p)
        ret["in"], ret["out"] = list(ret["in"]), list(ret["out"])
        self.write_response(ret)


class FenceManagerFilter(BaseRequestHandler):
    def post(self):
        """
        传入一些坐标,然后给出这些坐标落入的fence的全部manager
        """
        try:
            data = json.loads(self.request.body)
            locs = data["locs"]
        except:
            self.write_error_response("bad json", status_code=400)
            return
        fence_ids = []
        for i in locs:
            fence_ids.extend([
                                 str(i) for i in Fence.objects(points__geo_intersects=[i["lng"], i["lat"]]).scalar("id")
                                 ])

        fence_ids = list(set(fence_ids))
        self.write_response([
                                {
                                    "tel": i.manager.get("tel", None),
                                    "name": i.manager.get("name", None),
                                    "id": str(i.manager.get("id", None))
                                }
                                for i in Fence.objects(pk__in=fence_ids) if i])
