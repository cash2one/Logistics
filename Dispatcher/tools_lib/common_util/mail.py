# coding:utf-8
from __future__ import unicode_literals
import logging
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

NO_REPLY_MAIL = "noreply_gezbox@163.com"
MAIL_PASS = "tech123feng"
MAIL_HOST = "smtp.163.com"


def send_mail(to_addrs, title, body, content_type='plain', file_name=None, file_body=None):
    """
    邮件发送
    同步发送，功能简陋，以后再升级
    @param to_addrs: 收件地址
    @param title: 标题
    @param body: 正文
    @param content_type: 类型
    @param file_name:
    @param file_body:
    @return:
    """
    try:
        if not isinstance(to_addrs, list):
            to_addrs = [to_addrs]

        msg = MIMEMultipart()

        msg['From'] = NO_REPLY_MAIL
        msg['To'] = ';'.join(to_addrs)
        msg['Subject'] = Header(title, charset='utf-8').encode()

        attr = MIMEText(body, content_type, 'utf-8')
        msg.attach(attr)

        if file_name:
            if file_body:
                attr = MIMEText(file_body, 'base64', "utf-8")
            else:
                attr = MIMEText(open(file_name).read(), 'base64', "utf-8")
            attr.add_header("Content-Disposition", "attachment", filename=file_name)
            attr.add_header("Content-Type", "application/octet-stream")
            msg.attach(attr)

        # server = smtplib.SMTP(MAIL_HOST, port=25)
        server = smtplib.SMTP_SSL(MAIL_HOST)
        server.login(NO_REPLY_MAIL, MAIL_PASS)
        server.sendmail(NO_REPLY_MAIL, to_addrs=to_addrs, msg=msg.as_string())
        server.quit()
    except Exception as e:
        logging.exception(e)


if __name__ == '__main__':
    send_mail(['chenxinlu@123feng.com', 'fangkai@123feng.com'], '测试', 'hello,world\nsecond line.')
