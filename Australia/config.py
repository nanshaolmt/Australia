# coding=utf-8

""" 配置文件 """
import logging
import configparser  # 可以读写和解析注释文件, 但是没有写入注释的功能
import inspect
import os
import sys
import io


# os.path.dirname()返回绝对路径文件夹
#-----拿到当前的文件的父目录.C/../Australia
dirPath = os.path.dirname(inspect.currentframe().f_code.co_filename)
# 拼接路径
cfgfile = dirPath + "/config.ini"


# 读写配置文件
config = configparser.ConfigParser()
# config.read(cfgfile)
# 打开file对象并返回对应的数据流。如果打开失败，则抛出IOError异常,file是文件路径，或者是文件描述序号
with io.open(cfgfile, 'r', encoding='utf_8_sig') as fp:
    config.readfp(fp)


BASE_PYTHON_COMMAND = config.get("BASE", "PYTHON_COMMAND")
DB_PREFIX = config.get("DB", "PREFIX")
# 文件路径
BASE_FILE_DIR = config.get("BASE", "FILE_DIR")
# 日志路径
# os.path.join合并目录
LOGS_DIR = os.path.join(BASE_FILE_DIR, "logs")
#是否是开发环境
IS_DEVELOP = config.get("BASE", "IS_DEVELOP")


def get_log(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        # 创建日志的级别
        logger.setLevel(logging.DEBUG)
        if not os.path.isdir(LOGS_DIR):
            os.makedirs(LOGS_DIR)
        # 创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        # 定义handler的输出格式formatter
        formatter_con = logging.Formatter(fmt='%(levelname)s %(module)s[line:%(lineno)d]    %(message)s')
        # setFormatter设置日志格式
        ch.setFormatter(formatter_con)
        # 创建一个handler，用于写入日志文件
        fh = logging.FileHandler(os.path.join(LOGS_DIR, '{}.log'.format(name)), encoding="utf-8")
        # formatter，定义了最终log信息的顺序, 结构和内容
        formatter_file = logging.Formatter(
            fmt='%(levelname)s %(asctime)s %(module)s[line:%(lineno)d]    %(message)s',
            datefmt='%a %Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter_file)
        # 给logger添加handler
        # logger.addFilter(filter)
        logger.addHandler(fh)
        if IS_DEVELOP:
            logger.addHandler(ch)
    return logger

# BASE_EMAIL = config.get('BASE', 'EMAIL')
# BASE_BANK_CARD_INFO_URL = config.get('BASE', 'BANK_CARD_INFO_URL')

# 消息队列消息间隔时间
# GET_ORDER_INTERVAL = int(config.get('BASE', 'GET_ORDER_INTERVAL'))

# 消息队列地址
# QUEUE_HOST = str(config.get("QUEUE", "QUEUE_HOST"))
# 消息队列虚拟机
# QUEUE_VHOST = str(config.get("QUEUE", "QUEUE_VHOST"))
# 消息队列端口
# QUEUE_PORT = int(config.get("QUEUE", "QUEUE_PORT"))
# 消息队列登录名
# QUEUE_USER = str(config.get("QUEUE", "QUEUE_USER"))
# 消息队列密码
# QUEUE_PASSWORD = str(config.get("QUEUE", "QUEUE_PASSWORD"))


'''
BASE_INTERFACE_URL  = config.get("BASE", "INTERFACE_URL")
#客户端列表
CLIENTS = []
CLIENTS_CLIENT_ID = config.get("CLIENTS", "CLIENT_ID").split(", ")
i=0
while(i<len(CLIENTS_CLIENT_ID)):
    CLIENTS.append({"id": CLIENTS_CLIENT_ID[i],
                    "md5key":config.get("CLIENTS", "MD5KEY_" + str(CLIENTS_CLIENT_ID[i])),
                    "deskey":config.get("CLIENTS", "DESKEY_" + str(CLIENTS_CLIENT_ID[i]))})
    i+=1
#print CLIENTS
'''

