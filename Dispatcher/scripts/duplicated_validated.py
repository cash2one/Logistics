#!/usr/bin/env python
# coding:utf-8
from mysql.connector import connect

if __name__ == '__main__':
    cnx = connect(host='182.92.166.43', port=3307, user='fengdevelop', password='dk@s3h%y7tr#c0z', charset='utf8')
    cursor = cnx.cursor(dictionary=True)

    sql = 'SELECT man_id, tel, expr_num, create_time FROM f_deliveryman.flow WHERE TYPE=\'VALIDATED\';'
    print(sql)
    cursor.execute(sql)

    i = 0
    l = list()
    e = set()
    dup = {}
    for record in cursor:
        # print i, record['expr_num']
        num = record['expr_num']
        if num in e:
            dup[num] = dup[num] + 1 if num in dup else 2
        e.add(num)

    for k in dup:
        i += 1
        print((i, k, dup[k]))