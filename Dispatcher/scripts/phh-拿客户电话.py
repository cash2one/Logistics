# encoding=utf-8
import re
import requests
from pymongo import MongoClient
from tools_lib.transwarp.tz import utc_8_to_utc, n_days_before


def get_customer_info_from_tn(tn):
    ret = None
    url = "http://express.yqphh.com/login"
    payload = {'username': 'fxs1', 'password': 'i6l01v', 'return_url': '', 'act': 'signin'}
    with requests.session() as s:
        # fetch the login page
        s.get(url)
        # print(s.cookies)

        # post to the login form
        s.post(url, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        # print(s.cookies)

        # url2 = 'http://express.yqphh.com/shipmentDetail?tracking_number=000000064513'
        url2 = 'http://express.yqphh.com/shipmentDetail?tracking_number=%s' % tn
        r = s.get(url2)
        # print(r.text)
        raw = r.text

    # raw = """
    # 	            <tbody>
    # 	                <tr>
    # 	                	<td>000000064513</td>
    # 	                	<td>风先生</td>
    # 	                    <td>朱琴琴</td>
    # 	                    <td>13738229699</td>
    # 	                    <td>浙江</td>
    # 	                    <td>杭州</td>
    # 	                    <td>拱墅区</td>
    # 	                    <td>定海西园21幢1单元303</td>
    # 	                </tr>
    # 	            </tbody>
    # """
    raw = ''.join(raw.split())
    m = re.search(r"(?<=<tbody><tr>)(.*)(?=</tr></tbody>)", raw)
    if not m:
        return ret
    tbody = m.group(0)
    # print tbody
    m = re.findall(r"(?<=<td>)(.*?)(?=</td>)", tbody)
    for i in range(len(m)):
        item = m[i]
        # 跳过“风先生”这栏信息
        if i == 1:
            continue
        else:
            ret = str(item) if not ret else "%s,%s" % (ret, item)
    print(ret)
    return ret


if __name__ == '__main__':
    # 从mongodb取出到现在48H内的expr_num
    mc = MongoClient(host='123.56.117.75', port=27017)['wholesale_ec']['express']
    result = mc.find(
        {"create_time": {"$gte": n_days_before(2, ret="datetime")}, "shop.is_test": False},
        {"receiver.name": 1, "receiver.tel": 1, "expr_num": 1, "create_time": 1})
    i, N = 0, 20
    out = []
    for doc in result:
        # todo: 根据expr_num找客户电话.
        # get_customer_info_from_tn('000000073264')
        # s = 59675
        # e = 75035
        # i, N = 0, 20
        # for tn in xrange(s, e + 1):
        # tn = '%012d' % tn
        tn = doc['expr_num']
        line = get_customer_info_from_tn(tn)
        if not line:
            continue
        line = "%s\n" % line
        out.append(line.encode('utf-8'))
        i += 1
        print((i, doc['expr_num']))
        # 每N个输出到文件
        if i % N == 0:
            with open("customer.csv", 'a+') as f:
                f.writelines(out[(i / N - 1) * N:i])
