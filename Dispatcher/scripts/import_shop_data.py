# coding:utf-8
from __future__ import unicode_literals
from pymongo import MongoClient
from mysql.connector import connect


def ifnull(s, default=''):
    return default if s is None else s


if __name__ == '__main__':
    cnx = connect(host='182.92.166.43', port=3307, user='fengdevelop', password='dk@s3h%y7tr#c0z', charset='utf8')
    cursor = cnx.cursor(dictionary=True)

    # shop_ids = [12988, 12382, 11077, 12823, 10377, 15081, 2397]
    shop_ids = [17065, 17066]
    sql = 'select s.*, o.tel ' \
          'from f_shop.shop s ' \
          'inner join f_shop.shop_owner o on s.shop_owner_id = o.id ' \
          'where s.id in (%s)' % ','.join(['%s'] * len(shop_ids))
    print(sql)
    cursor.execute(sql, shop_ids)

    mc = MongoClient(host='123.56.117.75', port=27017)['profile']['shop']

    # 清理旧数据
    mc.delete_many({
        'deprecated.id': {
            '$in': shop_ids
        }
    })
    new_shop_records = [{
                            'tel': record['tel'],
                            'password': record['password'],
                            'name': record['shop_name'],
                            'avatar': record['avatar'],
                            'status': 'STATUS_INIT',
                            'create_time': record['create_time'],
                            'accounts': [],
                            'loc': {
                                'province': record['province'],
                                'province_code': record['province_code'],
                                'district': record['district'],
                                'city': record['city'],
                                'address': ifnull(record['address']),
                                'street_code': record['street_code'],
                                'longitude': record['longitude'],
                                'street': record['street'],
                                'district_code': record['district_code'],
                                'latitude': record['latitude'],
                                'city_code': record['city_code']
                            },
                            'deprecated': {
                                'shop_creator_id': record['shop_creator_id'],
                                'shop_owner_id': record['shop_owner_id'],
                                'shop_owner_tel': ifnull(record['shop_owner_tel']),
                                'phone': ifnull(record['phone']),
                                'shop_owner_name': ifnull(record['shop_owner_name']),
                                'type': ifnull(record['type']),
                                'id': record['id'],
                            },
                        } for record in cursor]

    mc.insert_many(new_shop_records)

    cnx.close()
