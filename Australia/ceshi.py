#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File  : ceshi.py
@Author: ChenLei
@Date  : 2019/6/26
"""
import inspect
import os
import requests
import json

BASEDIR = 'C:\\Users\\Administrator\\Desktop\\Australia\\files'
for root, dirs, files in os.walk(BASEDIR):
    file_name = files[0]
    # print(type(file_name))
    print(file_name)
    file_dir = BASEDIR + '\\' + file_name
    # os.rename(file_name, 'invoice.pdf')
    invoice_url = requests.post(
        "https://visa.dllm.cn/index.php?s=/Business/Pcapi/insertpdf",
        files={"file": ('invoice.pdf', open(file_dir, 'rb'), "application/pdf")},
        timeout=10).json()


