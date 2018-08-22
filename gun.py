#!/usr/bin/python
# coding:utf-8
import multiprocessing

bind = '0.0.0.0:9000'
# 用于处理工作进程的数量
workers = multiprocessing.cpu_count() * 2 + 1
# 等待服务的客户的数量,一般设置为2048，超过这个数字将导致客户端在尝试连接时错误
backlog = 2048
# 要使用的工作模式, 默认为sync，使用gevent需要安装gevent， pip install gevent
worker_class = "gevent"
loglevel = 'debug'
accesslog = '/var/log/gunicorn/access.log'
errorlog = '/var/log/gunicorn/error.log'
capture_output = True
