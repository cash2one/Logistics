#!/usr/bin/env python
# coding:utf-8
import os
import sys

# 模块自己的PYTHON_PATH, 让代码找到正确的tools_lib. =>要在所有import前做!!!
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))
import requests
from model_logics.config import CONFIGS
from tools_lib.transwarp import db
from tools_lib.transwarp.web import safe_str
# from tools_lib.windchat import send_plain_text_to_delivers_shortcut

# init db:
db.create_engine(**CONFIGS.db)

# 去掉中队长和司机
minus_teamleader = {7770037, 7753062, 7752078, 7766504, 7767437, 7793155, 7768503, 7806286, 7805057, 7755753, 7753710,
                    7754434, 7758378, 7752697, 7769354, 7772660, 7775557, 7800704, 7758906, 7755309, 7766637, 7760535,
                    7799143, 7756821, 7752047, 7757831, 7773944, 7751971, 7777089, 7769666, 7752788, 7755798, 7752353,
                    7792505, 7757544, 7796727, 7810020, 7810019, 7797911, 7755037, 7760575, 7795050, 7753283, 7773529,
                    7750801, 7751513, 7756383, 7757174, 7767840, 7753078, 7808288, 7753086, 7800143, 7785679, 7753035,
                    7752017, 7759276, 7796319, 7760451, 7788609, 7766895, 7761511, 7762177, 7761263, 7764255, 7779111,
                    7795570, 7795841, 7796735, 7754317, 7760519, 7768534, 7759870, 7775209, 7755781, 7761327, 7760256,
                    7754672, 7763041, 7763264, 7769619, 7767029, 7751275, 7774453, 7771247, 7773415, 7774732, 7766639,
                    7756098, 7791883, 7753599, 7752867, 7771835, 7768832, 7772637, 7757598, 7755126, 7751731, 7752257,
                    7754736, 7756280, 7749908, 7751126, 7771327, 7782955, 7751934, 7767455, 7754606, 7751383, 7762694,
                    7755772, 7758426, 7767700, 7763623, 7750832, 7771424, 7753857, 7767879, 7769551, 7778635}
drivers = db.select("select id from f_deliveryman.deliveryman where job_description='driver'")
minus_driver = {t[0] for t in drivers}
testers = db.select("select id from f_deliveryman.deliveryman where real_name like '%测试%'")
testers = {t[0] for t in testers}

print(("length of minus_teamleader=[%s]. type=[%s]" % (len(minus_teamleader), type(minus_teamleader))))
print(("length of minus_driver=[%s]. type=[%s]" % (len(minus_driver), type(minus_driver))))
print(("length of testers=[%s]. type=[%s]" % (len(testers), type(testers))))

# 找到所有在架构中的人
all_working = db.select(
    "SELECT user_id FROM user_center.deliver_org where deleted <> 1 and level in (2, 3, 4) and user_id <> 0")
all_working = {t[0] for t in all_working}
print(("length of all_working=[%s]. type=[%s]" % (len(all_working), type(all_working))))

out = all_working - minus_teamleader - minus_driver - testers
print(("length of out=[%s]. type=[%s]" % (len(out), type(out))))

# 找到所有11月累计10日无营收
ten_no_tip = db.select("""
                        SELECT
                            user_id
                        FROM
                            F_DB_EVENT_PS.daily_rank_v3
                        WHERE
                            deleted <> 1
                                AND statistic_date BETWEEN '2015-11-1' AND '2015-11-30'
                                AND tip = 0
                                AND org_level IN (2, 3, 4)
                        GROUP BY user_id
                        HAVING COUNT(*) >= 10""")
ten_no_tip = {t[0] for t in ten_no_tip}
print(("length of ten_no_tip=[%s]. type=[%s]" % (len(ten_no_tip), type(ten_no_tip))))

out &= ten_no_tip
print("")

# 去掉不是BINDING和WORKING状态的（没法APPLY_RESIGN）
invalids = db.select("""
                select
                    status
                from f_deliveryman.deliveryman
                where
                    id in (%s) and status not in ('CHECK_BINDING_TEAM', 'CHECK_WORKING')
                """ % ','.join([str(i) for i in out]))
invalids_status = set([t[0] for t in invalids])
valid = db.select("""
                select
                    id
                from f_deliveryman.deliveryman
                where
                    id in (%s) and status in ('CHECK_BINDING_TEAM', 'CHECK_WORKING')"""
                  % ','.join([str(i) for i in out]))
valid = {t[0] for t in valid}
print(("Invalids are in status %s." % invalids_status))
print(("Auto apply resign: [%s/%s]." % ((len(out) - len(invalids)), len(out))))

bindings = db.select("""
                select
                    id
                from f_deliveryman.deliveryman
                where
                    id in (%s) and status = 'CHECK_BINDING_TEAM'
                """ % ','.join([str(i) for i in out]))
print(("Auto apply resign valids = [WORKING][%s] + [BINDING_TEAM][%s]." %
      ((len(out) - len(invalids) - len(bindings)), len(bindings))))
bindings = {t[0] for t in bindings}
print(("WORKING=%s" % (valid-bindings)))
print(("BINDING=%s" % bindings))


# 自动申请离职
suc, err = 0, 0
suc_man = []
for man in valid:
    url = "http://10.171.99.129:5555/deliveryman/event/%s/EVENT_APPLY_RESIGN" % man
    # print url
    # r = requests.post(url, json={"remark": "自动申请离职"})
    # if r.status_code != 200:
    #     err += 1
    # else:
    #     suc += 1
    #     suc_man.append(man)
print(("Auto apply resign: succeeded=[%s], failed=[%s], mans=[%s]." % (suc, err, len(suc_man))))
print(suc_man)

# 发风信通知
# send_plain_text_to_delivers_shortcut(suc_man, safe_utf8("您好, 由于系统检测到您长期没有送单, 于是自动为您申请了离职, 请您按照要求归还装备办理离职手续, 如需撤销离职, 请到账户/工作分配/离职申请下点击撤销离职."))
