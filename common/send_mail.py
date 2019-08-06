# -*- coding:utf-8 -*-
from common.log import loggers
import configparser
import os
from email.header import Header
from email.mime.text import MIMEText
import smtplib

logger = loggers()

config = configparser.ConfigParser()
conf_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
config.read(conf_path + "/saltshaker.conf")
from_addr = config.get("Mail", "FROM_ADDR")
password = config.get("Mail", "MAIL_PASSWORD")
smtp_server = config.get("Mail", "SMTP_SERVER")
smtp_port = config.get("Mail", "SMTP_PORT")

def send_mail(to_addr, sub, content):
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = "Saltshaker <%s>" % from_addr
    msg['To'] = to_addr
    msg['Subject'] = Header(sub, "utf-8")
    server = smtplib.SMTP(smtp_server, 25)
    # server.set_debuglevel(1)
    server.login(from_addr, password)
    server.sendmail(from_addr, [to_addr], msg.as_string())
    server.quit()
