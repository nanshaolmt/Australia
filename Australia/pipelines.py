#!/usr/bin/env python
# coding: utf-8
"""
@File   : pipelines.py
@Remarks: 数据库操作模块
@Author : ZhaoBin
@Date   : 2018-12-16 18:37:06
@Last Modified by   : ZhaoBin
@Last Modified time : 2018-12-16 18:37:06
"""

import pymysql
from DBUtils.PooledDB import PooledDB
from pymysql.cursors import DictCursor, Cursor

import config
import settings

# 测试上的。
DBHOST = config.config.get("CSDB", "HOST")
DBPORT = int(config.config.get("CSDB", "PORT"))
DBUSER = config.config.get("CSDB", "USER")
DBPWD = config.config.get("CSDB", "PASSWORD")
DBNAME = config.config.get("CSDB", "DB_NAME")
DBCHAR = config.config.get("CSDB", "CHARSET")

# DBHOST = config.config.get("DB", "HOST")
# DBPORT = int(config.config.get("DB", "PORT"))
# DBUSER = config.config.get("DB", "USER")
# DBPWD = config.config.get("DB", "PASSWORD")
# DBNAME = config.config.get("DB", "DB_NAME")
# DBCHAR = config.config.get("DB", "CHARSET")


class Mysql(object):
    """
     1、执行带参数的 sql 时，请先用sql语句指定需要输入的条件列表，然后再用tuple/list进行条件匹配
    ２、在格式 sql 中不需要使用引号指定数据类型，系统会根据输入参数自动识别
    ３、在输入的值中不需要使用转意函数，系统会自动处理
    MYSQL数据库对象，负责产生数据库连接 , 此类中的连接采用连接池实现获取连接对象：conn = Mysql.getConn()
        释放连接对象: conn.close() 或 del conn
    """
    # 连接池对象
    __pool = None
    SELSQL = 'SELECT {sel} FROM {tb} '
    UPDSQL = "UPDATE {tb} SET {upd} "
    WHERE = "WHERE {cond} "
    INSSQL = "INSERT INTO {tb} ({field}) VALUES({val}) "

    def __init__(self, dictcur=True, **kwargs):
        self.logger = kwargs.get("logger", None)
        if not self.logger:
            self.logger = config.get_log("Mysql")
        self.getConn(dictcur)

    def getConn(self, dictcur):
        # 数据库构造函数，从连接池中取出连接，并生成操作游标
        self._conn = Mysql.__getConn(dictcur)

    @staticmethod
    def __getConn(dictcur):
        """
        @summary: 静态方法，从连接池中取出连接
        @return MySQLdb.connection
        """
        cur = DictCursor if dictcur else Cursor
        if Mysql.__pool is None:
            Mysql.__pool = PooledDB(
                creator=pymysql, mincached=1, maxcached=20,
                host=DBHOST, port=DBPORT,
                user=DBUSER, passwd=DBPWD,
                db=DBNAME, use_unicode=True,
                charset=DBCHAR, cursorclass=cur
            )
            #连接数据库
        return Mysql.__pool.connection()


    # 查询语句创建
    # (tb=TB_INFO, sel="COUNT(*) as c", cond={"status": 1})
    def select_sql(self, tb, sel="*", cond=None, param=""):


        """
        @summary    : 查询 SQL 语句拼接
        @param tb   : 所要查询的表名
        @param sel  : 要查询的字段
        @param cond : 查询的条件
        @param param: 查询的其它语句
        @return sql : 查询语句
        @return val : 参数
        """

        if not tb:
            self.logger.debug("查询语句未传递表名")
            raise Exception("查询语句未传递表名")
        sql = self.SELSQL.format(sel=sel, tb=tb)  #为了下面去拼接
        val = []
        if cond and isinstance(cond, dict):
            #----状态  cond={"status": 1}
            keys = list(cond.keys())
            key = ", ".join([f"{k}=%s" for k in keys])   #列表['status']
            val = [cond[k] for k in keys]
            sql += self.WHERE.format(cond=key) if cond else ""
        elif cond and isinstance(cond, str):
            sql += self.WHERE.format(cond=cond)

        sql += param
        self.logger.info(f"{sql} - {str(val)}")
        return (sql, val) if val else sql

    # 更新语句创建
    def update_sql(self, tb, cond=None, **kwargs):
        """
        @summary: 更新 SQL 语句拼接
        @param tb: 所要更新的表名
        @param cond: 更新的条件
        @param kwargs: 更新的字典化数据
        @return sql: 更新语句
        @return val: 参数
        """
        if not (tb and kwargs):
            self.logger.debug("更新语句表名未传或参数未设置")
            raise Exception("更新语句表名未传或参数未设置")
        keys = list(kwargs.keys())
        key = ", ".join([f"{k}=%s" for k in keys])
        val = [kwargs[k] for k in keys]
        # key = 'k1=%s, k2=%s
        sql = self.UPDSQL.format(tb=tb, upd=key)
        #"UPDATE 个人信息表  SET 字段条件 "
        if isinstance(cond, dict):
            keys = list(cond.keys())
            key = ", ".join([f"{k}=%s" for k in keys])
            val += [cond[k] for k in keys]
            sql += self.WHERE.format(cond=key) if cond else ""
        elif isinstance(cond, str):
            sql += cond + " "
        self.logger.info(f"{sql} - {str(val)}")
        return sql, val


    # 插入语句创建
    def insert_sql(self, tb, **kwargs):
        """
        @summary: 插入 SQL 语句拼接
        @param tb: 所要插入的表名
        @param kwargs: 插入的字典化数据
        @return sql: 插入语句
        @return val: 参数
        """
        if not (tb and kwargs):
            self.logger.debug("插入语句表名未传或参数未设置")
            raise Exception("插入语句表名未传或参数未设置")
        keys = list(kwargs.keys())
        fields = ", ".join([key for key in keys])
        val = [kwargs[k] for k in keys]
        values = ", ".join("%s" for _ in val)
        sql = self.INSSQL.format(tb=tb, field=fields, val=values)

        # self.logger.info(f"{sql} - {str(val)}")
        return sql, val

    # 查询所有
    def getAll(self, sql, param=None):
        """
        @summary: 执行查询，并取出所有结果集
        @param sql:查询 sql ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list(字典对象)/boolean 查询到的结果集
        """
        self._cursor = self._conn.cursor()
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchall()
        else:
            result = []
        self._cursor.close()
        return result

    def getNum(self, sql, param=None):
        """
        @summary: 执行查询，并取出查询数量
        @param sql:查询 sql ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list(字典对象)/boolean 查询到的结果集
        """
        self._cursor = self._conn.cursor()
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        self._cursor.close()
        return count

    # 查询第一个
    def getOne(self, sql, param=None):
        """
        @summary: 执行查询，并取出第一条
        @param sql:查询 sql ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list/boolean 查询到的结果集
        """
        self._cursor = self._conn.cursor()
        print('204----',param)   #[1]
        if param is None:
            count = self._cursor.execute(sql)
        else:
            # print('inter-208',sql)   #SELECT COUNT(*) as c FROM dc_business_australia_info_eng WHERE status=%s
            #执行sql语句，返回sql查询成功的记录数目  防sql 注入
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchone()
            # print('Pip-211',result)
        else:
            result = {} if isinstance(self._cursor._cursor, DictCursor) else ()
        self._cursor.close()
        return result

    # 查询多个
    def getMany(self, sql, num, param=None):
        """
        @summary: 执行查询，并取出num条结果
        @param sql:查询 sql ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param num:取得的结果条数
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list/boolean 查询到的结果集
        """
        self._cursor = self._conn.cursor()
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchmany(num)
        else:
            result = []
        self._cursor.close()
        return result

    # 插入一条
    def insertOne(self, sql, value):
        """
        @summary: 向数据表插入一条记录
        @param sql:要插入的 sql 格式
        @param value:要插入的记录数据tuple/list
        @return result: 插入数据的 Id 值
        """
        result = self.__getInsertId() if self.__query(sql, value) else None
        return result

    # 插入多条
    def insertMany(self, sql, values):
        """
        @summary: 向数据表插入多条记录
        @param sql:要插入的 sql 格式
        @param values:要插入的记录数据tuple(tuple)/list[list]
        @return: count 受影响的行数
        """
        self._cursor = self._conn.cursor()
        count = self._cursor.executemany(sql, values)
        result = self.__getInsertId() if self.end() else None
        self._cursor.close()
        return count, result

    # 获取当前连接最后一次插入操作生成的id,如果没有则为０
    def __getInsertId(self):
        """
        获取当前连接最后一次插入操作生成的id,如果没有则为０
        """
        self._cursor.execute("SELECT @@IDENTITY AS id")
        result = self._cursor.fetchall()
        return result[0]['id']

    # 执行 sql 语句
    def execute(self, sql, param=None):
        """
        @summary: 执行 sql 语句
        @param sql:  sql 格式及条件，使用(%s,%s)
        @param param: 参数 tuple/list
        @return: count 受影响的行数
        """
        return self.__query(sql, param)

    # 「底层」执行 sql 语句
    def __query(self, sql, param=None):
        self._cursor = self._conn.cursor()
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
            #关闭游标
        self._cursor.close()
        return count if self.end() else None

    # 更新数据表记录
    def update(self, sql, param=None):
        """
        @summary: 更新数据表记录
        @param sql:  sql 格式及条件，使用(%s,%s)
        @param param: 要更新的  值 tuple/list
        @return: count 受影响的行数
        """
        return self.__query(sql, param)

    # 删除数据表记录
    def delete(self, sql, param=None):
        """
        @summary: 删除数据表记录
        @param sql:  sql 格式及条件，使用(%s,%s)
        @param param: 要删除的条件 值 tuple/list
        @return: count 受影响的行数
        """
        return self.__query(sql, param)

    # 开启事务
    def begin(self):
        """
        @summary: 开启事务
        """
        self._conn.autocommit(0)

    # 结束事务
    def end(self, option='commit'):
        """
        @summary: 结束事务
        """
        if option == 'commit':
            try:
                self._conn.commit()
                return 1
            except Exception:
                self._conn.rollback()
        else:
            self._conn.rollback()

    # 释放连接池资源
    def dispose(self, isEnd=1):
        """
        @summary: 释放连接池资源
        """
        if isEnd == 1:
            self.end('commit')
        else:
            self.end('rollback')
        self._conn.close()
