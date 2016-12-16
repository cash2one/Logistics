## Usage

最新的更新在`master`分支.请clone该分支进行开发.

## Directory Layout

    MrWind_Dispatcher/       --> all of the files to be used in production
	  api_gateway/           --> api网关
	    uwsgi_apis/
	    tornado_apis/
	    ...
      business_logic/        --> 业务逻辑api(可向下调用data_and_service接口)
	    A_service/           --> 可以有自己的cache、DB。
	    B_service/           --> 可以有自己的cache、DB。
	    ...
	  data_and_service/      --> 业务逻辑api(只操作自己的数据,不调用项目内部接口)
        token/               --> token服务
        ...
      tools_lib/             --> 公用服务
        gps/        	     --> 地理位置信息服务
        sms-*/    		     --> 短信/IM推送服务
        logging/      	     --> 日志服务
      scripts/               --> handy shell/py/... scripts