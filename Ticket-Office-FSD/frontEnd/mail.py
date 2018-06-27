#!/usr/bin/python
# -*- coding: UTF-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.header import Header


class SendEmail(object):

    def __init__(self):
        self.mail_host = "smtp.126.com"  # 设置服务器
        self.mail_user = "sjtu_acm_class@126.com"  # 用户名
        self.mail_pass = "keepmoving"  # 口令
        self.mail_pass2 = "keepmoving123456"  # 口令
        self.smtpObj = smtplib.SMTP_SSL(self.mail_host, 465)
        self.smtpObj.ehlo()  # 25 为 SMTP 端口号
        self.smtpObj.login(self.mail_user, self.mail_pass2)
        self.sender = 'sjtu_acm_class@126.com'

    def send(self, Email, Title, Content):
        self.mail_host = "smtp.126.com"  # 设置服务器
        self.mail_user = "sjtu_acm_class@126.com"  # 用户名
        self.mail_pass = "keepmoving"  # 口令
        self.mail_pass2 = "keepmoving123456"  # 口令
        self.smtpObj = smtplib.SMTP_SSL(self.mail_host, 465)
        self.smtpObj.ehlo()  # 25 为 SMTP 端口号
        self.smtpObj.login(self.mail_user, self.mail_pass2)
        self.sender = 'sjtu_acm_class@126.com'

        self.message = MIMEText(Content, 'plain', 'utf-8')
        self.message['To'] = Header(Email)
        self.receivers = Email  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
        self.message['From'] = Header("sjtu_acm_class@126.com", 'utf-8')
        self.subject = 'SJTU ACM CLASS: ' + Title
        self.message['Subject'] = Header(self.subject, 'utf-8')
        self.smtpObj.sendmail(self.sender, self.receivers, self.message.as_string())
        self.smtpObj.close()


if __name__ == '__main__':
    email = SendEmail()
    email.send('lijiasen0921@126.com', 'Title I like', 'This is\nthe email')
    email.send('lijiasen0921@126.com', 'Title J like', 'This is\nthe EWmail')
