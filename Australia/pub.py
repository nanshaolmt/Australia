# coding=utf-8

import re
import urllib.request
import config
import binascii
import logging
import time
import inspect
import os
import urllib
import json
# import mq
import traceback
# import pub
# from util.pyDes import *
# import database as db
# import translate.api as trans
# import util.requests as requests
import uuid
import hashlib
from datetime import datetime, timedelta
from calendar import monthrange
from subprocess import check_output, call, STDOUT
from urllib.parse import urlencode, quote
import sys
import settings


# 当前目录名称
CURRENT_DIR_PATH = os.path.dirname(inspect.currentframe().f_code.co_filename)
# 获取MD5值
# print(f"CURRENT_DIR_PATH: {CURRENT_DIR_PATH}")

province = {
    'AH': 'ANHUI SHENG',
    'BJ': 'BEIJING SHI',
    'CH': 'CHONGQING SHI',
    'FJ': 'FUJIAN SHENG',
    'GS': 'GANSU SHENG',
    'GD': 'GUANGDONG SHENG',
    'GX': 'GUANGXI ZHUANGZU ZIZHIQU',
    'GU': 'GUIZHOU SHENG',
    'HI': 'HAINAN SHENG',
    'HE': 'HEBEI SHENG',
    'HL': 'HEILONGJIANG SHENG',
    'HN': 'HENAN SHENG',
    'HK': 'HONG KONG (SPECIAL ADMINISTRATIVE REGION)',
    'HB': 'HUBEI SHENG',
    'HA': 'HUNAN SHENG',
    'JS': 'JIANGSU SHENG',
    'JX': 'JIANGXI SHENG',
    'JL': 'JILIN SHENG',
    'LN': 'LIAONING SHENG',
    'MO': 'MACAO (SPECIAL ADMINISTRATIVE REGION)',
    'NM': 'NEI MONGOL ZIZHIQU',
    'NX': 'NINGXIA HUIZI ZIZHIQU',
    'QH': 'QINGHAI SHENG',
    'SN': 'SHAANXI SHENG',
    'SD': 'SHANDONG SHENG',
    'SH': 'SHANGHAI SHI',
    'SX': 'SHANXI SHENG',
    'SC': 'SICHUAN SHENG',
    'TW': 'TAIWAN SHENG',
    'TJ': 'TIANJIN SHI',
    'XJ': 'XINJIANG UYGUR ZIZHIQU',
    'XZ': 'XIZANG ZIZHIQU',
    'YN': 'YUNNAN SHENG',
    'ZJ': 'ZHEJIANG SHENG'
}


def fmst(st=None, dis="01", new=1):
    """
    dis "000111" 正0 正1 负1
    """
    strs = "0123456789abcdefghijklmnopqrstuvwxyz"
    if new:
        if len(st) != len(dis) // 2:
            print(f"参数长度不一致 st: {st} dis: {dis}")
        if len(st) == 1:
            s = strs.find(st[0])
            d = int(dis[:2])
            return strs[s + d] if d < 10 else strs[s - d % 10]
        else:
            return "%s%s" % (fmst(st[:-1], dis[:-2]), fmst(st[-1], dis[-2:]))
    else:
        if len(st) == 2:
            a, b = st
            i = strs.find(a)
            o = strs.find(b)
            n = i * 36 + o + dis
            x = (n) // 36
            y = (n) % 36
            print(f"i: {i}, o: {o}, x: {x}, y: {y}")
            st = strs[x] + strs[y]
        elif len(st) == 3:
            a, b, c = st
            i = strs.find(a)
            o = strs.find(b)
            x = strs.find(c)
            if dis == 1:
                st = a + strs[o - 1] + strs[x + 1]
            elif dis == 2:
                st = strs[i + 1] + strs[o - 1] + strs[x + 1]
        elif len(st) == 5:
                a = st[0]
                b = st[2]
                i = strs.find(a) + 2
                o = strs.find(b) + 1
                st = strs[i] + st[1] + strs[o] + st[3:]
        return st


def is_json(strs):
    if isinstance(strs, str):
        try:
            result = json.loads(strs)
            return result
        except Exception:
            pass
    return False


# 获取正则表达式匹配值
def get_reg_value(regs, src):
    # 如果为列表，循环，以此获取正则值
    # print(str(regs))
    if(isinstance(regs, list)):
        for i in range(0, len(regs)):
            # print(i)
            src = get_reg_value_ex(regs[i], src)
        return src
    else:
        return get_reg_value_ex(regs, src)


# 高级的获取正则表达式的值
def get_reg_value_ex(parttern, src):
    pattern = re.compile(parttern)
    # print(str(pattern))
    match = pattern.search(src)
    if match:
        # print(str(match))
        return match.group()
    else:
        return ""


# 高级的获取正则表达式的值2，要两次才匹配的出来的情况
def get_reg_value_ex2(parttern1, parttern2, src):
    lst = get_reg_value_list(parttern1, src)
    # print(parttern2)
    # print('(?<="checkbox" name=").+?(?=".+成都-走马街)')
    for i in range(0, len(lst)):
        txt = lst[i]
        val = get_reg_value(r'' + parttern2 + r'', txt)
        if val:
            return val
    return ""


def get_reg_value_list(parttern, src):
    pattern = re.compile(parttern)
    match = pattern.findall(src)
    if match:
        return match
    else:
        return []
