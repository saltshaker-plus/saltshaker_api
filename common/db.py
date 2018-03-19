# -*- coding:utf-8 -*-
import pymysql
import configparser
import os
from common.log import Logger

logger = Logger()

config = configparser.ConfigParser()
conf_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
config.read(conf_path + "/saltshaker.conf")
mysql_host = config.get("Mysql", "MYSQL_HOST")
mysql_port = config.get("Mysql", "MYSQL_PORT")
mysql_user = config.get("Mysql", "MYSQL_USER")
mysql_password = config.get("Mysql", "MYSQL_PASSWORD")
mysql_db = config.get("Mysql", "MYSQL_DB")
mysql_charset = config.get("Mysql", "MYSQL_CHARSET")


class DB(object):
    def __init__(self):
        self.host = mysql_host
        self.port = int(mysql_port)
        self.user = mysql_user
        self.password = mysql_password
        self.db = mysql_db
        self.charset = mysql_charset
        self.conn, self.cursor = self.connect_mysql()

    def connect_mysql(self):
        try:
            conn = pymysql.Connect(
                host=self.host,
                port=self.port,
                user=self.user,
                passwd=self.password,
                db=self.db,
                charset=self.charset
            )
            conn.autocommit(False)
            cursor = conn.cursor()
            return conn, cursor
        except Exception as e:
            logger.info("Connect mysql error: %s" % e)

    def select_by_id(self, table, id):
        sql = "SELECT * FROM %s WHERE data -> '$.id'='%s'" % (table, id)
        logger.info(sql)
        try:
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return True, result
        except Exception as e:
            logger.info("Select by id error: %s" % e)
            return False, str(e)

    def select(self, table, arg):
        sql_create = "CREATE TABLE IF NOT EXISTS %s(data json)" % table
        logger.info(sql_create)
        self.cursor.execute(sql_create)
        self.conn.commit()
        sql = "SELECT * FROM %s %s" % (table, arg)
        logger.info(sql)
        try:
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            return True, result
        except Exception as e:
            logger.info("Select by id error: %s" % e)
            return False, str(e)

    def delete_by_id(self, table, id):
        sql = "DELETE FROM %s WHERE data -> '$.id'='%s'" % (table, id)
        logger.info(sql)
        try:
            self.cursor.execute(sql)
            self.conn.commit()
            return True, self.cursor.rowcount
        except Exception as e:
            logger.info("Delete by id error: %s" % e)
            self.conn.rollback()
            return False, str(e)

    def update_by_id(self, table, data, id):
        sql = "UPDATE %s SET data='%s' WHERE data -> '$.id'='%s'" % (table, data.replace("'", r"\'"), id)
        logger.info(sql)
        try:
            self.cursor.execute(sql)
            self.conn.commit()
            return True, self.cursor.rowcount
        except Exception as e:
            logger.info("Insert error: %s" % e)
            self.conn.rollback()
            return False, str(e)

    def insert(self, table, data):
        sql_create = "CREATE TABLE IF NOT EXISTS %s(data json)" % table
        logger.info(sql_create)
        self.cursor.execute(sql_create)
        self.conn.commit()
        # 转义'
        sql = "INSERT INTO %s(data) VALUES('%s') " % (table, data.replace("'", r"\'"))
        logger.info(sql)
        try:
            self.cursor.execute(sql)
            self.conn.commit()
            return True, self.cursor.rowcount
        except Exception as e:
            logger.info("Insert error: %s" % e)
            self.conn.rollback()
            return False, str(e)
        # finally:
        #     self.cursor.close()
        #     self.conn.close()

    def close_mysql(self):
        self.cursor.close()
        self.conn.close()
