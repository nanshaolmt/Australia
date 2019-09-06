#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File  : 测试.py
@Author: ChenLei
@Date  : 2019/7/22
"""
import re
import requests
from selenium import webdriver

req = webdriver.Chrome()
def index():

        print('正在执行登录...')
        index_url = 'https://www.windowmalaysia.my/evisa/vlno_verification_success.jsp?status=1&email=zenmh0816@163.com'

        res = req.get(index_url)
        print('请求主页...')

        reg = r'<input type="hidden" id="ipAddress" name="ipAddress" value="(.*?)"\s?/>'
        ipaddr = re.findall(reg, res.text)[0]
        print(ipaddr)
        # img = get_img(res)
        # answer = codeDemo(img)
        # # rsp = Captcha(1, img)
        # # answer = rsp.pred_rsp.value
        # print("验证码为:", answer)
        # if not answer:
        #     return 0
        # url = f'https://www.windowmalaysia.my/evisa/login?ipAddress={ipaddr}&txtEmail={self.email}&'\
        #     f'txtPassword={GLOBAL_DATA[4]}&answer={answer}&_={int(time.time()*1000)}'
        # res = self.req.get(url, timeout=10)
        # print(res.json().get("status"))
        # if res.json().get("status") == "conEstablished":
        #     return 0
        # elif res.json().get("status") == "fail":
        #     url_02 = "https://visa.dllm.cn/index.php?s=/Api/MalaysiaApi/getEmailStatus"
        #     data_02 = {"email": self.email, "status": "4"}
        #     requests.post(url_02, data_02, timeout=10)
        #     return 0
        # elif res.json().get("status") == "error":
        #     return 0
        # assert res.status_code == 200
        # return 1

if __name__ == '__main__':
    index()
