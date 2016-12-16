# coding:utf-8
import arrow
from uuid import uuid4

from mongoengine import Document, StringField, DictField, DateTimeField


class Account(Document):
    """
    任何配送员\众包\商户\公司员工对应的外部聊天帐号
    """
    client_id = StringField(help_text="风信帐号", max_length=64)  # "不多于 64 个字符的字符串"
    account = DictField(default={"account_id": "", "account_type": ""}, help_text='外部账号', unique=True)
    create_time = DateTimeField(default=arrow.utcnow().datetime)

    meta = {
        "collection": "account",
        "indexes": [
            "client_id",
            "account"
        ]
    }

    @classmethod
    def create_account(cls, account_id, account_type, existed_account_obj=None):
        """
        设置一个新的account
        :param account_id:
        :param account_type:
        :param existed_account_obj: 如果给了,则表示新创建的账户与之共享client_id
        :return:
        """
        new_obj = cls()
        # 创建唯一的client_id与时间挂勾,以防止出现重复的client_id
        new_obj.client_id = uuid4().hex
        if existed_account_obj:
            new_obj.client_id = existed_account_obj.client_id
        new_obj.account["account_id"] = account_id
        new_obj.account["account_type"] = account_type
        new_obj.save()
        return new_obj

    def format_response(self):
        return {
            "account_id": self.account["account_id"],
            "account_type": self.account["account_type"],
            "client_id": self.client_id
        }
