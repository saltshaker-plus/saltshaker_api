# -*- coding:utf-8 -*-
import configparser
import os
import socket
from common.log import loggers
from common.db import DB

logger = loggers()

config = configparser.ConfigParser()
conf_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
config.read(conf_path + "/saltshaker.conf")
rsync_host = config.get("Rsync", "RSYNC_HOST")
rsync_port = config.get("Rsync", "RSYNC_PORT")
rsync_path = config.get("Rsync", "RSYNC_PATH")
rsync_module = config.get("Rsync", "RSYNC_MODULE")
hosts_allow = config.get("Rsync", "HOSTS_ALLOW")
hosts_deny = config.get("Rsync", "HOSTS_DENY")


def rsync_config():
    file_name = "/etc/rsyncd_%s.conf" % str(rsync_port)
    conf = '''uid             = nobody
gid             = nobody
use chroot      = no
max connections = 200
address = %s
port = %s

''' % (rsync_host, str(rsync_port))

    # 根据产品生成对应的Rsync模块
    db = DB()
    status, result = db.select("product", "")
    db.close_mysql()
    if status is True:
        product_list = result
    else:
        return {"status": False, "message": result}, 500
    if os.path.exists(file_name):
        os.remove(file_name)
    with open(file_name, "x") as file:
        file.write(conf)
        for i in product_list:
            if i.get("file_server") == "rsync":
                rsync_path_product = rsync_path + "/" + i.get("id")
                modules = '''
[%s]
path = %s
hosts allow = %s
hosts deny  = %s
read only = false
list      = false
uid = root
gid = root
''' % (i.get("id"), rsync_path_product, hosts_allow, hosts_deny)
                file.write(modules)
                # 创建Rsync对应的目录
                if not os.path.exists(rsync_path_product):
                    os.makedirs(rsync_path_product)
        # 启动Rsync服务
        if not port_check(rsync_host, int(rsync_port)):
            rsync = os.popen("which rsync").readline().strip("\n")
            os.popen("%s --daemon --config=%s" % (rsync, file_name))


def port_check(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except Exception as _:
        return False


if __name__ == "__main__":
    rsync_config()
