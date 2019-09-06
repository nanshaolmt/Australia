#!/usr/bin/env python
# coding: utf-8


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

class Selvisa(huilian_selenium.Huilian):
    mysql = Mysql()
    _tb_info = "dc_business_australia_info_eng"
    _tb_infoC = "dc_business_australia_info"
    _tb_visa = "dc_business_visa_account"

    def __init__(self, app_id=""):
        sql, val = self.asql.select_sql(tb=self._tb_info, cond={"status": 5} if not app_id else {"id": app_id})
        self.app = self.asql.getAll(sql, val)
        for i in self.app:
            self.id = i['id']
            self.application_id = i['application_id']
            self.mpid = i['mpid']
            self.fullName = i["username"].strip()  # 全名 - 中
            self.firstEName = i["english_name"].strip()  # 姓 - 英
            self.lastEName = i["english_name_s"].strip()  # 名 - 英
            self.application_status = i['application_status']
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
            # visa_account 信息
            visa_account = self.asql.getOne(*self.asql.select_sql(tb=self._tb_visa, cond={"mpid": self.mpid}))
            if visa_account['email_status'] == '1':
                self.userName = visa_account['official_account']  # 登陆账号
                self.password = visa_account['official_account_pass']  # 登陆密码
            else:
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
            if self.application_status == 5:
                self.send_keys((By.NAME, 'i_instantSearchFld'), self.application_id)
                self.click((By.NAME, 'btn_perform_instant_srch'), 2)
                self.click((By.ID, 'defaultActionPanel_0_3'), 2)
                self.pageSuc()
        except Exception as e:
            print(e)
            pass

    def pageSuc(self):
        print(f'查询{self.fullName}是否出签？')
        sleep(3)
        try:
            # 已出签
            if 'Granted' in self.page:
                self.click((By.ID, '_0a1a0c1a0a0b0a1a0b0-body'))
                text = self.find_element((By.ID, '_0a1a0c1a0a0b1a0c2-row-r0-_0a0b')).text
                sleep(2)
                if text == 'IMMI Grant Notification':
                    self.click((By.ID, '_0a1a0c1a0a0b1a0c2-row-r0-_0a0b'), 2)
                    self.click((By.ID, '_0a1a0c1a0a0b1a0c2-row-r0-_0a0a-dlg-_0b0b'), 2)
                else:
                    self.click((By.ID, '_0a1a0c1a0a0b1a0c2-row-r1-_0a0b'), 2)
                    sleep(4)
                    self.click((By.ID, '_0a1a0c1a0a0b1a0c2-row-r1-_0a0a-dlg-_0b0b'), 2)
                # if os.path.isdir(self.download_path):
                #     os.mkdir(self.download_path)
                #     sleep(3)
                receive_path = self.download_path + r'\application.pdf'
                sleep(5)
                receive_url = requests.post(
                    "https://visa.dllm.cn/index.php?s=/Business/Pcapi/insertpdf",
                    files={"file": ("application.pdf", open(receive_path, 'rb'), "application/pdf")},
                    timeout=10).json()
                print(receive_url)
                # 保存状态至数据库
                update_data = {
                    "status": 6,
                    "receive_url": receive_url,
                    "utime": int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.id}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
                print(f'{self.fullName}已出签')
                self.quit()
                return 0
            else:
                print(f'{self.fullName}未出签')
                self.quit()
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
        sql, val = mysql.select_sql(tb=TB_INFO, sel="COUNT(*) as c", cond={"status": 5})
        res = mysql.getOne(sql, val)
        if res['c']:
            Selvisa()
        else:
            print('没有数据, 等待中...', strftime('%m/%d %H:%M:%S'))


if __name__ == "__main__":
    # while 1:
    #     run()
    schedule.every().day.at("22:00").do(run)
    while 1:
        print('没到时间，等待中...', strftime('%m/%d %H:%M:%S'))
        schedule.run_pending()
        sleep(60 * 60)
        os.system('cls')

