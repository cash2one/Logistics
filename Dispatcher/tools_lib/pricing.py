#! /usr/bin/env python
# coding: utf-8

from math import ceil

# == 基础定价 ==
DEFAULT_CATEGORY = '标准件'
FH_BASE = 12
CATEGORIES = {
    # 常规件
    DEFAULT_CATEGORY: FH_BASE,
    '文件': 12,
    # 低温件
    '冻品（自带保温）': 12,
    '服饰': 12,
    # 易损件
    '水果': 12,
    '蔬菜': 12,
    '鲜花花盒': 24,
    '鲜花花束': 30,
    '生日蛋糕': 30,
    '特殊类目': 10,
    '水果特价': 8,
}


def fh_base():
    cont = [
        # # 常规件
        # {'category': '文件', 'fh_base': 12},
        # {'category': DEFAULT_CATEGORY, 'fh_base': FH_BASE},
        # # 低温件
        # {'category': '冻品（自带保温）', 'fh_base': 12},
        # {'category': '服饰', 'fh_base': 12},
        # # 易损件
        # {'category': '水果', 'fh_base': 12},
        # {'category': '蔬菜', 'fh_base': 12},
        # {'category': '鲜花花盒', 'fh_base': 24},
        # {'category': '鲜花花束', 'fh_base': 30},
        # {'category': '生日蛋糕', 'fh_base': 30},
        # {'category': '特殊类目', 'fh_base': 10},
    ]
    for cate in ('标准件', '文件', '冻品（自带保温）', '服饰', '水果', '蔬菜', '鲜花花盒', '鲜花花束', '生日蛋糕', '特殊类目', '水果特价'):
        base = CATEGORIES[cate]
        cont.append({'category': cate, 'fh_base': base})
    return cont


# == 加价 ==
def pricing(volume=0, weight=0.0):
    """
    获取溢价
    :param volume: 如果传入了体积, 优先按体积算
    :param weight:
    :return: (32.0 元, '17.5-18.5kg', 18.5)
    """
    # v_bps = [9000, 15000, 21000, 27000, 33000, 39000, 45000, 51000, 57000, 63000, 69000, 75000, 81000, 87000,
    #          93000, 99000, 105000, 111000]
    # w_bps = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5]
    # prices = [0, 1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 32]

    # 如果传入了体积, 优先按体积算
    if volume > 0:
        if volume <= 9000:
            return 0, '0kg - 1.5kg', 1.5
        elif 9000 < volume <= 15000:
            return 1, '1.5kg - 2.5kg', 2.5
        else:
            n = ceil((volume - 9000) / 6000.0)
    else:
        if weight <= 1.5:
            return 0, '0kg - 1.5kg', 1.5
        elif 1.5 < weight <= 2.5:
            return 1, '1.5kg - 2.5kg', 2.5
        else:
            n = ceil((weight - 1.5) / 1)

    # 总是换算成重量: n >= 1
    cash = 2 * (n - 1)
    msg = "%s - %skg" % (n + 0.5, n + 1.5)

    return cash, msg, n + 1.5


if __name__ == "__main__":
    print(('[default] cash=%.2d, msg=%s, %s' % pricing()))  # default weight=0
    print(('[1.5    ] cash=%.2d, msg=%s, %s' % pricing(weight=1.5)))
    print(('[2.5    ] cash=%.2d, msg=%s, %s' % pricing(weight=2.5)))
    print(('[3      ] cash=%.2d, msg=%s, %s' % pricing(weight=3)))
    print(('[4      ] cash=%.2d, msg=%s, %s' % pricing(weight=4)))
    print(('[4.5    ] cash=%.2d, msg=%s, %s' % pricing(weight=4.5)))
    print(('[18.5   ] cash=%.2d, msg=%s, %s' % pricing(weight=18.5)))

    print(('[8000   ] cash=%.2d, msg=%s, %s' % pricing(volume=8000)))
    print(('[13000  ] cash=%.2d, msg=%s, %s' % pricing(volume=13000)))
    print(('[20000, -3000] cash=%.2d, msg=%s, %s' % pricing(volume=20000, weight=-3000)))
    print(('[100 * 100 * 100] cash=%.2d, msg=%s, %s' % pricing(volume=100 * 100 * 100)))
    print(('[100 * 100 * 99] cash=%.2d, msg=%s, %s' % pricing(volume=100 * 100 * 99)))

    print()
    import json
    print((json.dumps(fh_base(), ensure_ascii=False, indent=2)))
