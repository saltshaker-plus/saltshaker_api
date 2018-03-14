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
        try:
            self.conn = pymysql.Connect(
                host=mysql_host,
                port=int(mysql_port),
                user=mysql_user,
                passwd=mysql_password,
                db=mysql_db,
                charset=mysql_charset
            )
            self.conn.autocommit(False)
            self.cursor = self.conn.cursor()
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
            self.cursor.close()
            self.conn.close()
            return True, self.cursor.rowcount
        except Exception as e:
            logger.info("Delete by id error: %s" % e)
            self.conn.rollback()
            self.cursor.close()
            self.conn.close()
            return False, str(e)

    def update_by_id(self, table, data, id):
        sql = "UPDATE %s SET data='%s' WHERE data -> '$.id'='%s'" % (table, data, id)
        logger.info(sql)
        try:
            self.cursor.execute(sql)
            self.conn.commit()
            self.cursor.close()
            self.conn.close()
            return True, self.cursor.rowcount
        except Exception as e:
            logger.info("Insert error: %s" % e)
            self.conn.rollback()
            self.cursor.close()
            self.conn.close()
            return False, str(e)

    def insert(self, table, data):
        sql_create = "CREATE TABLE IF NOT EXISTS %s(data json)" % table
        logger.info(sql_create)
        self.cursor.execute(sql_create)
        self.conn.commit()
        sql = "INSERT INTO %s(data) VALUES('%s') " % (table, data)
        logger.info(sql)
        try:
            self.cursor.execute(sql)
            self.conn.commit()
            self.cursor.close()
            self.conn.close()
            return True, self.cursor.rowcount
        except Exception as e:
            logger.info("Insert error: %s" % e)
            self.conn.rollback()
            self.cursor.close()
            self.conn.close()
            return False, str(e)
