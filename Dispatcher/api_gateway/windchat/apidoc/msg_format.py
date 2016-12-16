#coding=utf-8
__author__ = 'kk'


def windchat_message_format():
    """
    @apiDefine base_wc_msg_format
    @apiExample {json} 代码示例

        // 对话格式
        {
            "talker_type": "man" "shop" "staff",                // 账户类型
            "talker_name": "黄银洁",                             // 对话者显示名
            "talker_id": "qazxswedc321"                         // 账户 id
            "talker_avatar": "http://imkk.me/favicon.png"       // 头像 URL
            "message_type": 1                                   // 消息类型
            "message": {
                "title": "标题",
                "content": "正文",
                "summary": "摘要",
                "description": "描述,在最上面",
                "url": "链接"
                "id":
            }
        }

        消息类型:
        1 纯文本, content
        2 单纯图片, url
        3 配送提醒content, description
        4 线路变更提醒content, description
        5 报备邀请消息, id
        6 操作结果提示(灰色小框), content


    """
    pass


def fe_windchat_message_format():
    """
    @api {format} url 消息类型代码+消息格式
    @apiName fe_wc_message_format
    @apiGroup fe_windchat
    @apiVersion 4.0.0

    @apiUse base_wc_msg_format
    """
    pass


def app_windchat_message_format():
    """
    @api {format} url 消息类型代码+消息格式
    @apiName app_wc_message_format
    @apiGroup app_windchat
    @apiVersion 4.0.0

    @apiUse base_wc_msg_format
    """
    pass


def open_windchat_message_format():
    """
    @api {format} url 消息类型代码+消息格式
    @apiName open_windchat_message_format
    @apiGroup open_windchat
    @apiVersion 4.0.0

    @apiUse base_wc_msg_format
    """
    pass
