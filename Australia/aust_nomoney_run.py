#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File  : aust_nomoney_run.py
@Author: ChenLei
@Date  : 2019/7/22
"""

import time

import schedule
from selenium.webdriver.common.by import By
from pipelines import Mysql
from settings import TB_INFO
import huilian_selenium
import os
from time import strftime
from selenium import webdriver
from time import sleep
from time import time
import settings
import requests
import shutil
import pub


class Selvisa(huilian_selenium.Huilian):
    mysql = Mysql()
    _tb_info = "dc_business_australia_info_eng"
    _tb_infoC = "dc_business_australia_info"
    _tb_visa = "dc_business_visa_account"

    def __init__(self, app_id=""):
        sql, val = self.asql.select_sql(tb=self._tb_info, cond={"status": 3} if not app_id else {"id": app_id})
        self.app = self.asql.getOne(sql, val)
        self.download_path = os.path.join(settings.BASEDIR, 'files')
        if os.path.isdir(self.download_path):
            shutil.rmtree(self.download_path)
        self.initParmar()
        # 设置 chrome_options 属性
        chrome_options = webdriver.ChromeOptions()
        # 设置浏览器窗口大小
        chrome_options.add_argument('window-size=1800x2000')
        # 无界面
        chrome_options.add_argument('--headless')
        # 不加载图片
        chrome_options.add_argument('blink-settings=imagesEnabled=false')
        chrome_options = huilian_selenium.chromeOptions(noWin=True, noImg=True, pdf=True)
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        self.driver.maximize_window()
        super().__init__(driver=self.driver)
        self.Login()

    # 信息，参数
    def initParmar(self):
        try:
            self.id = self.app['id']
            self.mpid = self.app['mpid']
            self.application_id = self.app['application_id']
            self.fullName = self.app["username"].strip()          # 全名 - 中
            self.application_status = self.app['application_status']
            # visa_account 信息
            visa_account = self.asql.getOne(*self.asql.select_sql(tb=self._tb_visa, cond={"mpid": self.mpid}))
            # if visa_account['email_status'] == 1:
            #     self.userName = visa_account['official_account']  # 登陆账号
            #     self.password = visa_account['official_account_pass']  # 登陆密码
            # else:
            self.userName = '180256122@qq.com'
            self.password = 'C5678tyui'
        except Exception as e:
            pass
            print(e)

    # 登录页面
    def Login(self):
        print('进入登录页面...')
        try:
            # get方法会一直等到页面加载，然后才会继续程序，通常测试会在这里选择# sleep(2)
            self.open("https://online.immi.gov.au/lusc/login")
            sleep(2)
            # 输入登陆用户名
            self.send_keys((By.NAME, 'username'), self.userName)
            # 输入登陆密码
            self.send_keys((By.NAME, 'password'), self.password)
            self.click((By.NAME, 'login'))
            if ">An error has occurred<" in self.page:
                return 0
            else:
                pass
            self.click((By.NAME, 'continue'), 2)
            self.send_keys((By.NAME, 'i_instantSearchFld'), self.application_id)
            self.click((By.NAME, 'btn_perform_instant_srch'), 2)
            if 'defaultActionPanel_0_3' in self.page:
                update_data = {
                    "status": 5,
                    "application_status": 5,
                    "utime": int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = (sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1])
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
                self.click((By.ID, 'defaultActionPanel_0_3'), 3)
                self.pageSuc()
            pass
        except Exception as e:
            print(e)
            self.quit()
            pass

    def pageSuc(self):
        print(f"进入付款成功页面")
        try:
            text = self.page
            text_required = text[text.rfind('Application home'):]
            text_required = text_required[text_required.find('<div id'):]
            requiredId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text_required)
            requirexp = f"//*[@id='{requiredId}']/div/div[2]/div/div/div"
            # 判断文件夹是否存在，如果没有则创建
            if not os.path.exists(self.download_path):
                os.mkdir(self.download_path)
                sleep(10)
            # 个人信息表，下载PDF文档
            self.click((By.XPATH, f'{requirexp}/table/tbody/tr[1]//a'), 2)
            sleep(6)
            # 文件名字
            info_name = self.download_path + '\\visa.pdf'
            # 文件重命名
            os.rename(os.path.join(self.download_path, 'Application'), info_name)
            sleep(1)
            # 浏览器开的窗口总数，下标从0开始
            windows = self.driver.window_handles
            # 去第二个窗口
            self.driver.switch_to.window(windows[1])
            # 关闭当前窗口
            self.close()
            sleep(1)
            my_info_url = requests.post(
                "https://visa.dllm.cn/index.php?s=/Business/Pcapi/insertpdf",
                files={"file": ("visa.pdf", open(info_name, 'rb'), "application/pdf")},
                timeout=10).json()

            update_data = {
                "my_info_url": my_info_url,
                "utime": int(time())
            }
            sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
            sqlc = (sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1])
            self.asql.update(*sqls)
            self.asql.update(*sqlc)
            sleep(1)
            return 0

        except Exception as e:
            print(e)
            self.quit()
            pass
            return 1

    # 数据库操作
    @property
    def asql(self):
        return Mysql()

def run():
        mysql = Mysql()
        sql, val = mysql.select_sql(tb=TB_INFO, sel="COUNT(*) as c", cond={"status": 3})
        res = mysql.getOne(sql, val)
        if res['c']:
            Selvisa()
        else:
            print('没有数据, 等待中...', strftime('%m/%d %H:%M:%S'))


if __name__ == "__main__":
    # while 1:
    #     run()
    schedule.every().day.at("21:00").do(run)
    while 1:
        print('没到时间，等待中...', strftime('%m/%d %H:%M:%S'))
        schedule.run_pending()
        sleep(60 * 60)
        os.system('cls')

