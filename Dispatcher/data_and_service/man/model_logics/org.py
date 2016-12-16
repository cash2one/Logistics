# # encoding: utf-8
# import re
# import logging
# from tools_lib.transwarp.tz import utc_8_now, utc_now
# from tools_lib.transwarp import db
# from models import DeliverymanOrg
#
#
# class DeliverymanOrgLogic(object):
#     """
#     Model logic for org.
#     """
#
#     """>>>Begin DB functions"""
#
#     @staticmethod
#     @db.with_transaction
#     def create(**kw):
#         # 检查deliveryman_id, 如果存在record且该record的deleted为RECORD_NORMAL, 不允许添加
#         sanity_check = DeliverymanOrgLogic.find_by('sn', 'where sn=?', '', kw['sn'])
#         if sanity_check:
#             raise ValueError("Already exist record with sn=[%s]." % kw['sn'])
#         now = utc_8_now()
#         kw['update_time'] = now
#         org = DeliverymanOrg(**kw)
#         org.insert()
#         # TODO 同步旧db
#
#         deliver_org = dict(
#             user_id=kw['deliveryman_id'],
#             user_num='',
#             level=0,
#             level_parent=0,
#             team_name=kw.get('team_name', ""),
#             flag=0,
#             create_time=utc_now(),
#             update_time=utc_now(),
#             deleted=0
#         )
#         # db.update()
#
#     @staticmethod
#     @db.with_transaction
#     def remove(kn, kv):
#         # 参数合法性检查. 如果不合法,直接报错.
#         DeliverymanOrgLogic.is_valid_kn_kv(kn, kv)
#         # 获取想要删除的记录
#         org = DeliverymanOrg.get(key_name=kn, key_value=kv)
#         # 如果根据kn,kv找不到这条记录,报错
#         if not org:
#             raise AttributeError("Could not find in org with [%s]=[%s]. So could not mark it deleted, either."
#                                  % (kn, kv))
#         # 如果是最小节点,删除它.
#         if org.level == 2:
#             org.delete()
#         # 虽然是上部节点,但是底下没有有效人员, 删除它.
#         else:
#             sn_regex = org.sn[:3 * (8 - org.level)] + '...' * (org.level - 2)
#             ids = DeliverymanOrg.find_by('id', 'where sn REGEXP BINARY ? AND deliveryman_id!=0', '', sn_regex)
#             if len(ids) > 0:
#                 raise ValueError("Could not delete org with [%s]=[%s], it has men inside." % (kn, kv))
#             else:
#                 for i in xrange(0, len(ids), 100):
#                     id_list = ids[i: i + 100]
#                     db.update('DELETE FROM org WHERE id IN (%s)' % ','.join(id_list))
#                     # TODO 同步旧db
#
#     @staticmethod
#     def bind_unbind(sn, deliveryman_id):
#         # 参数合法性检查. 如果不合法,直接报错.
#         DeliverymanOrgLogic.is_valid_kn_kv("deliveryman_id", deliveryman_id)
#         DeliverymanOrgLogic.is_valid_kn_kv("sn", sn)
#         # 获取想要的记录
#         org = DeliverymanOrg.get("sn", sn)
#         # 如果根据kn,kv找不到这条org记录,报错
#         if not org:
#             raise AttributeError("Could not find in org with [sn]=[%s]. So could not unbind it, either."
#                                  % sn)
#         if deliveryman_id == 0:
#             # 如果已经是untie过,直接返回.
#             if org.deliveryman_id == 0:
#                 return "Already an untied record in org with [sn]=[%s]." % sn
#             # 找到这条记录并且它的deliveryman_id还未被设置过, update这条记录.
#             org.deliveryman_id = 0
#         else:
#             # 想要绑定
#             org.deliveryman_id = deliveryman_id
#             logging.info("Binding [sn]=[%s] with [deliveryman_id]=[%s]." % (sn, deliveryman_id))
#         org.update_time = utc_8_now()
#         org.update()
#         # TODO 同步旧db
#
#     @staticmethod
#     def get(kn, kv):
#         # 参数合法性检查. 如果不合法,直接报错.
#         DeliverymanOrgLogic.is_valid_kn_kv(kn, kv)
#         # 获取想要的记录并返回
#         return DeliverymanOrg.get(key_name=kn, key_value=kv)
#
#     @staticmethod
#     def find_by(cols, where, group_order_limit, *args):
#         """
#         获取符合条件的记录.
#
#         :param str cols: "id, deliveryman_id"
#         :param str where: "where sn REGEXP BINARY ? AND NOT sn=?"
#         :param str group_order_limit: "order by deliveryman_id limit 50"
#         :param list args: list of args to fill into the generated sql params.
#         :return: [{}]
#         """
#         where = "%s %s" % (where, group_order_limit)
#         return DeliverymanOrg.find_by(cols, where, *args)
#
#     """<<<End DB functions"""
#
#     """>>>Begin class util functions"""
#
#     @staticmethod
#     def is_valid_kn_kv(kn, kv):
#         # 检查参数合法性: 只允许按照固定的col_name查找
#         if kn not in ('deliveryman_id', 'sn'):
#             raise ValueError("Invalid param kn=[%s], should be in ('deliveryman_id', 'sn')." % kn)
#         # 检查参数合法性: mysql equals 0 to any str
#         elif not str(kv).isdigit():
#             raise ValueError("Invalid param kv=[%s], should be all digits." % kv)
#         return True
#
#     """<<<End class util functions"""
#
#     """>>>Begin class API functions"""
#
#     @staticmethod
#     def get_level(kn, kv):
#         """
#         获取当前员工(编号/deliveryman_id)所对应的职位
#
#         :param str kn: 'deliveryman_id' or 'sn'
#         :param str kv: '<deliveryman_id>' or '<sn>'
#         :return: 如果存在,返回 level; 否则,返回0
#         :rtype: int
#         """
#         # 参数合法性检查. 如果不合法,直接报错.
#         kn, kv = str(kn), str(kv)
#         DeliverymanOrgLogic.is_valid_kn_kv(kn, kv)
#
#         org = DeliverymanOrg.get(kn, kv)
#         if org:
#             return org.level
#         else:
#             return 0
#
#     @staticmethod
#     def get_leader(kn, kv, require_deliveryman_id=False):
#         """
#         获取直属上级
#
#         :param str kn: 'deliveryman_id' 或者 'sn'
#         :param str kv: '<deliveryman_id>' 或者 '<sn>
#         :param bool require_deliveryman_id: 要求该上级编号对应的真实员工必须存在
#         :return: {'deliveryman_id': <deliveryman_id>, 'sn': <sn>, 'level': <level>}
#         """
#         # 参数合法性检查. 如果不合法,直接报错.
#         kn, kv = str(kn), str(kv)
#         DeliverymanOrgLogic.is_valid_kn_kv(kn, kv)
#
#         my_org = DeliverymanOrg.get(kn, kv)
#         my_level = my_org.level
#         # 岗位已经是最大的, 没有上级
#         if my_level == 7:
#             return None
#
#         # 找上级职位(跳过所有为000的上级), 其实理论上不该存在这样的编号.
#         leader_level = None
#         my_sn = my_org.sn
#         my_sn_list = re.findall('...', my_sn)
#         # 让自己的编码片从小到大排列
#         my_sn_list.reverse()
#         # [0-4]~5
#         for i in xrange(my_level - 2, 6):
#             if my_sn_list[i] != '000':
#                 leader_level = i + 2
#
#         # 提供的参数sn_dict有问题
#         if not leader_level:
#             raise AttributeError("Could not find leader with his man whose sn=[%s] in org." % my_sn)
#         # 拼接正确的上级编号
#         else:
#             leader_sn = my_sn[:3 * (8 - leader_level)] + '000' * (leader_level - 2)
#         # 到数据库找是否存在此sn的人
#         leader = DeliverymanOrgLogic.get(kn='sn', kv=leader_sn)
#         # 要求存在此人, 如果deliveryman_id是0,表示人不在啦,就继续找
#         while require_deliveryman_id and leader and leader.deliveryman_id == 0:
#             logging.info("Leader with sn=[%s] is gone.(deliveryman_id==0)", leader_sn)
#             leader = DeliverymanOrgLogic.get_leader('sn', leader['sn'], require_deliveryman_id=True)
#         # Finally, get my leader.
#         if not leader:
#             # 首先必须存在这样的上级编号表项.如果根本没有这样的编号在表里面,报错.
#             raise AttributeError("Could not find leader with sn=[%s] in org." % leader_sn)
#
#         return {'deliveryman_id': leader.deliveryman_id, 'sn': leader.sn, 'level': leader.level}
#
#     @staticmethod
#     def get_all_leaders(kn, kv, require_deliveryman_id=False):
#         """
#         获取所有上级
#
#         :param str kn: 'deliveryman_id' 或者 'sn'
#         :param str kv: '<deliveryman_id>' 或者 '<sn>
#         :param bool require_deliveryman_id: 要求该上级编号对应的真实员工必须存在
#         :return: [{'deliveryman_id': <deliveryman_id>, 'sn': <sn>, 'level': <level>}]
#         :rtype: list
#         """
#         kn, kv = str(kn), str(kv)
#         leader = DeliverymanOrgLogic.get_leader(kn, kv, require_deliveryman_id)
#         if not leader:
#             return None
#         leaders = []
#         while leader:
#             leaders.append(leader)
#             leader = DeliverymanOrgLogic.get_leader('sn', leader['sn'], require_deliveryman_id)
#         return leaders
#
#     @staticmethod
#     def get_men_directly_under_me(kn, kv, require_deliveryman_id=False):
#         """
#         获取直属下级(有递归).
#
#         :param str kn: 'deliveryman_id' 或者 'sn'
#         :param str kv: '<deliveryman_id>' 或者 '<sn>
#         :param bool require_deliveryman_id: 要求下属编号对应的真实员工必须存在
#         :return: [{'deliveryman_id': <deliveryman_id>, 'sn': <sn>, 'level': <level>}]
#         :rtype: list
#         """
#
#         def traverse(upper_sn, colleges_sn_regex, colleagues, all_men):
#             # 直系手下的sn都不存在, 且这些手下不是最底层的
#             while not colleagues and colleges_sn_regex.index('.000') != len(colleges_sn_regex) - len('.000'):
#                 cutting_point = colleges_sn_regex.index('.000')
#                 colleges_sn_regex = "%s...%s" % (colleges_sn_regex[:cutting_point + 1],
#                                                  colleges_sn_regex[cutting_point + 4:])
#                 colleagues = DeliverymanOrgLogic.find_by('deliveryman_id, sn, level',
#                                                          'where NOT sn=? AND sn REGEXP ?', 'limit 99',
#                                                          upper_sn, colleges_sn_regex)
#             for colleague in colleagues:
#                 if colleague['deliveryman_id'] != 0:  # 该手下存在
#                     all_men.add(colleague)
#                 else:
#                     colleague_sn = colleague['sn']
#                     # 生成下级的编号正则
#                     if colleges_sn_regex.index('.000') == len(colleges_sn_regex) - len('.000'):  # 已经没有下级
#                         continue
#                     cutting_point = colleges_sn_regex.index('.000')
#                     subordinates_sn_regex = "%s...%s" % (colleges_sn_regex[:cutting_point + 1],
#                                                          colleges_sn_regex[cutting_point + 4:])
#                     subordinates = DeliverymanOrgLogic.find_by('deliveryman_id, sn, level',
#                                                                'where NOT sn=? AND sn REGEXP ?', 'limit 99',
#                                                                colleague_sn, subordinates_sn_regex)
#                     traverse(colleague_sn, subordinates_sn_regex, subordinates, all_men)
#
#         # 参数合法性检查. 如果不合法,直接报错.
#         kn, kv = str(kn), str(kv)
#         DeliverymanOrgLogic.is_valid_kn_kv(kn, kv)
#
#         my_org = DeliverymanOrg.get(kn, kv)
#         my_level = my_org.level
#         # 岗位已经是最小的, 没有下级
#         if my_level == 2:
#             return None
#         # 生成下级的编号正则, my_level=[3-7]
#         my_men_sn_regex = my_org.sn[:3 * (8 - my_level)] + '...' * (my_level - 2)
#         # 根据该正则获取所有符合条件的下级员工
#         all_my_men_list = DeliverymanOrgLogic.find_by('deliveryman_id, sn, level',
#                                                       'where NOT sn=? AND sn REGEXP BINARY ?', 'limit 99', my_org.sn,
#                                                       my_men_sn_regex)
#         if require_deliveryman_id:
#             men = set()
#             traverse(my_org.sn, my_men_sn_regex, all_my_men_list, men)
#             all_my_men = [x for x in men]
#         else:
#             all_my_men = all_my_men_list
#         return all_my_men
#
#     @staticmethod
#     def get_my_men(kn, kv, require_deliveryman_id=False):
#         """
#         获取所有下级.
#
#         :param str kn: 'deliveryman_id' 或者 'sn'
#         :param str kv: '<deliveryman_id>' 或者 '<sn>
#         :param bool require_deliveryman_id: 要求下属编号对应的真实员工必须存在
#         :return: [{'deliveryman_id': <deliveryman_id>, 'sn': <sn>, 'level': <level>}]
#         """
#         # 参数合法性检查. 如果不合法,直接报错.
#         kn, kv = str(kn), str(kv)
#         DeliverymanOrgLogic.is_valid_kn_kv(kn, kv)
#
#         my_org = DeliverymanOrg.get(kn, kv)
#         my_level = my_org.level
#         # 岗位已经是最小的, 没有下级
#         if my_level == 2:
#             return None
#         # 生成下级的编号正则, my_level=[3-7]
#         my_men_sn_regex = my_org.sn[:3 * (8 - my_level)] + '...' * (my_level - 2)
#         # 根据该正则获取所有符合条件的下级员工(包含自己)
#         if require_deliveryman_id:
#             all_my_men_list = DeliverymanOrgLogic.find_by('deliveryman_id, sn, level',
#                                                           'WHERE sn REGEXP BINARY ? AND deliveryman_id != 0', '',
#                                                           my_org.sn, my_men_sn_regex)
#         else:
#             all_my_men_list = DeliverymanOrgLogic.find_by('deliveryman_id, sn, level',
#                                                           'where sn REGEXP BINARY ?', '', my_org.sn, my_men_sn_regex)
#         return all_my_men_list
#
#     """<<<End class API functions"""
