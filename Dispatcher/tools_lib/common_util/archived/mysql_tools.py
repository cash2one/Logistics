# coding:utf-8
# 提供一些适用于mysql数据库的工具函数

if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.join(os.getcwd(), os.pardir))

import mysql.connector
from tools_lib.host_info import *

DEBUG = True


# mysql 辅助函数
def dictfetchall(cursor):
    """
    Returns all rows from a cursor as a dict
    :param cursor:
    :return:
    """
    desc = cursor.description
    return [dict(list(zip([col[0] for col in desc], row))) for row in cursor.fetchall()]


def get_conn_from_old_db():
    """
    连接原master主库
    @return:
    """
    return Mysql()


def get_conn_from_db():
    """
    获取当前主库的连接
    """
    return Mysql()


class Mysql(object):
    """
    获取连接对象
    conn = Mysql.getConn()
    释放连接对象
    conn.close()
    """
    DB_Settings = {
        PROD_API_NODE: {
            "host": PROD_MYSQL_REDIS_INNER_IP,
            "port": 3306,
            "user": "fengservice",
            "password": "sk#u6j%n2x&w9ia",
            "charset": "utf8",
        },
        'default': {
            'host': DEV_OUTER_IP,
            'user': 'root',
            'password': 'admindev',
            'port': 3306,
            "charset": "utf8",
        },
    }

    def __init__(self, db_setting=None):
        self._conn = self.__get_conn(db_setting)
        self._cursor = self._conn.cursor(dictionary=True)

    @classmethod
    def get_db_settings(cls):
        node = CURRENT_NODE if CURRENT_NODE in cls.DB_Settings else 'default'
        return cls.DB_Settings[node]

    @classmethod
    def __get_conn(cls, db_setting=None):
        if db_setting is None:
            db_setting = cls.get_db_settings()
        return mysql.connector.connect(**db_setting)

    def get_all(self, sql, param=None):
        if DEBUG:
            print(sql)
            print(param)

        if param is None:
            self._cursor.execute(sql)
        else:
            self._cursor.execute(sql, param)
        result = self._cursor.fetchall()
        return result

    def get_one(self, sql, param=None, value_only=True):
        if DEBUG:
            print(sql)
            print(param)
        if param is None:
            self._cursor.execute(sql)
        else:
            self._cursor.execute(sql, param)
        rst = self._cursor.fetchone()
        if value_only:
            rst = list(rst.values())
            rst = rst[0] if len(rst) > 0 else None
        return rst

    def execute(self, sql, param=None):
        if DEBUG:
            print(sql)
            print(param)
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        return count

    def end(self, option='commit'):
        if option == 'commit':
            self._conn.commit()
        else:
            self._conn.rollback()

    def close(self, is_end=True):
        """
        释放连接池
        @param is_end:
        @return:
        """
        if is_end:
            self.end('commit')
        else:
            self.end('rollback')
        self._cursor.close()
        self._conn.close()


class Conn2Mysql(object):
    def __init__(self, old=False):
        """
        获取mysql连接
        @param old: 是否连接到原主库, 向前兼容
        @return:

        Usage:

            with Conn2Mysql() as cn:
                some code ....

        """
        self.cn = get_conn_from_db()

    def __enter__(self):
        return self.cn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cn.close(is_end=(exc_type is None))


if __name__ == '__main__':
    for i in range(10):
        with Conn2Mysql() as cn:
            print(cn.get_all("select shop_name, phone from f_shop.shop where id = %s", [15081]))
        with Conn2Mysql() as cn:
            print(cn.get_all("select shop_name, phone from f_shop.shop where id = %s", [17065]))
