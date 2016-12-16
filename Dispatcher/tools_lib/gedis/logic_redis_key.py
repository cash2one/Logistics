# -*- coding:utf-8 -*-
__author__ = 'Qian Lei'


# 公司内部员工信息缓存（数据源:node.js服务）
key_staff_info = "mrwind_inc_staff_info:{user_id}"

# 配送员简要信息
key_deliver_info = "DELIVER:INFO:{user_id}"

# 配送员邀请商户的邀请码
key_staff_invite_shop_code = "staff:{id}:invite_shop_code:{code}"
# 商户邀请商户的邀请码
key_shop_invite_shop_code = "shop:{id}:invite_shop_code:{code}"

# 商户某月累计奖励金额
key_shop_invite_reward = "mall:shop:{shop_id}:invite_shop_reward:{year}:{month}"
# 商户某日是否已有过邀请奖励
key_shop_invite_reward_flag = "mall:shop:{shop_id}:invite_shop_reward:{year}:{month}:{day}:flag"

# 预约驻派, 商户保证金
key_shop_deposit = "shop:{shop_id}:deposit"

# 拼好货日数据
key_PHH_data = "data:PHH:{year}:{month}:{day}"
# F2鲜果配送
key_F2_data = "data:F2:{year}:{month}:{day}"
