#coding=utf-8
__author__ = 'kk'


def request_prefix():
    """
    @apiDefine python_server_and_port_definition
    @apiParamExample {json} Python 服务 IP 以及端口
    {

        // develop
        IP: 外网123.57.45.209
            内网10.173.1.31
        Port: 9099

        // Production
        IP: 外网182.92.240.69
            内网10.171.103.109
        Port: http://{{IP}}:5000/port  // 通过这个接口获取访问端口, 返回内容就是端口

    }
    """
    pass
