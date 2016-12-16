# coding:utf-8
from multiprocessing.dummy import Pool
from pymongo import MongoClient
from bson import ObjectId

PROD = '123.56.117.75'
DEV = '123.57.45.209'

mc_from = MongoClient(host=PROD, port=27017)['wholesale_ec']['charge_standard']
mc_to = MongoClient(host=PROD, port=27017)['profile']['shop']


def move_charge(charge_cursor):
    i = 0
    for c in charge_cursor:
        c_shop_id = c['shop'].get('shop_id')
        c_shop_name = c['shop'].get('name')
        ps = c['yuan_per_order']
        fh = c['yuan_per_order_cost']

        # 空shop_id不迁移
        if not c_shop_id:
            continue
        else:
            c_shop_id = ObjectId(c_shop_id)
        # 根据fee字段是否存在判断是否已经迁移
        if mc_to.find_one({'_id': c_shop_id, 'fee': {'$exists': True}}):
            print(u'定价[%s]已迁移.' % c['shop'].get('name'))
            continue

        i += 1
        result = mc_to.update_one({'_id': c_shop_id}, {'$set': {'fee': {'ps': ps, 'fh': fh}}})
        print('%s, %s, %s, ps:%s, fh:%s, %s, %s' % (i, c_shop_id, c_shop_name, ps, fh, result.matched_count, result.modified_count))


if __name__ == '__main__':
    pool = Pool(4)
    # ==> 迁移商户定价到shop的document内部
    e_cursor = mc_from.find({})
    pool.map(move_charge, [e_cursor])
