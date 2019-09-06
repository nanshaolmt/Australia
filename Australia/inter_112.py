#!/usr/bin/env python
# coding: utf-8
"""
@File   : inter_112_1_10.py
@Remarks: 澳大利亚签证系统
@Author : ZhaoBin
@Date   : 2018-12-15 14:58:31
@Last Modified by   : ZhaoBin
@Last Modified time : 2018-12-19 23:27:30
"""

import json
import os
import re
import shutil
import traceback
from datetime import datetime
from time import mktime, sleep, strftime, strptime, time
from selenium import webdriver
from selenium.webdriver.common.by import By
import config
import huilian_file_tools
import huilian_selenium
import pub
import settings
from pipelines import Mysql
import requests
from lxml import etree


# 主要用来测试selenium使用phantomJs
class Implement_class(huilian_selenium.Huilian):
    """
    澳大利亚签证系统
    """
    # userName = 'jiu20187745re@163.com'  # 登陆账号
    # userName = '180256122@qq.com'  # 登陆账号
    # password = 'C5678tyui'  # 登陆密码
    # kb = PyKeyboard()
    _tb_info = "dc_business_australia_info_eng"
    _tb_infoC = "dc_business_australia_info"
    _tb_order = "dc_business_australia_order"
    _tb_visa = "dc_business_visa_account"
    def __init__(self, id, extra="", steps="", app_id=""):
        # self.extra = extra
        # self.steps = steps
        self.logger = config.get_log(f"implement_{id}")
        #_tb_info = "dc_business_australia_info_eng" 又查了一次个人英文信息表  aust_run.py 已经查过了

        sql, val = self.asql.select_sql(tb=self._tb_info, cond={"status": 1} if not app_id else {"id": app_id})
        # 测试   查询具体的信息  SELECT * FROM dc_business_australia_info_eng WHERE status=%s  [1]
        # sql, val = self.asql.select_sql(tb=self._tb_info, cond={"id": 54})
        self.app = self.asql.getOne(sql, val)
        #----app  插叙的结果  字典类型
        params = {"logger": self.logger, "user": self.app.get("username", "陈小云")}
        # -----实例化   拆分字段
        self.Tools = huilian_selenium.Tools(**params)  #实例化一个TooLS对象
        #------图片转PDF  实例化一个类
        self.FileTools = huilian_file_tools.FileTools(**params)
        self.initParmar()
        self.app_id = self.app["id"]
        # 待上传文件本地存放根目录,各个国家可以在此基础上加上国家编码的下级文件夹  例如：E:\\visafile\\112\\
        self.local_path = os.path.join(config.BASE_FILE_DIR, "112", self.passport)
        # 判断返回的是否是文件夹/目录
        if os.path.isdir(self.local_path):
            # 用于递归删除目录/文件夹 == os.removedirs()
            shutil.rmtree(self.local_path)
        self.download_path = os.path.join(settings.BASEDIR, 'files')
        if os.path.isdir(self.download_path):
            shutil.rmtree(self.download_path)
        #chrome_options---# 不加载图片  可下载pdf
        chrome_options = huilian_selenium.chromeOptions(noWin=True, noImg=True, pdf=True)
        # chrome_path = r'C:\Program Files (x86)\Google\Chrome\Application\chromedriver'
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        # self.driver.maximize_window()
        #------把driver 封装到 父类属性中
        super().__init__(driver=self.driver, **params)
    # 签证信息 参数
    def initParmar(self):
        try:
            self.moreinfo = None
            self.stream = '29'  # 申请人的流   29旅游  31商务  30赞助家庭游   61频繁的旅行（商业目的）

            # 境外 -> 访问澳大利亚的所有理由  2:商业，3:旅游，4:探亲，5:研究，6:宗教活动，7:其他
            self.visitReason = self.app['all_reasons_access'][1:-1].split(",")
            # 澳大利亚期间重要时间节点
            # 境外 -> 请详细说明申请人需要在澳大利亚的任何重要日期
            self.significantDates = self.app['any_important_date']
            self.id = self.app["id"]
            #  公众号id   mpid
            self.mpid = self.app["mpid"]
            # 组 id: order_id
            self.order_id = self.app["order_id"]
            # 签证ID（Python专用）官网订单ID
            self.application_id = self.app['application_id']
            # 姓名 中-英
            self.fullName   = self.app["username"].strip()          # 全名 - 中
            self.firstEName = self.app["english_name"].strip()      # 姓 - 英
            self.lastEName  = self.app["english_name_s"].strip()    # 名 - 英
            #  查询  _tb_order = "dc_business_australia_order" 公共表 :在公共表中查询 个人信息表与它 关联的数据.    order_id 关联公共表的 字段.
            sql, param = self.asql.select_sql(tb=self._tb_order, sel="group_type", cond={"id": self.order_id})
            #group_type  签证小组 组类别 （1: 家庭 2: 学校/学习 3: 奖励旅游 4: 工作/雇主 5: 朋友 6: 其他 7: 娱乐 8: 运动队/体育赛事）

            #拿到签证小组的类别:  签证小组 组类别 （1: 家庭 2: 学校/学习 3: 奖励旅游 4: 工作/雇主 5: 朋友 6: 其他 7: 娱乐 8: 运动队/体育赛事）
            self.group_type = self.asql.getOne(sql, param).get("group_type")
            self.group_type = self.group_type if self.group_type else "1"
            #-----类型的就没有 1
            # 性别 1：男  2：女 3：其他
            self.sex = self.app["sex"]
            # 出生具体某一天日期
            #  修改---- for   循环 改为  列表推导式
            # birthday_list = []
            self.birthdays = (self.Tools.convertDateForAustralia(str(self.app["date_birth"])).split('-'))
            # for birthday in self.birthdays:
            #     birthday_day = int(birthday)
            #     birthday_list.append(birthday_day)
            birthday_list = [int(birthday) for birthday in self.birthdays ]
            '''把时间 年 月  日  添加到列表中[1944,3,1] 并且都为整型'''
            #  --[1944,3,1]
            # 1970年以前出生的时间戳转换 元组形势   (-6565,day,00:00:00)
            self.timestamp = (datetime(birthday_list[0], birthday_list[1], birthday_list[2]) - datetime(1970, 1, 1))
            y, m, d, h = [int(i) for i in strftime("%Y-%m-%d-%H").split("-")]
            # 是否是小孩 18
            self.is_child   = mktime(strptime(f'{y - 18}{m}{d}', "%Y%m%d")) - self.timestamp.total_seconds() <= 0
            if self.is_child:
                self.parent_id = "610623650"
            # 是否是老人 75
            self.is_old_man = (datetime(y - 75, m, d, h) - datetime(*[int(i) for i in self.app["date_birth"].split("-")])).days > 0
            self.passport = self.app['passport_number']  # 护照号码
            self.place_issue_country = self.app["place_issue_country"] #护照签发国家
            self.nationality = self.app["nationality"]
            self.passportStarTime = self.Tools.convertDateForAustralia(str(self.app['lssue_date']))  # 护照开始日期
            self.passportEndTime = self.Tools.convertDateForAustralia(str(self.app['expiration_date']))  # 护照开始日期
            self.passportProvince = self.app['place_issue_province'].strip()  # 护照发行省
            self.idCard = self.app["identity_number"]  # 身份证号
            self.idCardStarTime = self.Tools.convertDateForAustralia(str(self.app["id_lssue_date"]))  # 身份证开始时间
            self.idCardEndTime = self.Tools.convertDateForAustralia(str(self.app["id_expiration_date"]))  # 身份证结束时间
            # 3 place_of_birth
            self.city = self.app['date_city'].upper()  # 出生所在市
            self.birth_province = self.app["date_province"]  # 出生所在省
            self.country = self.app["date_country"]  # 出生国家
            # 3 relationship_status
            # F:同居 D:离婚 E:订婚 M:已婚 N:未婚 S:分居 W:丧偶
            self.relationshipStatus = self.app['marriage']
            # 3 other_names_spellings
            # 是否有曾用名  1是 2否
            self.nameUsedBefore = self.app['used_name_is']
            # 3 previous_travel_to_Australia
            # 此前曾前往澳大利亚或曾申请过签证吗  1是 2否  +后
            self.oldVisa = str(self.app['australia_oldis'] + 1)
            # 是否有以前曾经去过澳大利亚旅行的护照？ 1是 2否
            self.oldGoAustraliaPassport = str(self.app['australia_oldpassis'] + 1)  # 表中的是 0是 1否
            # 申请人有澳大利亚签证申请号吗？
            self.license_number_is = str(self.app["license_number_is"] + 1)
            self.license_number = self.app["license_number"]
            # 5是否有陪同人员
            self.peer_people = str(self.app["peer_people"] + 1)
            # 7 country_of_residence
            # 居住国家[PRCH类型]
            self.country_residence = self.app["country_residence"]
            # 7 department_office
            # 最近的面试办公室
            self.nearest_office = self.app["nearest_office"]
            # 7 residential_address
            # 住址国家
            self.live_country = self.app["live_country"]
            # 住址省份
            self.live_province = self.app["live_province"].strip()
            self.address = self.app['live_address'].upper()                     # 居住街道 住址详细地址(街道门牌号)
            self.postalCode = self.app['live_postal_code']                      # 邮编
            # 7 contact_telephone_numbers
            self.homePhone = self.app['home_phone'].replace('-', '')            # 家庭电话
            self.businessPhone = self.app['business_phone'].replace('-', '')    # 业务电话
            self.mobile = self.app['mobile_phone'].replace('-', '')             # 移动电话
            # 7 postal_address
            self.mailing_address_is = self.app["mailing_address_is"] + 1        # 邮件地址与居住地址是否一致?（0是1不是）
            self.mailing_country = self.app['mailing_country']                  # 国家
            self.mailing_address = self.app['mailing_address']                  # 邮件地址详细地址(街道门牌号)
            self.mailing_city = self.app['mailing_city']                        # 邮件地址城市
            self.mailing_province = self.app['mailing_province']                # 邮件州/省
            self.mailing_postal_code = self.app['mailing_postal_code']          # 邮件地址邮政编码
            # # 访问澳大利亚理由  1:商业，2:旅游，3:探亲，4:研究，5:宗教活动，6:其他
            # self.visitReason = int(self.app['visit_reason']) + 1

            # 8 authorised_recipient
            # 申请人是否授权他人代表他们收到书面信件？: (NO:没有, YES_MIGRATION_AGENT:是的/迁移代理, YES_ANOTHER_PERSON:是的/另一个人)
            self.collection_letter = self.app["collection_letter"]

            # 9 是否有非陪同人员
            #----调用
            self.together, self.no_together = self.get_together

            # 10 申请人是否打算不止一次进入澳大利亚？（1是2不是）
            self.entryCount = str(self.app["enter_multiple_is"] + 1)
            # 10 澳大利亚逗留时间 3: 3个月  6: 6个月 12: 12个月
            self.stayAusTime = self.app['further_stay_time']
            # 计划到达日期
            self.plannedArrivalDate = self.Tools.convertDateForAustralia(self.app['entry_time'])
            # 计划离开日期
            self.plannedFinalDepartureDate = self.Tools.convertDateForAustralia(self.app['departure_time'])
            # 申请人是否知道首次进入澳大利亚后每个场合的入境日期？
            self.occasion_entry = str(self.app["occasion_entry"] + 1)  #这个字段有点问题.
            # 不知道的理由(Give reason)
            self.occasion_entry_reasons = self.app["occasion_entry_reasons"]
            # 在澳大利亚期间会拜访任何亲戚，朋友或联系人吗？
            self.visit_relatives = str(self.app["visit_relatives"] + 1)
            if self.visit_relatives == '1':
                self.visit_rela_info = json.loads(self.app["visit_relatives_info"])

            # 12 就业状况 employment_status 就业     1 在职, 2 自我雇佣, 3 失业, 4 退休, 5 学生, 99 其他
            self.workType = self.app["employment_status"]
            if self.workType == "3":
                # 12 就业状况 3 失业
                self.unemploymentTime = self.Tools.convertDateForAustralia(self.app['unemployment_time'])  # 失业时间
                self.oldWrok = self.app['unemployment_job']  # 上一份工作
            elif self.workType == "4":
                # 12 就业状况 4 退休
                self.retirementTime = self.Tools.convertDateForAustralia(self.app['retirement_time'])  # 退休时间
            elif self.workType == "99":
                # 12 就业状况 99 其它-原因
                self.workDeatil = self.app['employment_other']  # 工作详情
            # 13 资金来源
            self.financialType = self.app["tourism_funding_who"]
            self.supportType = self.app['tourism_funding_type']
            self.financialDetail = self.app['tourism_funding']  # 资金详情

            # 16 在过去五年中，是否有申请人连续三个月访问或居住在护照国境外？ 默认否
            self.country_stay_other = str(self.app["country_stay_other"] + 1)

            # 18 是否持有澳大利亚或其他任何国家的签证？（0是1不是)
            self.other_visa_is = str(self.app["other_visa_is"] + 1)
            if self.other_visa_is == '1':
                self.other_visa_info    = self.app["other_visa_info"]
            # 18 是否曾在澳大利亚或其他任何国家逗留时间超时？（0是1不是）
            self.stay_timeout_is = str(self.app["stay_timeout_is"] + 1)
            if self.stay_timeout_is == '1':
                self.stay_timeout_info  = self.app["stay_timeout_info"]
            # 18 是否有过在澳大利亚或其他任何国家被拒绝签证或取消？（0是1不是）)
            self.refuse_visa_is = str(self.app["refuse_visa_is"] + 1)
            if self.refuse_visa_is == '1':
                self.refuse_visa_info   = self.app["refuse_visa_info"]

            # visa_account 信息   查询公共表的信息.
            visa_account = self.asql.getOne(*self.asql.select_sql(tb=self._tb_visa, cond={"mpid": self.app["mpid"]}))


            #  official_account_status   就业状况(1在职、2自我雇佣、3失业、4退休、5学生、99其他)
            if visa_account['official_account_status'] == 1:
                self.userName = visa_account['official_account']  # 登陆账号
                self.password = visa_account['official_account_pass']  # 登陆密码
            else:
                self.userName = '180256122@qq.com'
                self.password = 'C5678tyui'  # C5678tyui
            #判断(payment_card_status)支付卡状态   1使用  2不使用
            if visa_account["payment_card_status"] is 1:
                #这些都是支付的信息.
                self.pay_cord = visa_account["payment_card"]
                self.pay_year, self.pay_month, _ = visa_account["payment_card_time"][2:].split("-")
                self.pay_name = visa_account["payment_card_name"]
                self.pay_cvv = visa_account["payment_card_cvv"]
            else:
                visa_account = self.asql.getOne(*self.asql.select_sql(tb=self._tb_visa, cond={"mpid": 44}))
                #-----做了修改  ["payment_card"],改为
                self.pay_cord = visa_account.get("payment_card",None)

                self.pay_year, self.pay_month, _ = visa_account["payment_card_time"][2:].split("-")
                self.pay_name = visa_account["payment_card_name"]
                self.pay_cvv = visa_account["payment_card_cvv"]


        except BaseException as e:
            # self.errinfo()
            update_data = {
                'ques': str(e),
                'status': 4,
                'utime': int(time())
            }

            sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
            sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
            self.asql.update(*sqls)

            # -------sqls 拿到的是元组,并且这个数据,sql,val 值.
            self.asql.update(*sqlc)
            #执行sql 并没有走.
            sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            # self.driver.quit()
            return 1


    @property
    def get_together(self):
        """判断有没有非同行人员
        @return : (togs: list, no_togs: list)
        """
        togs = []       # 同行人员
        no_togs = []    # 不同行人员

        # 配偶
        spouse_info = {
            "rela": "3",
            "name": self.app["spouse_name_eng"],
            "names": self.app["spouse_names_eng"],
            "sex": "M" if self.app["sex"] == "F" else "F",
            "birth": self.Tools.convertDateForAustralia(self.app["spouse_birth"]),
            "country": self.app["spouse_birth_country"],
        }
        if not self.app["spouse_together"]:  # 代表啥   1  ，0
            togs.append(spouse_info)
        elif min(self.app["spouse_name_eng"], self.app["spouse_names_eng"], self.app["spouse_birth"], self.app["spouse_birth_country"]):
            no_togs.append(spouse_info)
        pass

        # 父亲
        father_info = {
            "rela": "2",
            "name": self.app["father_name_eng"],
            "names": self.app["father_names_eng"],
            "sex": "M",
            "birth": self.Tools.convertDateForAustralia(self.app["father_birth"]),
            "country": self.app["father_birth_country"],
        }
        if not self.app["father_together"]:
            togs.append(father_info)
        elif min(self.app["father_name_eng"], self.app["father_names_eng"], self.app["father_birth"], self.app["father_birth_country"]):
            no_togs.append(father_info)
        pass
        # 母亲
        mother_info = {
            "rela": "2",
            "name": self.app["mother_name_eng"],
            "names": self.app["mother_names_eng"],
            "sex": "F",
            "birth": self.Tools.convertDateForAustralia(self.app["mother_birth"]),
            "country": self.app["mother_birth_country"],
        }
        if not self.app["mother_together"]:
            togs.append(mother_info)
        elif min(self.app["mother_name_eng"], self.app["mother_names_eng"], self.app["mother_birth"], self.app["mother_birth_country"]):
            no_togs.append(mother_info)
        pass

        # 兄弟姐妹
        if not self.app["brothers_sisters_is"]:
            brothers = pub.is_json(self.app["brothers_sisters_info"])
            for i in brothers:
                borther_info = {
                    "rela": "35" if i["sex"] == "M" else "36",
                    "name": i["name_eng"],
                    "names": i["names_eng"],
                    "sex": i["sex"],
                    "birth": self.Tools.convertDateForAustralia(i["birth_date"]),
                    "country": i["birth_country"],
                }
                if not int(i["together"]):
                    togs.append(borther_info)
                elif min(i["sex"], i["name_eng"], i["names_eng"], i["birth_date"], i["birth_country"]):
                    no_togs.append(borther_info)
                pass
            pass
        pass

        # 子女
        if not self.app["children_is"]:
            children = pub.is_json(self.app["children_info"])
            for i in children:
                children_info = {
                    "rela": "1",
                    "name": i["name_eng"],
                    "names": i["names_eng"],
                    "sex": i["sex"],
                    "birth": self.Tools.convertDateForAustralia(i["birth_date"]),
                    "country": i["birth_country"],
                }
                if not int(i["together"]):
                    togs.append(children_info)
                elif min(i["sex"], i["name_eng"], i["names_eng"], i["birth_date"], i["birth_country"]):
                    no_togs.append(children_info)
                pass
            pass
        pass

        # 其它
        if not self.app["other_relatives_is"]:
            others = pub.is_json(self.app["children_info"])
            for i in others:
                others_info = {
                    "rela": i["applicant"],
                    "name": i["name_eng"],
                    "names": i["names_eng"],
                    "sex": i["sex"],
                    "birth": self.Tools.convertDateForAustralia(i["birth_date"]),
                    "country": i["birth_country"],
                }

                if not int(i["together"]):
                    togs.append(others_info)
                elif min(i["applicant"], i["sex"], i["name_eng"], i["names_eng"], i["birth_date"], i["birth_country"]):
                    no_togs.append(others_info)
                pass
            pass
        pass
        return togs, no_togs

    # 数据库操作
    @property
    def asql(self):
        return Mysql(logger=self.logger)

    # 输出日志
    def log(self, info="", debug="", error=""):
        # return
        if info:
            self.logger.info(f"{self.fullName} {info}")
        elif debug:
            self.logger.debug(f"{self.fullName} {debug}")
        elif error:
            self.logger.error(f"{self.fullName} {error}")

    # 从页面获取 _2a0b0a0a0e0a0a1a6c0a0 st1, "<input", "</span>"
    def find_page(self, strs=None, name=1):
        page = self.page
        text1 = page.split(strs[0])[-1]
        text2 = text1[text1.find(strs[1]):].split(strs[2])[0]
        s = "name" if name else "id"
        return pub.get_reg_value(fr'(?<={s}=").*?(?=")', text2)


    # 登录页面
    def Login(self):
        try:
            # get方法会一直等到页面加载，然后才会继续程序，通常测试会在这里选择# sleep(2)
            self.open("https://online.immi.gov.au/lusc/login")
            #启动后睡多长时间合适.
            sleep(2)
            # 输入登陆用户名
            self.log(f"登陆: {self.userName}")

            self.send_keys((By.NAME, 'username'), self.userName)
            # 输入登陆密码
            self.send_keys((By.NAME, 'password'), self.password)
            self.click((By.NAME, 'login'))
            self.click((By.NAME, 'continue'), 2)

            # 新增订单

            print('472------inter',self.application_id)
            print('473------inter',self.Tools.is_empty(self.application_id))
            if self.Tools.is_empty(self.application_id):
                self.click((By.NAME, 'btn_newapp'), 2)
                sleep(1)
                #点击访客
                self.click((By.ID, "mainpanel_parentSection_1b0a0bd0-body"))
                # if self.attr(self.find_element_by_id("mainpanel_parentSection_1b0a0bd-content"), "aria-expanded") == "false":
                # self.click((By.ID, 'mainpanel_parentSection_1b0a0bd-content'))
                sleep(2)
                # else:
                #     self.js_execute('document.getElementById("mainpanel_parentSection_1b0a0bd-content").setAttribute("aria-expanded", true)')
                # 国境签证页面（771）
                # self.click((By.ID, "mainpanel_parentSection_1b0a0bd1c0-body"))
                # 访客签证（600）
                self.click((By.ID, "mainpanel_parentSection_1b0a0bd1d0-body"))
                self.page1()
                sleep(1)
                # 如果没有订单号   就查询并保存订单号
                self.click((By.XPATH, '//button[@title="Link to account page" and @type="submit"]'), 2)
                text = self.page
                with open('wy.html','w',encoding='utf-8') as f:
                    f.write(text)
                # with open('song.txt', 'r', encoding='utf-8') as f:
                #     print(f.read(12))


                index = text.find('Reference No')
                text1 = text[index: index + 500]
                index = text1.find('<div class="wc-input">')
                index2 = text1.find('</div>')
                text1 = text1[index + 22: index2]
                self.application_id = text1
                logger = config.get_log("application_id")
                logger.info(f"application_id: {self.application_id}")
                self.logger.info(f"application_id: {self.application_id}")
                # 保存状态至数据库 生成 application_id
                update_data = {
                    "application_id": self.application_id,
                    "application_status": 1,
                    "utime": int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
                self.click((By.ID, 'defaultActionPanel_0_1'), 2)
                return 1
            else:

                #订单号（Python 专用）0初始 1已有订单 2上传文件 3待付款 5付款成功

                self.log(f"已有订单: {self.application_id}")
                self.send_keys((By.NAME, 'i_instantSearchFld'), self.application_id)
                self.click((By.NAME, 'btn_perform_instant_srch'), 2)

                if self.app['application_status'] == 1:
                    self.log(f"填写信息")
                    self.click((By.ID, 'defaultActionPanel_0_1'), 2)
                    return 1
                elif self.app['application_status'] == 2:
                    self.log(f"上传文件")
                    if self.find_element((By.CSS_SELECTOR, "button[id^='defaultActionPane']")).text == "Attach documents":
                        self.click((By.ID, 'defaultActionPanel_0_0'), 2)
                        return 2
                    elif self.find_element((By.CSS_SELECTOR, "button[id^='actionPanel_0_9']")).text == "Submit":
                        self.log(f"进入确认提交付款页面")
                        self.click((By.ID, 'actionPanel_0_9'), 2)
                        self.click((By.ID, "confirmBtn"), 2)
                        return 3
                    else:
                        self.click((By.ID, "actionPanel_0_10"), 2)
                        return 2
                elif self.app['application_status'] == 3:
                    self.log(f"付款")
                    self.click((By.ID, 'actionPanel_0_9'), 2)
                    self.click((By.ID, 'confirmBtn'), 2)
                    return 3
                elif self.app['application_status'] == 5:
                    self.log(f"付款成功")
                    self.click((By.ID, 'defaultActionPanel_0_3'), 2)
                    return 5
                else:
                    self.driver.quit()
                    return -1
                pass
            pass
        except BaseException as e:
            self.driver.quit()
            return 0
    pass

    # 第一页填写内容
    def page1(self):
        self.log(f"进入第一页")
        sleep(1)
        try:
            # sleep(2)
            text = self.page
            # 我已阅读并同意条款和条件
            index = text.find('I have read and agree to the terms and conditions')
            text = text[:index]
            index = text.rfind('<label')
            text = text[:index]
            index = text.rfind('<input')
            text = text[index:]
            # 阅读条款
            ids = pub.get_reg_value(r'(?<=input id=").*?(?=")', text)
            if self.is_clickable_time((By.ID, ids)):
                inp = self.find_element((By.ID, ids))
                if not inp.is_selected():
                    inp.click()
            # 下一步按钮为动态 需要截取字符串获取
            #------第一页的 下一步定位错误。更改
            # self.click((By.XPATH, "//span[text()='Next']"))  //*[@id="_2a0bc0a0a0g1"]/span/span/font/font
            self.click((By.XPATH, '//*[@id="_2a0bc0a0a0g1"]'))
            # sleep(1)
            # self.page2()
            return 0

        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass


    # 第二页填写内容
    def page2(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Application context")
            self.log(f"{self.fullName} 第一页必要信息未齐全")
            return 1
        self.log(f"进入第二页")
        try:
            text1 = text[:text.find('Application context')]
            text1 = text1[text1.rfind('<div id='):]
            titleId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text1)
            titleId2 = titleId[:-1]

            # baxp = f"//*[@id='{titleId2}']/div/div"

            hid_id = self.attr(self.find_element((By.CSS_SELECTOR, f"#{titleId2}>div>div:nth-of-type(3)")))
            js = f'document.getElementById("{hid_id}").removeAttribute("hidden")'
            self.js_execute(js)

            text2 = text.split('Is the applicant currently outside Australia?')[-1]
            text2 = text2.split('Yes', 1)[0]
            testid = text2.split('id="')[-1].split('"')[0]
            # 申请人是否在澳大利亚外  选择是
            self.click((By.ID, testid))
            sleep(1)
            # 选择申请类型  默认选第一个 旅游类型
            if self.is_clickable_time((By.XPATH, '//input[@value="' + self.stream + '"]')):
                inp = self.find_element((By.XPATH, '//input[@value="' + self.stream + '"]'), 2)
                if inp.is_displayed():
                    inp.click()

            # 当前国家
            self.select_by_value((By.CSS_SELECTOR, '.ELP-F4257>select[id$="input"]'), 'PRCH')
            # 申请人所在申请地的法律地位  默认选1 公民
            self.select_by_value((By.CSS_SELECTOR, '.ELP-F4258>select[id$="input"]'), '1')
            sleep(1)
            # self.click((By.XPATH,'//*/input[@name="'+testName+'" and @value="'+self.stream+'"]'))
            # [i.click() for i in self.find_elements((By.CSS_SELECTOR, 'button[title="Remove item. Shift + click remove button to remove all."]'), 1)]
            # 访问澳大利亚的所有理由 选择旅游
            for i, v in enumerate(self.visitReason):
                self.click((By.CSS_SELECTOR, 'button[title="Add item"]')) if i else ""
                self.select_by_value((By.CSS_SELECTOR, 'ul>li:first-child>select'), str(int(eval(v))))
            # 详细说明申请人在澳大利亚重要日期
            self.send_keys((By.CSS_SELECTOR, ".ELP-F3767>textarea"), f"{self.significantDates}") if self.significantDates else ""
            # 这个应用程序是作为一组应用程序的一部分提交的吗？默认选否
            text = self.page
            page = text.split("Is this application being lodged as part of a group of applications?")[-1]
            page = page[page.find("<label"):].split("</label>", 2)
            group_name = pub.get_reg_value(r'(?<=name=").*?(?=")', page[0])

            # 查询是否为组
            # sql = self.asql.select_sql(tb=self._tb_info, cond="order_id=%s")
            # if self.asql.getNum(sql, self.order_id) > 1:
            #     order_sql = self.asql.select_sql(
            #         tb=self._tb_order,
            #         sel="group_num",
            #         cond="id=%s"
            #     )
            #     group_num = self.asql.getOne(order_sql, self.order_id).get("group_num")
            #     if not group_num or group_num not in self.page:
            #         self.click((By.XPATH, f'//*/input[@name="{group_name}" and @value="1"]'), 2)
            #         page2 = page[2].split("Select group")[0]
            #         group_btn = page2[int(page2.find("<button")):]
            #         group_btn_id = pub.get_reg_value(r'(?<=id=").*?(?=")', group_btn)
            #         self.click((By.ID, group_btn_id))
            #         self.find_element((By.XPATH, "//*[text()='Has the group already been created?']"))
            #         # 组名是否已经存在
            #         text = self.page
            #         page_group = text.split("Has the group already been created?<")[-1]
            #         page_split = page_group[page_group.find("<label"):].split("</label>", 2)
            #         page_input = page_split[0]
            #         page_other = page_split[2]
            #         group_input_name = pub.get_reg_value(r'(?<=name=").*?(?=")', page_input)
            #         if group_num and len(group_num) > 5:
            #             # 有组名, 查询
            #             group_id_page = page_split[2]
            #             self.click((By.XPATH, f'//*/input[@name="{group_input_name}" and @value="1"]'), 2)
            #             # 组 Group ID 输入
            #             group_id_span = group_id_page[group_id_page.find("Group ID"):]
            #             group_id_span2 = group_id_span[group_id_span.find("<input"):].split("</span>")[0]
            #             group_id_input = pub.get_reg_value(r'(?<=name=").*?(?=")', group_id_span2)
            #             self.send_keys((By.CSS_SELECTOR, f'#{group_id_input}>input'), group_num)
            #             confirm_btn = page_other[:page_other.find("Confirm")].split("<button")[-1]
            #             confirm = pub.get_reg_value(r'(?<=id=").*?(?=")', confirm_btn)
            #             self.click((By.ID, confirm))
            #         else:
            #             # 无组名, 创建
            #             self.click((By.XPATH, f'//*/input[@name="{group_input_name}" and @value="2"]'), 2)
            #             # 输入组名 英文姓+签证类型
            #             g_n1 = page_other.split("Group name")[-1]
            #             g_n2 = g_n1[g_n1.find("<input"):].split("</span>")[0]
            #             g_n_id = pub.get_reg_value(r'(?<=id=").*?(?=")', g_n2)
            #             self.send_keys((By.ID, g_n_id), self.firstEName + self.stream)
            #             # 选择组类型
            #             g_t1 = page_other.split("Group type")[-1]
            #             g_t2 = g_t1[g_t1.find("<select"):].split("</span>")[0]
            #             g_t_id = pub.get_reg_value(r'(?<=id=").*?(?=")', g_t2)
            #             self.select_by_value((By.ID, g_t_id), self.group_type)
            #             confirm_btn = page_other[:page_other.find("Confirm")].split("<button")[-1]
            #             confirm = pub.get_reg_value(r'(?<=id=").*?(?=")', confirm_btn)
            #             self.click((By.ID, confirm))
            #
            #             # 保存组名
            #             text = self.page.split("Group ID")[1]
            #             group_id = pub.get_reg_value(r'(?<= value=").*?(?=")', text)
            #             sql = self.asql.update_sql(
            #                 tb=self._tb_order,
            #                 cond={"id": self.app["order_id"]},
            #                 group_num=group_id,
            #                 utime=int(time())
            #             )
            #             self.asql.update(*sql)
            #         pass
            #     pass
            # else:
            self.click((By.XPATH, f'//*/input[@name="{group_name}" and @value="2"]'), 2)
            pass
            self.busy
            page = text.split("Is the applicant travelling as a representative of a foreign government, or travelling on a United Nations Laissez-Passer, or a member of an exempt group?")[-1]
            page = page[page.find("<label"):].split("</label>", 2)
            group_name = pub.get_reg_value(r'(?<=name=").*?(?=")', page[0])
            self.click((By.XPATH, f'//*/input[@name="{group_name}" and @value="2"]'), 2)

            # 下一步
            self.click((By.XPATH, "//span[text()='Next']"))
            # sleep(1)
            # self.page3()
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第三页填写内容
    def page3(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Applicant")
            self.log(f"{self.fullName} 第二页必要信息未齐全")
            return 1
        self.log(f"进入第三页")
        try:
            requires = re.findall(r'<script type=[\'"]text/javascript[\'"] class=[\'"]registrationScripts[\'"]>(.*?)</script>', text)[0].replace(" ", "")
            con = json.loads(re.findall(r"c\.register\((.*?)\);", requires)[0])[0]
            index = text.find('Applicant')
            text = text[:index]
            index = text.rfind('<div id=')
            text = text[index:]
            titleId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)
            titleId = titleId[:-1]

            # basexp = f"//*[@id='{titleId}']/div/div"

            all_page = {
                "national_identity_card": 8,
                "place_of_birth": 9,
                "relationship_status": 11,
                "other_names_spellings": 12,
                "citizenship": 13,
                "previous_travel_to_Australia": 14,
                "grant_number": 14,
                "other_passports": 15,
                "other_identity_documents": 16,
                "health_examination": 18
            }

            names = con.replace(titleId, "")
            two = names[:2]
            oth = names[2:]

            # 姓
            self.send_keys((By.CSS_SELECTOR, f"[name^={titleId + pub.fmst(two, -37, 0) + pub.fmst(oth, 1, 0)}]"), self.firstEName)
            # 名
            self.send_keys((By.CSS_SELECTOR, f"[name^={titleId + pub.fmst(two, -37, 0) + pub.fmst(oth, 2, 0)}]"), f"{self.lastEName}") if self.lastEName else ""
            # 性别(男)
            self.click((By.XPATH, f'//input[@type="radio" and @value="{self.sex}"]'), 2)
            # 出生日期
            self.send_keys((By.NAME, titleId + pub.fmst(two, -35, 0) + oth), self.birthdays)
            # 护照号码
            self.send_keys((By.NAME, titleId + pub.fmst(two, -1, 0) + oth), self.passport)
            # 护照国家
            self.select_by_value((By.NAME, titleId + two + oth), self.place_issue_country)
            # 护照持有人国籍
            self.select_by_value((By.NAME, titleId + pub.fmst(two, 1, 0) + oth), self.nationality)
            # 护照发行日期
            self.send_keys((By.NAME, titleId + pub.fmst(two, 2, 0) + oth), self.passportStarTime)
            # 护照到期日期
            self.send_keys((By.NAME, titleId + pub.fmst(two, 3, 0) + oth), self.passportEndTime)
            # 护照发行省
            self.select_by_value((By.CSS_SELECTOR, f"[name^={titleId + pub.fmst(two, 4, 0) + oth}]"), self.passportProvince)
            # self.select_visibility_by_text((By.CSS_SELECTOR, f"[name^={titleId + pub.fmst(two, 4, 0) + oth}]"), self.passportProvince)
            # =============================== #
            # ==== national_identity_card === #
            # 是否有中国身份证
            self.click((By.CSS_SELECTOR, f'[name^={titleId + pub.fmst(names, 0, 0)}][value="1"] '), 2)
            locator = (By.XPATH, f"//*[@id='{titleId}']/div/div[9]//button")
            self.delete_btn(locator)

            self.find_elements(locator)[-1].click()
            # sleep(1)
            self.addIdCard()
            if ">An error has occurred<" in text:
                self.errinfo("Applicant")
                self.log(f"{self.fullName} 添加身份证页必要信息未齐全")
                return 1
            index = text.find('Applicant')
            text = text[:index]
            index = text.rfind('<div id=')
            text = text[index:]
            titleId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)
            titleId3 = titleId[:-1]

            # ======================== #
            # ==== place_of_birth ==== #
            attr = " .wc-content .wc-content>div"
            labels = self.get_labels(titleId3, all_page["place_of_birth"], attr)
            # 城镇
            self.elem_send_keys(labels[1].find_element_by_tag_name("input"), self.city)
            # 省份
            self.elem_send_keys(labels[2].find_element_by_tag_name("input"), self.birth_province)
            # 国籍
            self.select_has_element(labels[3].find_element_by_tag_name("select"), value='PRCH')

            # ============================= #
            # ==== relationship_status ==== #
            attr = " select"
            labels = self.get_labels(titleId3, all_page["relationship_status"], attr)
            # 婚姻状态
            self.select_has_element(labels[0], value=self.relationshipStatus)

            # =============================== #
            # ==== other_names_spellings ==== #
            attr = " .wc-content .wc-option input"
            labels = self.get_labels(titleId3, all_page["other_names_spellings"], attr)
            # 是否有其他名字
            self.log(f"是否有其它名字: {'是' if not self.nameUsedBefore else '否'}")
            # 如果有   则添加曾用名
            if not self.nameUsedBefore:
                labels[0].click()
                attr_btn = " button"
                label_btn = self.get_labels(titleId3, all_page["other_names_spellings"], attr_btn)
                for i in label_btn[1::2]:
                    i.click()
                    self.driver.switch_to.alert.accept()
                nameOld = json.loads(self.app["used_name"])
                for nameBefore in nameOld:
                    self.get_labels(titleId3, all_page["other_names_spellings"], attr_btn)[-1].click()
                    # 曾用姓
                    self.send_keys((By.XPATH, "//fieldset/div[2]/div/div[1]//input"), nameBefore["name_eng"])  # 曾用姓
                    # 曾用名
                    self.send_keys((By.XPATH, "//fieldset/div[2]/div/div[2]//input"), nameBefore["names_eng"])  # 曾用名
                    # 修改原因  D契约民意调查  M婚姻 O其他
                    self.select_by_value((By.CSS_SELECTOR, 'fieldset select'), nameBefore["name_change"])
                    # 如果修改原因选择其他  则填写详细信息
                    if nameBefore["name_change"] == 'O':
                        # sleep(1)
                        self.send_keys((By.CSS_SELECTOR, 'fieldset textarea'), nameBefore["give_details"])  # 详细说明修改原因
                    pass
                    self.click((By.XPATH, '//button[text()="Confirm"]'), 2)
                pass
                # sleep(1)
            else:
                labels[1].click()
            pass

            # ==================================== #
            # =========== citizenship ============ #
            labels = self.get_labels(titleId3, all_page["citizenship"], ">div>div")
            # 是否是中国公民
            labels[1].find_element(By.XPATH, f".//input[@value='{1}']").click()
            # 申请人是否是其他国家的公民？
            labels[2].find_element(By.XPATH, f".//input[@value='{2}']").click()

            # ==================================== #
            # === previous_travel_to_Australia === #
            labels = self.get_labels(titleId3, all_page["previous_travel_to_Australia"], ">div>div")
            # 此申请人此前曾前往澳大利亚吗？
            if self.oldVisa == '1':
                labels[1].find_element(By.XPATH, f".//input[@value='{self.oldVisa}']").click()
            else:
                labels[1].find_element(By.XPATH, f".//input[@value='{self.oldVisa}']").click()
            # 此申请人之前申请过澳大利亚签证吗？
            if self.oldGoAustraliaPassport == 1:
                labels[2].find_element(By.XPATH, f".//input[@value='{self.oldGoAustraliaPassport}']").click()
            else:
                labels[2].find_element(By.XPATH, f".//input[@value='{self.oldGoAustraliaPassport}']").click()

            # ==================================== #
            # ========= grant_number ========== #
            # 该申请人是否有澳大利亚签证许可号码？
            labels[3].find_element(By.XPATH, f".//input[@value='{2}']").click()

            # ==================================== #
            # ========= other_passports ========== #
            attr = " input[type=radio]"
            labels = self.get_labels(titleId3, all_page["other_passports"], attr)
            # 申请人有其他护照吗？默认填没有
            if "NoOldPassport":
                labels[1].click()
            else:
                labels[0].click()

            # ==================================== #
            # === other_identity_documents ======= #
            labels = self.get_labels(titleId3, all_page["other_identity_documents"], attr)
            # 申请人是否有其他身份证明文件？
            if "NoOtherIdentityDocuments":
                labels[1].click()
            else:
                labels[0].click()

            # ==================================== #
            # ======= health_examination ========= #
            labels = self.get_labels(titleId3, all_page["health_examination"], attr)
            # 申请人是否在过去12个月为澳大利亚签证进行体检？
            if "NoHealthExamination":
                labels[1].click()
            else:
                labels[0].click()
            # 体检详情
            self.click((By.XPATH, "//*[text()='Next']"))  # 下一步到第四页
            # sleep(1)
            # self.page4()
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第四页填写内容
    def page4(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Critical data confirmation")
            self.log(f"{self.fullName} 第三页必要信息未齐全")
            return 1
        self.log(f"进入第四页")
        try:
            # 确认信息是否正确
            self.click((By.XPATH, '//input[@type="radio" and @value="1"]'), 2)
            self.click((By.XPATH, "//*[text()='Next']"))  # 下一步到第五页
            sleep(2)
            if 'Warning!' in self.page:
                res = json.loads(requests.get(settings.PAY_API.format(122, 44)))
                if res['code'] == 0:
                    ques = res['info']
                    update_data = {
                        "status": 7,
                        "ques": ques,
                        "utime": int(time())
                    }
                    sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                    sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                    self.asql.update(*sqls)
                    self.asql.update(*sqlc)
                    # 关闭浏览器
                    self.driver.quit()
                    #
                else:
                    pass
            else:
                self.page5()
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                self.asql.update(*sqls)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第五页填写内容
    def page5(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Travelling companions")
            self.log(f"{self.fullName} 第四页必要信息未齐全")
            return 1
        self.log(f"进入第五页")
        try:
            index = text.find('Travelling companions')
            text = text[index:]
            titleId5 = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)[:-1]
            baxp = f'//*[@id="{titleId5}"]/div/div'
            while 1:
                if "Delete" in self.page:
                    self.click((By.XPATH, '//button[text()="Delete"]'), 2)
                    self.driver.switch_to.alert.accept()
                else:
                    break
            if self.peer_people == '1':
                self.click((By.XPATH, f'{baxp}[4]//input[@value="{self.peer_people}"]'), 2)
                # self.click((By.XPATH, f'{baxp}[5]//button'), 2)  # 点击添加按钮
                # self.addTravellingCompanion()
                self.peer_people_info = json.loads(self.app["peer_people_info"])
                for i in self.peer_people_info:
                    for _ in range(10):
                        if "Travelling companions" in self.page:
                            self.click((By.XPATH, f'{baxp}[5]/div/button'), 2)  # 点击添加按钮
                            sleep(0.1)
                    for _ in range(10):
                        if "Travelling companion" in self.page:
                            break
                        sleep(0.1)

                    text = self.page
                    index = text.find('Travelling companion')
                    text = text[:index]
                    index = text.rfind('<fieldset id="')
                    text = text[index:]
                    labId = pub.get_reg_value(r'(?<=fieldset id=").*?(?=")', text)
                    labxp = f"//*[@id='{labId}']/div"
                    self.busy
                    # 姓                                                                                  
                    self.send_keys((By.XPATH, f"{labxp}[3]/div/div[1]/div/div[1]//input"), i["name_eng"])
                    # 名
                    self.send_keys((By.XPATH, f"{labxp}[3]/div/div[1]/div/div[2]//input"), i["names_eng"])
                    # 性别
                    self.click((By.XPATH, f"{labxp}[3]/div/div[2]//input[@value='{i['sex']}']"))
                    # 生日
                    self.send_keys((By.XPATH, f"{labxp}[3]/div/div[3]//input"),
                                   self.Tools.convertDateForAustralia(i["birth_date"]))
                    # 关系
                    self.select_by_value((By.XPATH, f"{labxp}[2]//select"), i["applicant"])
                    # 下一步返回第五页
                    self.click((By.XPATH, '//button[text()="Confirm"]'), 2)
                text = self.page
                if ">An error has occurred<" in text:
                    self.errinfo("Travelling companions")
                    self.log(f"{self.fullName} 添加同行页面必要信息未齐全")
                    return 1
            else:
                self.click((By.XPATH, f'{baxp}[4]//input[@value="{self.peer_people}"]'), 2)
            sleep(1)
            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第六页
            return 0
            """
                guardian_is     申请人是否与父母或法定监护人一起旅行？（0是1不是）（儿童）
                guardian_info   法定监护人信息 （
                                            applicant 关系
                                            name 中文姓
                                            names 中文名
                                            name_eng 拼音姓
                                            names_eng 拼音名
                                            sex 性别
                                            birth_date 出生日期
                                            passport 护照号
                                            country 护照持有人的国籍[CHN类型下拉框]
                                            publish_time 发行日期
                                            expire_date 到期日期
                                            place_issue 护照签发省[下拉框]
                                            passport_country 护照的国家[CHN类型下拉框]
                                        ）
                guardian_notgo  reason 申请人在没有父母或法定监护人的情况下旅行的原因 、information 详细说明
            """
            # 是否是小孩
            if self.is_child:
                self.guardian_is = str(self.app["guardian_is"] + 1)
                self.click((By.XPATH, f'{baxp}[3]//input[@value="{self.guardian_is}"]'))
                # 没有家人陪同
                if self.guardian_is == "2":
                    self.guardian_notgo = json.loads(self.app["guardian_notgo"])
                    self.click((By.XPATH, f'{baxp}[3]//input[@value="{self.guardian_notgo["reason"]}"]'))
                    # 其它原因
                    if self.guardian_notgo["reason"] == "5":
                        self.send_keys((By.XPATH, f'{baxp}[3]//textarea'), self.information)
                    pass
                # 有家人陪同 | 有
                if self.guardian_is == "1" or (self.guardian_is == "2" and self.guardian_notgo["reason"] == "1"):
                    self.guardian_info = json.loads(self.app["guardian_info"])
                    locator = (By.XPATH, f"{baxp}[3]//button")
                    addId = self.delete_btn(locator)
                    for i in self.guardian_info:
                        for _ in range(30):
                            if "Travelling companions" in self.page:
                                self.click((By.ID, addId))
                            # if "Responsible person details" in self.page:
                            if "Travelling companion" in self.page:
                                break
                            sleep(0.1)
                        text    = self.page
                        index   = text.find('Responsible person details')
                        text    = text[:index]
                        index   = text.rfind('<fieldset id="')
                        text    = text[index:]
                        labId   = pub.get_reg_value(r'(?<=fieldset id=").*?(?=")', text)
                        labxp   = f"//*[@id='{labId}']/div"
                        self.busy
                        # 关系
                        self.select_by_value((By.XPATH, f"{labxp}[2]//select"), i["applicant"])
                        # 姓
                        self.send_keys((By.XPATH, f"{labxp}[6]/div/div[1]/div/div[1]//input"), i["name_eng"])
                        # 名
                        self.send_keys((By.XPATH, f"{labxp}[6]/div/div[1]/div/div[2]//input"), i["names_eng"])
                        # 性别
                        self.click((By.XPATH, f"{labxp}[6]/div/div[2]//input[@value='{i['sex']}']"))
                        # 生日
                        self.send_keys((By.XPATH, f"{labxp}[6]/div/div[3]//input"), self.Tools.convertDateForAustralia(i["birth_date"]))
                        # 护照
                        self.send_keys((By.XPATH, f"{labxp}[7]/div/div[1]//input"), i["passport"])
                        # 护照签发国家
                        self.select_by_value((By.XPATH, f"{labxp}[7]/div/div[2]//select"), i["country"])
                        # 国籍
                        self.select_by_value((By.XPATH, f"{labxp}[7]/div/div[3]//select"), i["country"])
                        # 签发日期
                        self.send_keys((By.XPATH, f"{labxp}[7]/div/div[4]//input"), self.Tools.convertDateForAustralia(i["publish_time"]))
                        # 到期日期
                        self.send_keys((By.XPATH, f"{labxp}[7]/div/div[5]//input"), self.Tools.convertDateForAustralia(i["expire_date"]))
                        # 护照签发省
                        self.select_by_value((By.XPATH, f"{labxp}[7]/div/div[6]//select"), i["place_issue"])
                        # 监护人是否陪同|2
                        # self.click((By.XPATH, f"{labxp}[9]//input[@value='2']"))
                        # # 监护人签证 ID
                        # parent_id = self.asql.getOne(*self.asql.select_sql(tb=self._tb_info, sel="application_id", cond={"passport_number": i["passport"]}))
                        # if parent_id.get("applicatiion_id"):
                        self.click((By.XPATH, f"{labxp}[9]//input[@value='1']"))
                        self.select_by_index((By.XPATH, f"{labxp}[12]//select"), 1)
                        s = time()
                        while self.attr(self.find_element((By.XPATH, f"{labxp}[14]")), "hidden"):
                            if time() - s > 3:
                                s = time()
                                self.select_by_index((By.XPATH, f"{labxp}[12]//select"), 2)
                                self.busy
                                self.select_by_index((By.XPATH, f"{labxp}[12]//select"), 1)
                                self.busy
                            sleep(0.1)
                        # self.send_keys((By.XPATH, f"{labxp}[14]//input"), parent_id.get("application_id"))
                        self.find_element((By.XPATH, f"{labxp}[14]//input"))
                        self.send_keys((By.XPATH, f"{labxp}[14]//input"), self.parent_id)
                        self.click((By.XPATH, '//button[@title="Save the current entry"]'))
                    pass
                pass
            pass
            self.busy
            # self.click((By.XPATH, f'{baxp}[4]//input[@value="2"]'), 2)
            # self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第六页
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第六页填写内容
    def page6(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Contact details")
            self.log(f"{self.fullName} 第五页必要信息未齐全")
            return 1
        self.log(f"进入第六页")
        try:
            index = text.find('Contact details')
            text = text[:index]
            index = text.rfind('<div id=')
            text = text[index:]
            titleId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)
            titleId6 = titleId[:-1]

            all_page = {
                "country_of_residence": 1,
                "department_office": 2,
                "residential_address": 3,
                "contact_telephone_numbers": 4,
                "postal_address": 5,
                "email_address": 1
            }

            attr_input_radio = " input[type=radio]"
            attr_input_text = " input[type=text]"
            attr_select = " select"
            attr_content_div = " .wc-content>div"
            attr_input_email = " input[type=email]"

            # ==================================== #
            # === department_office ============== #
            label = self.get_labels(titleId6, all_page["department_office"], attr_input_text)
            # 申请人可能被要求参加澳大利亚政府机关的面试。哪一个办公室离申请人最近的位置最近？默认填北京
            self.send_keys((By.ID, self.attr(label[0])), self.nearest_office)

            # ==================================== #
            # === country_of_residence =========== #
            label = self.get_labels(titleId6, all_page["country_of_residence"], attr_select)
            # 通常居住国
            sleep(3)
            if not self.is_clickable((By.ID, self.attr(label[0]))):
                sleep(5)
            self.select_by_value((By.ID, self.attr(label[0])), value=self.country_residence)

            # ==================================== #
            # === residential_address ============ #
            divs = self.get_labels(titleId6, all_page["residential_address"], ">div>div")
            # 居住地址  国家
            self.select_by_value((By.CSS_SELECTOR, f"#{self.attr(divs[2])} select"), self.live_country)
            # 街道
            self.send_keys((By.CSS_SELECTOR, f"#{self.attr(divs[3])} input"), self.address[:40])
            self.send_keys((By.CSS_SELECTOR, f"#{self.attr(divs[4])} input"), self.address[40:])
            # ==== #
            inputs = self.find_elements((By.CSS_SELECTOR, f"#{self.attr(divs[6])}>div>div"))
            # 城镇
            self.send_keys((By.CSS_SELECTOR, f"#{self.attr(inputs[0])} input"), f"{self.city}") if self.city else ""
            # 居住地址  省份
            inputs = self.find_elements((By.CSS_SELECTOR, f"#{self.attr(divs[6])}>div>div"))
            # element = self.find_visibility_element((By.CSS_SELECTOR, f"#{self.attr(inputs[1])} select"))
            sleep(1)
            self.select_by_value((By.CSS_SELECTOR, f"#{self.attr(divs[6])}>div>div select"), f"{self.live_province}") if self.live_province else ""
            # 邮编
            self.send_keys((By.CSS_SELECTOR, f"#{self.attr(inputs[2])} input"), f"{self.postalCode}") if self.postalCode else ""

            # ==================================== #
            # === contact_telephone_numbers ====== #
            phones = self.get_labels(titleId6, all_page["contact_telephone_numbers"], ">div>div")
            # 家庭电话
            self.send_keys((By.CSS_SELECTOR, f"#{self.attr(phones[2])} input"), f"{self.homePhone}") if self.homePhone else ""
            # 业务电话
            self.send_keys((By.CSS_SELECTOR, f"#{self.attr(phones[3])} input"), f"{self.businessPhone}") if self.businessPhone else ""
            # 手机
            self.send_keys((By.CSS_SELECTOR, f"#{self.attr(phones[4])} input"), self.mobile) if self.mobile else ""

            # ==================================== #
            # === postal_address ================= #
            postals = self.get_labels(titleId6, all_page["postal_address"], ">div>div")
            # 邮寄地址与住址相同吗  默认选是
            if self.mailing_address_is == 1:
                postals[1].find_element(By.CSS_SELECTOR, f"input[value='{self.mailing_address_is}']").click()
            if self.mailing_address_is == 2:
                self.log("邮寄地址不同")
                sleep(10)
                postals[1].find_element(By.CSS_SELECTOR, f"input[value='{self.mailing_address_is}']").click()
                # postals[1].find_element(By.CSS_SELECTOR, f"input[value='1']").click()
                # 国家
                self.select_by_value((By.CSS_SELECTOR, f"#{self.attr(postals[3])} select"), self.live_country)
                # 邮寄地址
                self.send_keys((By.CSS_SELECTOR, f"#{self.attr(postals[4])} input"), self.mailing_address[:40])
                self.send_keys((By.CSS_SELECTOR, f"#{self.attr(postals[5])} input"), self.mailing_address[40:])
                # 郊区/城镇
                inputs = self.find_elements((By.CSS_SELECTOR, f"#{self.attr(postals[7])}>div>div"))
                self.send_keys((By.CSS_SELECTOR, f"#{self.attr(inputs[0])} input"), f"{self.mailing_city}") if self.mailing_city else ""
                sleep(1)
                # 州/省
                self.select_by_value((By.CSS_SELECTOR, f"#{self.attr(postals[7])} select"), f"{self.mailing_province}") if self.mailing_province else ""
                sleep(1)
                # 邮政编码
                self.send_keys((By.CSS_SELECTOR, f"#{self.attr(inputs[2])} input"), f"{self.mailing_postal_code}") if self.mailing_postal_code else ""

            # ==================================== #
            # === email address ================= #
            self.email = self.app["email"]
            label = self.get_label(titleId6, all_page["email_address"], attr_input_email)
            self.send_keys((By.CSS_SELECTOR, f"#{self.attr(label[0])}"), f"{self.email}") if self.email else ""
            pass
            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第七页
            # sleep(1)
            # self.page8()
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第七页填写内容
    def page7(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Authorised recipient")
            self.log(f"{self.fullName} 第六页必要信息未齐全")
            return 1
        self.log(f"进入第七页")
        try:
            text = self.page
            index = text.find('Authorised recipient')
            text = text[:index]
            index = text.rfind('<div id=')
            text = text[index:]
            titleId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)
            titleId7 = titleId[:-1]

            all_page = {
                "authorised_recipient": 1,
            }

            # ==================================== #
            # === authorised_recipient =========== #
            labels = self.get_labels(titleId7, all_page["authorised_recipient"], ">div>div")
            # 授权部门将所有书面信件直接发送给申请人 默认选否
            self.click((By.CSS_SELECTOR, f"#{self.attr(labels[1])} input[value={self.collection_letter}]"), 2)
            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第八页
            # sleep(1)
            # self.page9()
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第八页填写内容
    def page8(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Non-accompanying members of the family unit")
            self.log(f"{self.fullName} 第七页必要信息未齐全")
            return 1
        self.log(f"进入第八页")
        try:
            index = text.find('Non-accompanying members of the family unit')
            text = text[:index]
            index = text.rfind('<div id=')
            text = text[index:]
            titleId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)
            titleId8 = titleId[:-1]
            # 申请人是否有任何非澳大利亚公民或澳大利亚永久居民前往澳大利亚的家庭成员？
            if self.no_together:
                self.click((By.XPATH, '//input[@type="radio" and @value="1"]'), 2)
                locator = (By.XPATH, f"//*[@id='{titleId8}']/div/div//button")
                self.delete_btn(locator)
                for i in self.no_together:
                    for _ in range(100):
                        if "Non-accompanying members of the family unit" in self.page:
                            break
                        sleep(0.1)
                    for _ in range(100):
                        if "Non-accompanying member of the family unit" not in self.page:
                            self.click((By.XPATH, '//*[text()="Add"]'), 2)
                            sleep(0.1)
                            if ">An error has occurred<" in text:
                                self.errinfo("Non-accompanying member of the family unit")
                                self.log(f"{self.fullName} 申请人是否有任何非澳大利亚公民或澳大利亚永久居民前往澳大利亚的家庭成员？")
                                return 1
                            pass
                        else:
                            break
                    xpath1 = "//fieldset[1]{}"
                    xpath2 = xpath1.format("/div[4]/div/div[{}]{}")
                    xpath3 = xpath2.format("{}", "/div/div[{}]{}")
                    # 非同行人姓
                    # self.elem_send_keys(user[0].find_element(By.XPATH, "./div/div[1]//input"), i["name"])
                    self.elem_send_keys(self.find_element((By.XPATH, xpath3.format("1", "1", "//input"))), i["name"])
                    # 非同行人名
                    # self.elem_send_keys(user[0].find_element(By.XPATH, "./div/div[2]//input"), i["names"])
                    self.elem_send_keys(self.find_element((By.XPATH, xpath3.format("1", "2", "//input"))), i["names"])
                    # 非同行人性别
                    # user[1].find_element(By.CSS_SELECTOR, f"input[value={i['sex']}]").click()
                    self.find_element((By.XPATH, xpath2.format(2, f"//input[@value='{i['sex']}']"))).click()
                    # 同行人出生日期
                    # self.elem_send_keys(user[2].find_element(By.CSS_SELECTOR, "input"), i["birth"])
                    self.elem_send_keys(self.find_element((By.XPATH, xpath2.format("3", "//input"))), i["birth"])
                    # 非同行人关系
                    # self.select_has_element(fieldset.find_element(By.XPATH, "./div[2]//select"), value=i["rela"])
                    self.select_has_element(self.find_element((By.XPATH, xpath1.format("/div[2]//select"))), value=i["rela"])
                    # 国籍
                    # self.select_has_element(fieldset.find_element(By.XPATH, "./div[5]//select"), value=i["country"].strip())
                    self.select_has_element(self.find_element((By.XPATH, xpath1.format("/div[5]//select"))), value=i["country"].strip())

                    self.click((By.XPATH, '//button[@title="Save the current entry" and @type="submit"]'), 2)
                pass
            else:
                self.click((By.XPATH, '//input[@type="radio" and @value="2"]'), 2)
            sleep(0.5)
            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第十页
            # sleep(1)
            # self.page10()
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第九页填写内容
    def page9(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Entry to Australia")
            self.log(f"{self.fullName} 第八页必要信息未齐全")
            return 1
        self.log(f"进入第九页")
        try:
            index = text.find("Entry to Australia")
            text = text[:index]
            index = text.rfind('<div id=')
            text = text[index:]
            titleId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)
            titleId9 = titleId[:-1]

            page_9 = {
                "proposed_period_of_stay": 2,
                "study_while_in_australia": 4,
                "relatives_friends_or_contacts_in_australia": 5,
            }

            element = self.get_labels(titleId9, page_9["proposed_period_of_stay"], ' .wc-option input[type=radio]')[0]
            name = self.attr(element, 'name')
            # 申请人是否打算多次进入澳大利亚？
            if self.entryCount == "1":
                self.click((By.XPATH, f'//input[@name="{name}" and @value="{self.entryCount}"]'), 2)

                # 申请人是否知道首次进入澳大利亚后每个场合的入境日期？
                element = self.get_labels(titleId9, page_9["proposed_period_of_stay"], '  .wc-option input[type=radio]')[2]
                name = self.attr(element, 'name')
                if self.occasion_entry == '1':
                    self.click((By.XPATH, f'//input[@name="{name}" and @value="{self.occasion_entry}"]'), 2)
                    self.click((By.XPATH, "//button[text()='Add']"))
                    self.addDetails()
                    text = self.page
                    if ">An error has occurred<" in text:
                        self.errinfo("Entry to Australia")
                        self.log(f"{self.fullName} 添加申请人知道首次进入澳大利亚后每个场合的入境日期细节页面必要信息未齐全")
                        return 1
                else:
                    self.click((By.XPATH, f'//input[@name="{name}" and @value="{self.occasion_entry}"]'), 2)
                    element = self.get_labels(titleId9, page_9["proposed_period_of_stay"], '  .wc-content textarea')[0]
                    name = self.attr(element, 'name')
                    self.send_keys((By.NAME, name), self.occasion_entry_reasons)
            else:
                self.click((By.XPATH, f'//input[@name="{name}" and @value="{self.entryCount}"]'), 2)

            # 逗留时间 默认选择3个月
            element = self.get_labels(titleId9, page_9["proposed_period_of_stay"], ' select')[0]
            name = self.attr(element, 'name')
            self.select_by_value((By.NAME, name), self.stayAusTime)
            self.busy
            # 计划到达日期
            element = self.get_labels(titleId9, page_9["proposed_period_of_stay"], ' input[type=text]')[0]
            name = self.attr(element, 'name')
            self.is_clickable_time((By.NAME, name))
            self.send_keys((By.NAME, name), self.plannedArrivalDate)
            # 计划离开日期
            element = self.get_labels(titleId9, page_9["proposed_period_of_stay"], ' input[type=text]')[1]
            name = self.attr(element, 'name')
            self.send_keys((By.NAME, name), self.plannedFinalDepartureDate)

            # 申请人是否会在澳大利亚学习 默认选否
            labels = self.get_labels(titleId9, page_9["study_while_in_australia"], ">div>div")
            labels[1].find_element(By.CSS_SELECTOR, "input[value='2']").click()

            # 申请人是否会在澳大利亚访问任何亲戚、朋友或联系人？ 默认选否
            labels = self.get_labels(titleId9, page_9["relatives_friends_or_contacts_in_australia"], ">div>div")
            labels[1].find_element(By.CSS_SELECTOR, f"input[value='{self.visit_relatives}']").click()

            if self.visit_relatives == '1':
                # Contact in Australia
                btns = self.get_labels(titleId9, page_9["relatives_friends_or_contacts_in_australia"], " button")
                for i in btns[1::2]:
                    i.click()
                    self.driver.switch_to.alert.accept()
                for i in self.visit_rela_info:
                    self.get_labels(titleId9, page_9["relatives_friends_or_contacts_in_australia"], " button")[-1].click()
                    text = self.page
                    text = text[:text.rfind('Contact in Australia')]
                    text = text[text.rfind('<div id='):]
                    tmpTitleId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)
                    tmpTitleId = tmpTitleId[:-1]
                    page101 = {
                        'relationship_to_applicant': 1,
                        'contacts_details': 3,
                        'residential_address': 4,
                        'contact_telephone_numbers': 5,
                        'electronic_communication': 6,
                        'australian_residency_status': 8
                    }
                    btns = self.find_elements((By.CSS_SELECTOR, f"#{tmpTitleId}>div"))

                    # ==================================== #
                    # === relationship_to_applicant ====== #
                    # 联系人关系 applicant
                    btns[page101["relationship_to_applicant"]].find_element(By.CSS_SELECTOR, f"select>[value='{i['applicant']}']")

                    # ==================================== #
                    # === contacts_details =============== #
                    user = btns[page101["contacts_details"]].find_elements(By.XPATH, "./div/div[1]//input")
                    # 联系人姓 name_eng
                    self.elem_send_keys(user[0], i["name_eng"])
                    # 联系人名 names_eng
                    self.elem_send_keys(user[1], i["names_eng"])
                    # 联系人性别 sex
                    btns[page101["contacts_details"]].find_element(By.XPATH, f"./div/div[2]//input[@value='{i['sex']}']")
                    # 联系人出生日期 birth_date
                    birth = btns[page101["contacts_details"]].find_element(By.XPATH, f"./div/div[3]//input")
                    self.elem_send_keys(birth, self.Tools.convertDateForAustralia(i["birth_date"]))

                    # ==================================== #
                    # === residential_address ============ #
                    resid = btns[page101["residential_address"]
                                 ].find_elements(By.XPATH, "./div/div")
                    # 联系人居住国家 country
                    resid[2].find_element(By.CSS_SELECTOR, f"select>option[value='{i['country']}']")
                    # 联系人地址 address
                    self.elem_send_keys(resid[3].find_element(By.CSS_SELECTOR, "input"), i["address"][:40].upper())
                    self.elem_send_keys(resid[4].find_element(By.CSS_SELECTOR, "input"), i["address"][40:].upper())
                    # 联系人城市 city
                    self.elem_send_keys(resid[5].find_element(By.XPATH, "./div/div[1]//input"), i["city"])
                    # 联系人省份 province
                    self.select_has_element(resid[5].find_element(By.XPATH, "./div/div[2]//select"), value=i["city"])
                    # 联系人邮编 postal_code
                    self.elem_send_keys(resid[5].find_element(By.XPATH, "./div/div[3]//input"), i["city"])

                    # ==================================== #
                    # === contact_telephone_numbers ====== #
                    # 联系人家庭电话 home_phone
                    self.elem_send_keys(
                        btns[page101["contact_telephone_numbers"]].find_element(By.XPATH, "./div/div[3]//input"),
                        i["home_phone"]
                    )
                    # 联系人商务电话 business_phone
                    self.elem_send_keys(
                        btns[page101["contact_telephone_numbers"]].find_element(By.XPATH, "./div/div[4]//input"),
                        i["business_phone"]
                    )
                    # 联系人手机 mobile_phone
                    self.elem_send_keys(
                        btns[page101["contact_telephone_numbers"]].find_element(By.XPATH, "./div/div[5]//input"),
                        i["mobile_phone"]
                    )

                    # ==================================== #
                    # === electronic_communication 6 ===== #
                    # 联系人邮箱 email
                    self.send_keys((By.XPATH, "//*[@id='{tmpTitleId}']/div[7]/div/div[3]//input"), i["mobile_phone"])

                    # ==================================== #
                    # === australian_residency_status  8 = #
                    # 联系人身份 identity
                    self.select_by_value((By.XPATH, "//*[@id='{tmpTitleId}']/div[9]//select"), i["identity"])
                    self.click((By.XPATH, "//*[text()='Confirm']"))
                    pass
                pass
            pass
            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第十一页（页面显示11）
            # sleep(1)
            # self.page12()
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第十页填写内容 -- 未发现
    def page10(self):
        self.log(f"进入第十页")
        pass
    pass

    # 第十一页填写内容
    def page11(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Visa applicant's current overseas employment")
            self.log(f"{self.fullName} 第九页必要信息未齐全")
            return 1
        self.log(f"进入第十一页")
        if self.is_child:
            return 0
        try:
            index = text.find("Visa applicant's current overseas employment")
            text = text[:index]
            index = text.rfind('<div id=')
            text = text[index:]
            titleId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)
            titleId11 = titleId[:-1]

            baxp = f"//*[@id='{titleId11}']/"
            bxp = f"{baxp}div/div[%s]/div/div"
            fixp = f"{baxp}div/fieldset"
            # 就业状况 1在职, 2自我雇佣, 3失业, 4退休, 5学生, ~~99其他~~
            self.select_by_value((By.XPATH, f"{bxp % 2 }[2]//select"), self.workType)
            if self.workType in ['1', '2']:
                workInfo = json.loads(self.app["employment_info"])
                # ==================================== #
                # === Current employment details ===== #
                # 职业分组
                self.select_by_value((By.XPATH, f"{bxp % 2 }[4]//select"), workInfo["job"])
                # if str(self.workGroup) == '070299':
                #     # 工作职业
                #     self.send_keys((By.CSS_SELECTOR, "textarea:nth-of-type(1)"), self.workTitle)
                # pass
                # 工作单位
                self.send_keys((By.XPATH, f"{bxp % 2 }[6]//input"), workInfo['name'])
                # 工作开始时间
                self.send_keys((By.XPATH, f"{bxp % 2 }[7]//input"), strftime("%d %b %Y", strptime(workInfo["time"], "%Y-%m-%d")))
                # ==================================== #
                # === Organisation address =========== #
                # 国家
                # self.select_by_value((By.XPATH, f"{bxp % 6 }[3]//select"), workInfo['country'])
                self.select_by_value((By.XPATH, f"{bxp % 6 }[3]//select"), "PRCH")
                # 详细地址
                self.send_keys((By.XPATH, f"{bxp % 6 }[4]//input"), workInfo['address'][:40].upper())
                self.send_keys((By.XPATH, f"{bxp % 6 }[5]//input"), workInfo['address'][40:].upper())
                # 城镇
                self.send_keys((By.XPATH, f"{bxp % 6 }[7]/div/div[1]//input"), workInfo['city'])
                sleep(2)
                # 省份
                self.select_by_value((By.XPATH, f"{bxp % 6}[7]/div/div[2]//select"), workInfo['province'])
                # 邮编
                self.send_keys((By.XPATH, f"{bxp % 6 }[7]/div/div[3]//input"), workInfo['postal_code'])
                # ==================================== #
                # === Contact telephone numbers ====== #
                # 商务电话
                self.send_keys((By.XPATH, f"{bxp % 8 }[3]//input"), str(
                    workInfo['business_phone']).strip("None").replace("-", ""))
                # 手机
                self.send_keys((By.XPATH, f"{bxp % 8 }[4]//input"), str(
                    # workInfo['mobile_phone']).strip("None").replace("-", ""))
                    workInfo['business_phone']).strip("None").replace("-", ""))
                # ==================================== #
                # === Electronic communication ======= #
                # 邮件
                self.send_keys((By.XPATH, f"{bxp % 9}[3]//input"), workInfo['email'])
            elif self.workType == '3':
                # ==================================== #
                # === Unemployment =================== #
                # 失业时间
                self.send_keys((By.XPATH, f"{fixp}[2]/div[4]//input"), self.unemploymentTime)
                # 上一个工作
                self.send_keys((By.XPATH, f"{fixp}[2]/div[5]//input"), self.oldWrok)
            elif self.workType == '4':
                # ==================================== #
                # === Retirement ===================== #
                # 退休时间
                self.send_keys((By.XPATH, f"{baxp}/div/div[3]//input"), self.retirementTime)
            elif self.workType == '5':
                student = json.loads(self.app["employment_study"])
                # ==================================== #
                # === Student course details ========= #
                # 专业
                self.send_keys((By.XPATH, f"{fixp}[1]/div[3]//input"), student["course_name"])
                # 学校
                self.send_keys((By.XPATH, f"{fixp}[1]/div[4]//input"), student["institution_name"])
                # 入学时间
                self.send_keys((By.XPATH, f"{fixp}[1]/div[5]/div/div[1]//input"), self.Tools.convertDateForAustralia(student['date_from']))
                # 毕业时间
                self.send_keys((By.XPATH, f"{fixp}[1]/div[5]/div/div[2]//input"), self.Tools.convertDateForAustralia(student['date_to']))
            elif self.workType == '99':
                # 详细信息
                self.send_keys((By.XPATH, f"{bxp % 2 }//textarea"), self.workDeatil)
            pass
            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第十二页
            # sleep(1)
            # self.page13()
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            # else:
            #     update_data = {
            #         'ques': str(e),
            #         'status': 4,
            #         'utime': int(time())
            #     }
            #     sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
            #     sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
            #     self.asql.update(*sqls)
            #     self.asql.update(*sqlc)
            #     sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第十二页填写内容
    def page12(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Financial support")
            self.log(f"{self.fullName} 第十一页必要信息未齐全")
            return 1
        self.log(f"进入第十二页")
        try:
            text = text[:text.find("Financial support")]
            text = text[text.rfind('<div id='):]
            titleId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)
            titleId12 = titleId[:-1]
            baxp = f"//*[@id='{titleId12}']/"
            # 详述申请人在澳大利亚逗留期间的资金情况。
            # if self.financialType == '1':
            self.click((By.XPATH, f'{baxp}div/div[2]/div/div[4]//input[@value="{self.financialType}"]'), 2)
            pass
            if self.financialType != '1':
                # 支持类型
                self.select_by_value((By.XPATH, f'{baxp}div/div[2]/div/div[5]//select'), self.supportType)
            pass
            """ applicant name_eng names_eng country address city province postal_code """
            # 申请人将有哪些资金支持他们在澳大利亚的逗留
            self.send_keys((By.XPATH, f"{baxp}div/div[2]/div/div[6]//textarea"), self.financialDetail)
            if self.financialType in ['3', '4']:
                fina = json.loads(self.app["tourism_funding_info"])
                # 国家
                self.select_by_value((By.XPATH, f"{baxp}div/div[8]/div/div[2]//select"), fina["country"])
                # sleep(1)
                # 详细地址
                self.send_keys((By.XPATH, f"{baxp}div/div[8]/div/div[3]//input"), fina["address"][:40].upper())
                self.send_keys((By.XPATH, f"{baxp}div/div[8]/div/div[4]//input"), fina["address"][40:].upper())
                # 城镇
                self.send_keys((By.XPATH, f"{baxp}div/div[8]/div/div[6]/div/div[1]//input"), fina["city"])
                # 省
                self.select_visibility_by_text((By.XPATH, f"{baxp}div/div[8]/div/div[6]/div/div[2]//select"), self.Tools.convertProvinceForAustralia(fina["province"]))
                # 邮编
                self.send_keys((By.XPATH, f"{baxp}div/div[8]/div/div[6]/div/div[3]//input"), fina["postal_code"])
            pass
            if self.financialType == '4':
                self.select_by_value((By.XPATH, f'{baxp}div/div[3]//select'), fina["applicant"])
                # 姓
                self.send_keys((By.XPATH, f"{baxp}div/div[6]/div/div[1]//input"), fina["name_eng"])
                # 名
                self.send_keys((By.XPATH, f"{baxp}div/div[6]/div/div[2]//input"), fina["names_eng"])
            pass
            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第十三页（页面显示15）
            # sleep(1)
            # self.page16()
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第十三页填写内容 -- 未发现
    def page13(self):
        self.log(f"进入第十三页")
        pass
    pass

    # 第十四页填写内容 -- 未发现
    def page14(self):
        self.log(f"进入第十四页")
        pass
    pass

    # 第十五页填写内容
    def page15(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Health declarations")
            self.log(f"{self.fullName} 第十二页必要信息未齐全")
            return 1
        self.log(f"进入第十五页")
        try:
            text = text[:text.find("Health declarations")]
            text = text[text.rfind('<div id='):]
            titleId15 = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)[:-1]

            baxp = f"//*[@id='{titleId15}']/div/div"

            # 在过去五年中，是否有申请人连续三个月访问或居住在护照国境外？ 默认否
            self.click((By.XPATH, f"{baxp}[2]//input[@value='{self.country_stay_other}']"), 2)
            if self.country_stay_other == "1":
                locator = (By.XPATH, f"{baxp}[3]//button")
                btns = self.find_elements(locator)
                self.delete_btn(locator)
                stay_countrys = json.loads(self.app["country_stay_info"])
                for i in stay_countrys:
                    self.find_elements((By.XPATH, f"{baxp}[3]//button"))[-1].click()
                    text1 = self.page
                    text1 = text1[:text1.find("Visits to other countries")]
                    text1 = text1[text1.rfind('<div id='):]
                    titleId151 = pub.get_reg_value(r'(?<=div id=").*?(?=")', text1)[:-1]
                    baxp151 = f"//*[@id='{titleId15}']/div/div"
                    # Name
                    self.select_by_index((By.XPATH, f"{baxp151}[3]//select"), 1)
                    # Country
                    self.select_by_value((By.XPATH, f"{baxp151}[4]//select"), i["country"])
                    # Date from
                    self.send_keys(
                        (By.XPATH, f"{baxp151}[5]/div/div[1]//input"),
                        self.Tools.convertDateForAustralia(i["entry_time"])
                    )
                    # Date to
                    self.send_keys(
                        (By.XPATH, f"{baxp151}[5]/div/div[2]//input"),
                        self.Tools.convertDateForAustralia(i["departure_time"])
                    )
                    self.click((By.XPATH, "//*[text()='Confirm']"))
            # 在澳大利亚，是否有申请人打算进入医院或医疗机构（包括疗养院）？ 否
            self.click((By.XPATH, f"{baxp}[4]//input[@value='2']"), 2)
            # 在澳大利亚逗留期间，申请人是否打算从事牙科医生、护士或护理人员的工作或学习？ 否
            self.click((By.XPATH, f"{baxp}[6]//input[@value='2']"), 2)
            # 有肺结核相关疾病吗？ 否
            self.click((By.XPATH, f"{baxp}[13]//input[@value='2']"), 2)
            # 申请人预计会产生医疗费用，或需要接受治疗或医疗跟进吗？ 否
            self.click((By.XPATH, f"{baxp}[16]//input[@value='2']"), 2)
            # 申请人是否因医疗条件需要调动或照料？ 否
            self.click((By.XPATH, f"{baxp}[18]//input[@value='2']"), 2)

            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第十六页
            # sleep(1)
            # self.page17()
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第十六页填写内容
    def page16(self):
        self.log(f"进入第十五页")
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Character declarations")
            self.log(f"{self.fullName} 第十六页必要信息未齐全")
            return 1
        try:
            text = self.page
            text = text[:text.find("Character declarations")]
            text = text[text.rfind('<div id='):]
            titleId16 = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)[:-1]

            inputs = self.find_elements((By.CSS_SELECTOR, f"input[name^={titleId16}][value='2']"))
            [i.click() for i in inputs if i.is_displayed()]
            # 申请人被指控犯有目前正在等待法律诉讼的罪行？ 否
            # 是否有任何申请人在任何国家被判有罪（包括从官方记录中删除的任何定罪）？ 否
            # 是否有任何申请人曾获逮捕令或国际刑警组织通知？ 否
            # 申请人是否曾被判犯有涉及儿童的性犯罪（包括没有定罪记录的地方）？ 否
            # 是否有任何申请人在性犯罪登记册上被提名？ 否
            # 申请人是否因无心或精神错乱而被判无罪？ 否
            # 是否有任何申请人被一个不适合辩护的法院发现？ 否
            # 是否有任何申请人曾直接或间接参与或参与在澳大利亚或任何其他国家可能对国家安全构成风险的活动？ 否
            # 申请人是否曾因种族灭绝、战争罪、危害人类罪、酷刑、奴役或其他严重国际罪行而被起诉或起诉？ 否
            # 申请人是否曾与海外或澳大利亚从事暴力或暴力行为（包括战争、叛乱、自由斗争、恐怖主义、抗议）的组织有联系？ 否
            # 申请人曾经在军事部队、警察部队、国家赞助的/私人的民兵或情报机构（包括秘密警察）工作过吗？ 否
            # 申请人是否接受过任何军事/准军事训练、武器/爆炸物训练或化学/生物制品制造训练？ 否
            # 申请人是否曾参与过走私或贩卖人口罪？ 否
            # 是否有任何申请人被驱逐出境、驱逐出境或被排除在任何国家（包括澳大利亚）？ 否
            # 是否有申请人在任何国家（包括澳大利亚）签证过期？ 否
            # 是否有任何申请人曾向澳大利亚政府或澳大利亚的任何公共当局提供过未偿还的债务？ 否
            # 任何申请人是否曾与曾参与或参与犯罪行为的人、团体或组织有联系？ 否

            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第十七页
            # sleep(1)
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第十七页填写内容
    def page17(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Visa history")
            self.log(f"{self.fullName} 第十六页必要信息未齐全")
            return 1
        self.log(f"进入第十七页")
        try:
            text = self.page
            text = text[:text.find("Visa history")]
            text = text[text.rfind('<div id='):]
            titleId17 = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)[:-1]

            baxp = f"//*[@id='{titleId17}']/div/div"

            # 申请人是否持有或正在申请澳大利亚或其他国家的签证？ 否
            self.click((By.XPATH, f'{baxp}[2]//input[@value="{self.other_visa_is}"]'), 2)
            if self.other_visa_is == '1':
                self.send_keys((By.XPATH, f'{baxp}[3]//textarea'), self.other_visa_info)
            pass
            # 申请人是否曾经在澳大利亚或任何其他国家，没有遵守签证条件，或离开其授权逗留期限？ 否
            self.click((By.XPATH, f'{baxp}[4]//input[@value="{self.stay_timeout_is}"]'), 2)
            if self.stay_timeout_is == '1':
                self.send_keys((By.XPATH, f'{baxp}[5]//textarea'), self.stay_timeout_info)
            pass
            # 申请人是否曾申请过澳大利亚签证或其他国家拒绝或取消签证？ 否
            self.click((By.XPATH, f'{baxp}[6]//input[@value="{self.refuse_visa_is}"]'), 2)
            if self.refuse_visa_is == '1':
                self.send_keys((By.XPATH, f'{baxp}[7]//textarea'), self.refuse_visa_info)
            pass

            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第十八页(页面显示19)
            # sleep(1)
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第十八页填写内容 -- 未发现
    def page18(self):
        self.log(f"进入第十八页")
        pass
    pass

    # 第十九页填写内容
    def page19(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Declarations")
            self.log(f"{self.fullName} 第十七页必要信息未齐全")
            return 1
        self.log(f"进入第十九页")
        try:
            text = text[:text.find("Declarations")]
            text = text[text.rfind('<div id='):]
            titleId19 = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)[:-2]
            inputs = self.find_elements((By.CSS_SELECTOR, f"input[name^={titleId19}][value='1']"))
            [i.click() for i in inputs if i.is_displayed()]
            # 阅读并理解在本申请中提供给他们的信息？ 是
            # 在该表格的每一个细节上，以及在它的任何附件上都提供了完整和正确的信息？ 是
            # 如果本申请书提供了任何欺诈性文件或虚假或误导性的信息，申请将被拒绝 是
            # 请理解，如果发给签证后发现文件有欺诈性或信息不正确，签证随后可能被取消。 是
            # 当他们得知情况变化（包括地址变化）时，或在审议本申请时，如与本申请所提供或与本申请有关的信息有任何变化，将立即书面通知本署。 是
            # 已阅读隐私声明（表格1442I）中包含的信息。是
            # 明白本署可收集、使用及披露申请人的个人资料（包括生物统计资料及其他敏感资料），如保密通知（表格1442i）所述。 是
            # 请理解，如果这个签证没有附加8503条件，它将限制在澳大利亚停留超过批准的停留期限的能力。 是
            # 同意不接受学习或培训超过三个月。 是
            # 同意在签证停留期届满前或离开澳大利亚前离开。 是
            # 如有需要，同意收集指纹和面部图像。 是
            # 请理解，如果需要提供他们的指纹和面部图像，申请人的指纹、面部图像和由该部保存的传记信息可以被提供给澳大利亚执法机构，以帮助识别申请人并确定授予e签证申请，并为执法目的。 是
            # 同意澳大利亚执法机构向司法部披露申请人的生物特征、个人简历和犯罪记录信息，以帮助确定申请人，确定授予签证和执法目的的资格。 是
            # 同意移民局使用申请人为移民法或2007年《公民法》目的而取得的生物特征资料、传记资料和犯罪记录资料。 是

            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到第二十页
            # sleep(1)
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 第二十页填写内容
    def page20(self):
        text = self.page
        if ">An error has occurred<" in text:
            self.errinfo("Priority Consideration (fast-track) service")
            self.log(f"{self.fullName} 第十九页必要信息未齐全")
            return 1
        self.log(f"进入第二十页")

        try:
            # sleep(10)
            text = self.page
            text = text[:text.find("Priority Consideration (fast-track) service")]
            text = text[text.rfind('<div id='):]
            titleId20 = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)[:-1]

            baxp = f"//*[@id='{titleId20}']/div/div"
            self.priority_treatment_is = str(self.app['priority_treatment_is'] + 1)
            # 申请人是否想申请优先考虑服务费？ 是
            if self.priority_treatment_is == "1":
                self.click((By.XPATH, f"{baxp}[3]//input[@value='{self.priority_treatment_is}']"), 2)
                self.click((By.XPATH, f"{baxp}[6]//input[@value='1']"), 2)
            else:
                # 申请人是否想申请优先考虑服务费？ 否
                self.click((By.XPATH, f"{baxp}[3]//input[@value='{self.priority_treatment_is}']"), 2)

            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到确认页面
            # sleep(1)

            # 确认页面
            self.click((By.XPATH, "//span[text()='Next']"))  # 下一步到上传文档页面
            # sleep(1)
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    def addIdCard(self):
        try:
            # 添加身份证页面
            self.find_element((By.XPATH, '//*[text()="National identity card"]'), 2)
            text = self.page
            requires = re.findall(r'<script type=[\'"]text/javascript[\'"] class=[\'"]registrationScripts[\'"]>(.*?)</script>', text)[0].replace(" ", "")
            ids = re.findall(r"c\.register\((.*?)\);", requires)
            index = text.find('National identity card')
            text = text[:index]
            index = text.rfind('<div id=')
            text = text[index:]
            titleId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text)
            titleId = titleId[: len(titleId)]
            con = json.loads(ids[0])[0]
            cons = con.replace(titleId, "")
            fName = ids[1][1:-1]
            names = fName.replace(titleId, "")
            # 姓
            self.send_keys((By.NAME, fName), self.firstEName)
            # 名
            self.send_keys((By.NAME, titleId + pub.fmst(names[:3], "000001") + names[3:]), self.lastEName)
            # 身份证号
            self.send_keys((By.NAME, titleId + pub.fmst(cons[:2], "0011") + cons[2:]), self.idCard)
            # 国籍
            for _ in range(50):
                if self.is_clickable((By.NAME, con)):
                    break
                sleep(0.1)
            self.select_by_value((By.NAME, con), 'PRCH')
            # 身份证发行时间
            self.send_keys((By.NAME, titleId + pub.fmst(cons[:2], "0002") + cons[2:]), self.idCardStarTime)
            # 到期时间
            self.send_keys((By.NAME, titleId + pub.fmst(cons[:2], "0003") + cons[2:]), self.idCardEndTime)
            # 下一步 回到第三页
            self.click((By.XPATH, '//button[text()="Confirm"]'), 2)
            # sleep(1)
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1
    pass

    # 添加同行页面
    def addTravellingCompanion(self):
        self.log("添加同行页面")
        try:
            text = self.page
            index = text.find('Travelling companion')
            text = text[:index]
            index = text.rfind('<fieldset id="')
            text = text[index:]
            labId = pub.get_reg_value(r'(?<=fieldset id=").*?(?=")', text)
            labxp = f"//*[@id='{labId}']/div"
            self.peer_people_info = json.loads(self.app["peer_people_info"])
            for i in self.peer_people_info:
                # 姓
                self.send_keys((By.XPATH, f"{labxp}[3]/div/div[1]/div/div[1]//input"), i["name_eng"])
                # 名
                self.send_keys((By.XPATH, f"{labxp}[3]/div/div[1]/div/div[2]//input"), i["names_eng"])
                # 性别
                self.click((By.XPATH, f"{labxp}[3]/div/div[2]//input[@value='{i['sex']}']"))
                # 生日
                self.send_keys((By.XPATH, f"{labxp}[3]/div/div[3]//input"), self.Tools.convertDateForAustralia(i["birth_date"]))
                # 关系
                self.select_by_value((By.XPATH, f"{labxp}[2]//select"), i["applicant"])
                # 下一步返回第五页
            self.click((By.XPATH, '//button[text()="Confirm"]'), 2)
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1

    # 添加申请人知道首次进入澳大利亚后每个场合的入境日期细节页面(第九页)Add details
    def addDetails(self):
        try:
            text = self.page
            index = text.find('Give details of the additional entry.')
            text = text[:index]
            index = text.rfind('<fieldset id="')
            text = text[index:]
            labId = pub.get_reg_value(r'(?<=fieldset id=").*?(?=")', text)
            labxp = f"//*[@id='{labId}']/div"
            self.occasion_entry_time = json.loads(self.app["occasion_entry_time"])
            for i in self.occasion_entry_time:
                # 起始日期
                self.send_keys((By.XPATH, f"{labxp}[2]//div[1]//div/div[2]//input"), i["date_from"])
                # 截止日期
                self.send_keys((By.XPATH, f"{labxp}[2]//div[2]//div/div[2]//input"), i["date_to"])
                # 给出理由
                self.send_keys((By.XPATH, f"{labxp}[3]//div/div[2]/span/textarea"), i["give_reasons"])
            self.click((By.XPATH, '//button[text()="Confirm"]'), 2)  # 返回第九页
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1

    # 上传文件页面
    def pageDoc(self):
        self.log(f"进入上传文件页面")
        try:
            # db.save("app", {"application_status": '2'}, "id=%s", [self.app_id])
            update_data = {
                "application_status": 2,
                "utime": int(time())
            }
            sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
            sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
            self.asql.update(*sqls)
            self.asql.update(*sqlc)
            reg = r'>(\d{1,2})</strong></div><div class="wc-cell"> attachments received of'
            nums = lambda: int(re.findall(reg, self.page)[0])
            self.material_down()
            if nums() != len(self.fileList):
                self.click((By.XPATH, "//*[text()='​ Expand all']"))
                self.busy
                while 'Delete file' in self.page:
                    try:
                        self.find_elements((By.XPATH, '//button[@title="Delete file"]'))[0].click()
                        self.driver.switch_to.alert.accept()
                    except Exception:
                        pass
                    sleep(1)

                text = self.page

                text_required = text[text.rfind('Required'):]
                text_required = text_required[text_required.find('<div id'):]
                requiredId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text_required)
                requirexp = f"//*[@id='{requiredId}']/div/div/div/div/div"

                text_recommended = text[text.find('Recommended'):]
                text_recommended = text_recommended[text_recommended.find('<div id'):]
                recommendedId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text_recommended)
                recommendedxp = f"//*[@id='{recommendedId}']/div/div/div/div/div"

                fileinfo = {
                    "my_photo"                      : "Personal Photos",                        # 个人照片 -
                    "passport_img"                  : "First page of passport",                 # 护照首页              - DT132
                    "id_card_positive"              : "ID card: frontal'",                      # 身份证: 正面          -
                    "id_card_negative"              : "ID card: reverse side'",                 # 身份证: 反面          -
                    "marital_status"                : "marital status",                         # 婚姻状况              - DT053
                    "proof_employment"              : "English employment certificate",         # 英文在职证明          - DT255
                    "account_book"                  : "Account book",                           # 户口本                - DT053
                    "student_identification"        : "Student identification",                 # 学生身份证明          - DT127
                    "proof_school"                  : "Proof at school or at school",           # 在校或在读证明        - DT127
                    "committee_certificate"         : "Residents' Certificate (freelance)",     # 居委会证明(自由职业)  - DT127
                    "retirement_certificate"        : "Retirement certificate (retirees)",      # 退休证(退休人员)      - DT425
                    "proof_funds"                   : "Proof of funds",                         # 资金证明              - DT010
                    "business_license"              : "Company business license or organization code (with official seal)",   # 公司营业执照或组织机构代码(盖公章) - DT015
                    "passport_shooting"             : "Other pages of the passport",            # 护照拍摄              - DT471
                    "land_title"                    : "Land title",                             # 房产证
                    "peer_data"                     : "Peer data",                              # 同行人资料            - DT470
                    "birth_certificate"             : "Birth certificate",                      # 出生证                - DT127
                    # "unacceptable_consent"          : "Unacceptable letter of consent",       # 不随行同意函
                    "mother_id_card"                : "Mother ID card",                         # 母亲身份证            - DT053
                    "father_id_card"                : "Father ID card",                         # 父亲身份证            - DT053
                    "parental_marriage_certificate" : "Parental marriage certificate",          # 父母结婚证            - DT053
                    "sponsor_income_certificate"    : "Sponsor's income certificate",           # 资助人收入证明        - DT127
                    # "spouse_parental_funding"       : "Spouse or parental funding statement"  # 配偶或父母资助声明    - DT127
                    # "other_information"             : "Other supplementary information",      # 其余补充资料          - DT127
                    "auxiliary_assets"              : "Auxiliary assets",                       # 辅助资产              - DT127
                    # "inviting_party_information"    : "Inviting party information",           # 邀请方资料            - DT127
                    "english_invitation"            : "Personal English invitation",            # 个人英文邀请函        - DT127
                    "travel_plan"                   : "Travel plan to Australia",               # 赴澳行程计划          - DT086
                    "family_table"                  : "Form54",                                  # Form54                - DT364
                }
                """
                    Required --
                    照片
                        ["my_photo"]
                    护照首页
                        ["passport_img", "passport_shooting"]
                    身份证
                        ["id_card_positive", "id_card_negative"]
                    家庭登记册和组成表
                        ["account_book", "marital_status", "mother_id_card", "father_id_card", "parental_marriage_certificate"]  # , "unacceptable_consent", "birth_certificate"
                    申请人之前旅行的证据
                        []

                    Recommended --
                    澳大利亚计划旅游活动的证据 - 行程-机票-酒店
                        # ["travel_plan", "other_information", "english_invitation", "peer_data"]  # , "inviting_party_information"
                    财务状况和访问资金的证据 - 资金证明
                        ["proof_funds", "sponsor_income_certificate", "spouse_parental_funding", "land_title", "retirement_certificate",]  # ,  "auxiliary_assets"
                    目前就业或自营职业的证据
                        ["proof_employment", "student_identification", "proof_school", "committee_certificate", "retirement_certificate", "business_license"]
                """
                seldict = {
                    "passport_img"                  : "DT132",
                    "marital_status"                : "DT053",
                    "proof_employment"              : "DT255",
                    "account_book"                  : "DT053",
                    "student_identification"        : "DT127",
                    "proof_school"                  : "DT127",
                    "committee_certificate"         : "DT127",
                    "retirement_certificate"        : "DT425",
                    "proof_funds"                   : "DT010",
                    "business_license"              : "DT015",
                    "passport_shooting"             : "DT471",
                    "land_title"                    : "DT160",
                    "peer_data"                     : "DT470",
                    "birth_certificate"             : "DT012",
                    "mother_id_card"                : "DT053",
                    "father_id_card"                : "DT053",
                    "parental_marriage_certificate" : "DT053",
                    "sponsor_income_certificate"    : "DT127",
                    # "spouse_parental_funding"       : "DT127",
                    # "other_information"             : "DT127",
                    "auxiliary_assets"              : "DT127",
                    # "inviting_party_information"    : "DT127",
                    "english_invitation"            : "DT127",
                    "travel_plan"                   : "DT086",
                    "family_table"                  : "DT364",
                    "1229"                          : "DT252",
                }

                Travel = ["passport_img", "passport_shooting"]
                Evidence = []

                recommendes = {
                    #
                    "Evidence of planned tourism activities in Australia": ["travel_plan", "english_invitation", "peer_data", ],
                    "Evidence of the financial status and funding for visit":
                        ["proof_funds", "land_title", "spouse_parental_funding", "sponsor_income_certificate", "retirement_certificate"],
                    "Evidence of current employment or self-employment":
                        ["proof_employment", "student_identification", "proof_school", "committee_certificate", "retirement_certificate", "business_license"],
                    # "Group tour details (group name list, itinerary)": ["travel_plan"],
                    "Exceptional reasons for extended stay in Australia as a Visitor (beyond 12 months)": [],
                    "Consent documents for children under 18 (Form 1229)": [],
                    "Child travelling alone declaration (Form 1257)": [],
                }


                recommend_element = self.find_elements((By.XPATH, recommendedxp))
                recommend_infos = [i.text.split("\n")[0] for i in recommend_element[::2]]

                recommended = {f"{i * 2 + 2}": recommendes.get(v, []) for i, v in enumerate(recommend_infos)}

                divs = self.find_elements((By.XPATH, requirexp))

                if len(divs) == 10:
                    Travel = ["passport_img"]
                    Evidence = ["passport_shooting"]
                    seldict["passport_shooting"] = "DT366"

                while nums() < len(self.fileList):
                    self.busy
                    i = nums()
                    if self.fileList[i]["filename"] not in self.page:
                        self.log(info=self.fileList[i]["filename"])
                        filedir = self.fileList[i]["filedir"]
                        path = os.path.join(self.fileList[i]["local_path"], self.fileList[i]["filename"])
                        if filedir in ["my_photo"]:
                            """ 照片 """
                            self.send_keys_wait((By.XPATH, f"{requirexp}[2]//input[@type='file']"), path)
                            # self.send_keys_wait((By.XPATH, f"{requirexp}/div[2]//input[@type='file']"), path)

                        elif filedir in ["id_card_positive", "id_card_negative", "birth_certificate"]:
                            """ 身份证 """
                            self.send_keys_wait((By.XPATH, f"{requirexp}[6]//input[@type='file']"), path)

                        # elif filedir in ["account_book", "mother_id_card", "father_id_card", "parental_marriage_certificate", "family_table"]:
                        elif filedir in ["account_book", "marital_status", "mother_id_card", "father_id_card","parental_marriage_certificate", "family_table"]:
                            # , "unacceptable_consent", "birth_certificate"
                            """ 家庭登记册和组成表 上传户口本 """
                            self.select_by_value((By.XPATH, f"{requirexp}[8]//select"), seldict[filedir])
                            self.busy
                            if seldict[filedir] == "DT127":
                                self.send_keys_wait((By.XPATH, f"{requirexp}[8]//input[@type='text']"), fileinfo[filedir])
                            locator = (By.XPATH, f"{requirexp}[8]//input[@type='file']")
                            ids = self.attr(self.find_element(locator))
                            self.js_execute(f'document.getElementById("{ids}").removeAttribute("disabled")')
                            self.send_keys_wait(locator, path)
                            sleep(6)


                        elif filedir in Travel:
                            """ 护照 """
                            self.select_by_value((By.XPATH, f"{requirexp}[4]//select"), "DT132")
                            self.busy
                            if seldict[filedir] == "DT127":
                                self.send_keys_wait((By.XPATH, f"{requirexp}[4]//input[@type='text']"), fileinfo[filedir])
                            locator = (By.XPATH, f"{requirexp}[4]//input[@type='file']")
                            ids = self.attr(self.find_element(locator))
                            self.js_execute(f'document.getElementById("{ids}").removeAttribute("disabled")')
                            self.send_keys_wait(locator, path)
                            sleep(10)


                        elif filedir in Evidence:
                            """ 申请人之前旅行的证据 护照其他页 """
                            self.select_by_value((By.XPATH, f"{requirexp}[10]//select"), "DT366")
                            self.busy
                            # sel_other_passport = False
                            locator = (By.XPATH, f"{requirexp}[10]//input[@type='file']")
                            ids = self.attr(self.find_element(locator))
                            self.js_execute(f'document.getElementById("{ids}").removeAttribute("disabled")')
                            self.send_keys_wait(locator, path)
                            sleep(10)

                        # 推荐的
                        self.sleep_time = 7
                        for key, val in recommended.items():
                            if filedir in val:
                                # """ 澳大利亚计划旅游活动的证据 - 行程-机票-酒店 """
                                self.select_by_value((By.XPATH, f"{recommendedxp}[{key}]//select"), seldict[filedir])
                                self.busy
                                # sel_evidence_tourism = False
                                locator = (By.XPATH, f"{recommendedxp}[{key}]//input[@type='file']")
                                ids = self.attr(self.find_element(locator))
                                self.js_execute(f'document.getElementById("{ids}").removeAttribute("disabled")')
                                self.send_keys_wait(locator, path)
                                sleep(self.sleep_time)
                                self.sleep_time = self.sleep_time+10
                            pass
                        pass
                    st = time()
                    while 1:
                        self.busy
                        nnn = 0
                        errs = re.findall(r"_err['\"][>\s]", self.page)
                        if errs and errs[0]:
                            self.click((By.CSS_SELECTOR, "[aria-describedby$='_err']>button"))
                            self.driver.switch_to.alert.accept()
                            self.busy
                            break
                        if 'value="Cancel uploading:' in self.page:
                            self.busy
                            if time() - st > 5:
                                self.click((By.CSS_SELECTOR, '[value^="Cancel uploading:"]'))
                                self.driver.switch_to.alert.accept()
                            continue
                        self.busy
                        # """ 判断 Attach 元素是否存在 //button[text()="Attach"] """
                        if ">Attach<" in self.page:
                            aids = [self.attr(i) for i in self.find_elements((By.XPATH, '//button[text()="Attach"]'))]
                            [self.click((By.ID, i)) for i in aids]
                            self.busy
                        for _ in range(30):
                            if nums() > i:
                                nnn = 1
                                break
                            sleep(0.1)
                        else:
                            if 'value="Cancel uploading:' not in self.page and ">Attach<" not in self.page:
                                break
                        if nnn: break
                    self.busy
                    self.log(info=time() - st)
                    sleep(1)
                pass

                while (">Attach<" in self.page):
                    try:
                        self.find_elements((By.XPATH, '//button[text()="Attach"]'))[0].click()
                    except Exception:
                        pass
                    sleep(2)
                pass
            self.click((By.CSS_SELECTOR, 'button[title="Link to account page"]'))
            self.send_keys((By.NAME, 'i_instantSearchFld'), self.application_id)
            self.click((By.NAME, 'btn_perform_instant_srch'), 2)
            self.busy
            if self.find_element((By.CSS_SELECTOR, "button[id^='defaultActionPane']")).text == "Attach documents":
                self.click((By.ID, 'defaultActionPanel_0_0'), 2)
            else:
                self.click((By.ID, "actionPanel_0_10"), 2)
            self.log(info="去支付页面")
            # 去支付页面
            self.find_element((By.CSS_SELECTOR, '[title="Go to the next page"]')).click()
            for _ in range(30):
                if "<h1>Providing supporting evidence</h1>" in self.page:
                    update_data = {
                        "status": 4,
                        "ques": f"{self.userName} 必要文件未齐全",
                        "utime": int(time()),
                    }
                    sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                    sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                    # sqlo = self.asql.update_sql(tb=self._tb_order, cond={"id": self.app["order_id"]}, ques=f"{self.userName} 必要文件未齐全")
                    self.asql.update(*sqls)
                    self.asql.update(*sqlc)
                    # self.asql.update(*sqlo)
                    sleep(1)
                    self.quit()
                    return 0
            self.click((By.XPATH, "//*[text()='Submit Now']"))
            update_data = {
                "status": 1,
                "ques": "",
                "application_status": 3,
                "utime": int(time())
            }
            sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
            sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
            self.asql.update(*sqls)
            self.asql.update(*sqlc)
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1

    # 付款页面
    def pagePay(self):
        self.log(f"进入付款页面")
        try:
            # db.save("app", {"application_status": '3'}, "id=%s", [self.app_id])
            if 'Application charges' in self.page:
                update_data = {
                    'status': 3,
                    "application_status": 3,
                    "utime": int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            # return
            # self.click((By.XPATH, "//*[text()='Submit Now']"))
            self.click((By.XPATH, '//input[@name="paymentMethod" and @value="CC"]'), 2)
            self.send_keys((By.NAME, 'cardnumber'), self.pay_cord)
            self.select_by_value((By.NAME, 'expirymonth'), str(int(self.pay_month)))
            self.select_by_text((By.ID, 'expiryyear'), self.pay_year)
            self.send_keys((By.NAME, 'cardname'), self.pay_name)
            self.send_keys((By.NAME, 'securityCode'), self.pay_cvv)
            pay_money = self.exChange()
            res = json.loads(requests.get(settings.VISA_API.format(self.id, self.mpid, pay_money)).text)
            if res['code'] == 6:
                self.click((By.ID, "submitButton"), 2)
            while self.attr(self.find_element((By.ID, "popup-container")), "style") == "display: none;":
                sleep(0.1)
            if self.attr(self.find_element((By.ID, "popup-container")), "style") == "display: block;":
                self.click((By.ID, "yesButton"), 2)  # 跳转到付款成功页面
                if ">Payment confirmation<" in self.page:
                    json.loads(requests.get(settings.VISA_API.format(self.id, self.mpid, pay_money)).text)
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
                    # 下载发票
                    self.click((By.XPATH, '//form[@id="cc_confirm"]/div/section/div/div/p/a'))
                    if not os.path.exists(self.download_path):
                        os.mkdir(self.download_path)
                    sleep(6)
                    for root, dirs, files in os.walk(self.download_path):
                        self.file_name = files[0]
                    self.file_dir = self.download_path + '\\' + self.file_name
                    sleep(3)
                    invoice_url = requests.post(
                        "https://visa.dllm.cn/index.php?s=/Business/Pcapi/insertpdf",
                        files={"file": ("invoice.pdf", open(self.file_dir, 'rb'), "application/pdf")},
                        timeout=10).json()

                    update_data = {
                        "invoice_url": invoice_url,
                        "utime": int(time())
                    }
                    sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                    sqlc = (sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1])
                    self.asql.update(*sqls)
                    self.asql.update(*sqlc)
                    sleep(1)


                    self.click((By.XPATH, '//button[@id="OnInputProcessing(return)"]'), 2)  # 返回数据列表页
                        # sql, val = self.asql.select_sql(tb=self._tb_info, cond={"status": 5})
                        # self.app = self.asql.getOne(sql, val)
                        # application_id = self.app["application_id "]
                    self.log(f"订单完成: {self.application_id}")
                    self.send_keys((By.NAME, 'i_instantSearchFld'), self.application_id)
                    self.click((By.NAME, 'btn_perform_instant_srch'), 2)
                    self.click((By.ID, 'defaultActionPanel_0_3'), 2)
                    self.pageSuc()
                    self.quit()
                    return 0
            else:
                update_data = {
                    "status": 4,
                    "ques": res['info'],
                    "utime": int(time())
                }
            sqlo = self.asql.update_sql(tb=self._tb_order, cond={"id": self.app["order_id"]}, **update_data)
            self.asql.update(*sqlo)
            return 0
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1

    # # 付款成功页面
    def pageSuc(self):
        self.log(f"进入付款成功页面")
        try:
            text = self.page
            text_required = text[text.rfind('Application home'):]
            text_required = text_required[text_required.find('<div id'):]
            requiredId = pub.get_reg_value(r'(?<=div id=").*?(?=")', text_required)
            requirexp = f"//*[@id='{requiredId}']/div/div[2]/div/div/div"
            # 判断文件夹是否存在，如果没有则创建
            if not os.path.exists(self.download_path):
                os.mkdir(self.download_path)
                sleep(3)
            # 个人信息表，下载PDF文档
            self.click((By.XPATH, f'{requirexp}/table/tbody/tr[1]//a'), 2)
            sleep(6)
            # 文件名字
            info_name = self.download_path + '\\visa.pdf'
            # 文件重命名
            os.rename(os.path.join(self.download_path, 'Application.pdf'), info_name)
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
                "status": 5,
                "my_info_url": my_info_url,
                "utime": int(time())
            }
            sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
            sqlc = (sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1])
            self.asql.update(*sqls)
            self.asql.update(*sqlc)
            sleep(1)
            return 0

        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1

    # 循环下载文件
    def material_down(self):
        self.log('待上传资料开始下载...')
        self.fileList = []

        fileList = [
            "my_photo",                         # 个人照片
            "passport_img",                     # 护照首页
            "id_card_positive",                 # 身份证: 正面'
            "id_card_negative",                 # 身份证: 反面'
            "marital_status",                   # 婚姻状况
            "proof_employment",                 # 英文在职证明
            "account_book",                     # 户口本  # =- 以下为 json -= #
            "student_identification",           # 学生身份证明
            "proof_school",                     # 在校或在读证明
            "committee_certificate",            # 居委会证明(自由职业)
            "retirement_certificate",           # 退休证(退休人员)
            "proof_funds",                      # 资金证明
            "business_license",                 # 公司营业执照或组织机构代码(盖公章)
            "passport_shooting",                # 护照拍摄
            "land_title",                       # 房产证
            "peer_data",                        # 同行人资料
            "birth_certificate",                # 出生证
            # "unacceptable_consent",             # 不随行同意函
            "mother_id_card",                   # 母亲身份证
            "father_id_card",                   # 父亲身份证
            "parental_marriage_certificate",    # 父母结婚证
            "sponsor_income_certificate",       # 资助人收入证明
            # "spouse_parental_funding",          # 配偶或父母资助声明
            # "other_information",                # 其余补充资料
            "auxiliary_assets",                 # 辅助资产
            # "inviting_party_information",       # 邀请方资料
            "english_invitation",               # 个人英文邀请函
            "travel_plan",                      # 赴澳行程计划
            "family_table",                     # Form 54
            # "electronic_signature",             # 电子签名
        ]

        r""" [self.fileList.append({"path": i, "filedir": appname}) for i in re.sub(r"[\[\]\\\"\s]", "", self.app[appname]).split(",") if i for appname in fileList if self.app[appname]] """
        for appname in fileList:
            jsonData = re.sub(r"[\[\]\\\"\s]", "", self.app[appname]).split(",") if self.app[appname] else []
            self.fileList += [
                {
                    "path": i, "filedir": appname
                } for i in jsonData if i
            ]


        for index in range(len(self.fileList)):
            path = self.fileList[index]['path']
            # self.fileList[index]["filename"] = "{}_{}.jpg".format(self.fileList[index]['filedir'], (index + 1))
            filepath, shotname, extension = self.FileTools.jwkj_get_filePath_fileName_fileExt(path)
            self.fileList[index]["filename"] = shotname + extension
            self.fileList[index]["local_path"] = os.path.join(self.local_path, self.fileList[index]['filedir']).lower()
            self.FileTools.down_file(path, self.fileList[index]["local_path"], self.app_id, (index + 1), len(self.fileList))
        pass

        while self.FileTools.errinfo:
            errlist = self.FileTools.errinfo
            self.FileTools.errinfo = []
            for index in range(len(errlist)):
                err = errlist[index]
                self.FileTools.down_file(err["url"], err["local_path"], self.app_id, (index + 1), len(errlist))

        for index in range(len(self.fileList)):
            file = self.fileList[index]
            self.log('服务器路径：%s 本地路径：%s' % (file['path'], file['local_path']))
        self.log('待上传资料下载完毕----')
    pass

    def get_labels(self, titleId, ids, attribute="", two_css=">.wc-content>div", by=By.CSS_SELECTOR):
        elements = self.find_elements((By.CSS_SELECTOR, f"#{titleId}{two_css}"), 2)
        element_id = elements[ids].get_attribute("id")
        labels = self.find_elements((by, f"#{element_id}{attribute}"))
        return labels

    def get_label(self, titleId, ids, attribute="", one_css=">.wc-content>fieldset>div>div>div>div", by=By.CSS_SELECTOR):
        elements = self.find_elements((By.CSS_SELECTOR, f"#{titleId}{one_css}"), 2)
        element_id = elements[ids].get_attribute("id")
        labels = self.find_elements((by, f"#{element_id}{attribute}"))
        return labels

    # 删除按钮
    def delete_btn(self, locator):
        self.busy
        while len(self.find_elements(locator)) > 1:
            btn = self.find_elements(locator)
            btn[1].click()
            self.driver.switch_to.alert.accept()
            self.busy
        add_id = self.attr(self.find_elements(locator)[-1])
        return add_id

    def attr(self, element, attr="id"):
        return element.get_attribute(attr)

    @property
    def busy(self):
        sleep(0.2)
        while '" aria-busy="true">' in self.page:
            sleep(0.1)

    # 错误信息字典
    @property
    def errdict(self):
        """ 错误信息提示：
            Returns:（dict) 奥签官网大部分错误信息的提示
        """
        return {
            "Please enter Username. ": "请输入用户名",
            "Please enter Password. ": "请输入密码",
            "'I have read and agree to the terms and conditions' is a required field.": "我已阅读并同意条款和条件未点击",
            "'Current location' is a required field.": "当前位置未填写",
            "'Legal status' is a required field.": "法律地位未填写",
            "'Select the stream the applicant is applying for:' is a required field.": "正在申请的类别未填写",
            "'List all reasons for visiting Australia' is a required field.": "访问澳大利亚类型未填写",
            "'Is this application being lodged as part of a group of applications?' is a required field.": "",
            "'Family name' is a required field.": "姓名未填写",
            "'Sex' is a required field.": "性别未填写",
            "'Date of birth' is a required field.": "出生日期未填写",
            "'Date of birth' must be today or before today.": "出生日期格式有误",
            "'Passport number' is a required field.": "护照号码未填写",
            "'Country of passport' is a required field.": "护照国家未填写",
            "'Nationality of passport holder' is a required field.": "护照持有人的国籍未填写",
            "'Date of issue' is a required field.": "护照发行日期未填写",
            "'Date of issue' is invalid.": "护照发行日期无效",
            "'Date of expiry' is a required field.": "护照到期日期未填写",
            "'Date of expiry' is invalid.": "护照到期日期无效",
            "'Place of issue / issuing authority' is a required field.": "护照发行地/发行机构未填写",
            "'Does this applicant have a national identity card?' is a required field.": "是否有身份证未选择",
            "'Identification number' is a required field.": "身份证号未填写",
            "All names may only contain standard English alphabetic characters including the space, apostrophe and hyphen characters. Please refer to the conversion table in Help.": "身份证名字输入格式不对",
            "'Country of issue' is a required field.": "发行国家未填写",
            "'Town / City' is a required field.": "出生城市未填写",
            "'State / Province' is a required field.": "出生省份未填写",
            "'Country of birth' is a required field.": "出生国家未填写",
            "'Relationship status' is a required field.": "婚姻状态未填写",
            "The table in 'Travelling companions' contains duplicate entries. The duplicate entry should be deleted or amended.": "“旅行伴侣”中的表格包含重复的条目。应删除或修改重复条目。",
            "'Is this applicant currently, or have they ever been known by any other names?' is a required field.": "是否有曾用名未填写",
            "'Is this applicant a citizen of the selected country of passport?' is a required field.": "是否为所选护照国家的公民未选择",
            "'Is this applicant a citizen of any other country?' is a required field.": "否是其他任何国家的公民未选择",
            "'Has this applicant previously travelled to Australia?' is a required field.": "是否曾去过澳大利亚未选择",
            "'Has this applicant previously applied for a visa to Australia?' is a required field.": "是否曾申请过澳大利亚的签证未选择",
            "'Does this applicant have an Australian visa grant number?' is a required field.": "授权号未选择",
            "'Does this applicant have any other passports or documents for travel?' is a required field.": "是否有其它护照/旅行证件未选择",
            "'Does this applicant have other identity documents?' is a required field.": "其它身份证件未选择",
            "'Has this applicant undertaken a health examination for an Australian visa in the last 12 months?' is a required field.": "健康检查未选择",
            "'Usual country of residence' is a required field.": "居住国家未填写",
            "'Office' is a required field.": "最近领区未填写",
            "'Country' is a required field.": "国家未填写",
            "'Address' is a required field.": "地址未填写",
            "'Planned arrival date' must be today or in the future.": "计划抵达日期”必须是今天或将来。",
            "'Planned final departure date' must be today or in the future.": "“计划的最终出发日期”必须是今天或将来。",
            "'Is the postal address the same as the residential address?' is a required field.": "邮寄地址为填写",
            "Telephone number can only contain numbers, no spaces are allowed.": "手机号码格式不对",
            "'Relationship to the applicant' is a required field.": "同行人与申请人的关系未填写",
            "The table in 'Non-accompanying members of the family unit' contains duplicate entries. The duplicate entry should be deleted or amended.":
                "家庭单位的非随行成员中的表格包含重复的条目.应删除或修改重复条目",
        }

    # 录入信息有误
    def errinfo(self, name=None):
        ls = []
        text = self.driver.page_source
        index = text.find('An error has occurred')
        text = text[index:]
        index = text.rfind(name)
        text = text[:index]
        errinfos = re.findall(r'<a.*?>(.*?)</a>', text, re.S)
        print(errinfos)
        for errinfo in errinfos:
            print(errinfo)
            print(type(errinfo))
            if errinfo == '':
                pass
            else:
                ls.append(self.errdict.get(errinfo))
        update_data = {
            "status": 4,
            "ques": str(ls),
            "utime": int(time())
        }
        sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
        sqlc = (sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1])
        self.asql.update(*sqls)
        self.asql.update(*sqlc)
        sleep(1)
        self.quit()

    # 澳元兑换人民币实时汇率
    def exChange(self):
        try:
            url = "https://www.huilv.cc/AUD_CNY/"  # 实时汇率网
            res = requests.get(url).text
            html = etree.HTML(res)
            text = html.xpath("//div[@class='converter_huilv2']/div[2]/span/text()")
            exchange = float(text[0])
            aus_pay = 141.85
            return round(exchange * aus_pay, 2)  #去小数点都两位
        except BaseException as e:
            if "Message" in str(e):
                pass
            else:
                update_data = {
                    'ques': str(e),
                    'status': 4,
                    'utime': int(time())
                }
                sqls = self.asql.update_sql(tb=self._tb_info, cond={"id": self.app["id"]}, **update_data)
                sqlc = [sqls[0].replace(self._tb_info, self._tb_infoC), sqls[1]]
                self.asql.update(*sqls)
                self.asql.update(*sqlc)
                sleep(1)
            self.log(debug='type(Exception):\t%s' % str(type(e)))
            self.log(debug='traceback.format_exc():\n{1}\n{0}\n{1}\n'.format(str(traceback.format_exc()), "-*" * 50))
            self.driver.quit()
            return 1



    def main(self):
        # self = Implement_class(112, '', '')
        status = self.Login()
        if status == 1:
            self.page1()
            pages = [
                self.page2, self.page3, self.page4, self.page6,
                self.page7, self.page8, self.page9, self.page11, self.page12,
                self.page15, self.page16, self.page17, self.page18, self.page19,
                self.page20, self.pageDoc, self.pagePay, self.pageSuc,
            ]
            for page in pages:
                sleep(1)
                if page():
                    break
        elif status == 2:
            self.pageDoc()
        elif status == 3:
            self.pagePay()
        elif status == 5:
            self.pageSuc()
        else:
            self.driver.quit()
            return 0
        self.driver.quit()

def main():
    aust = Implement_class(112, '', '', '')
    status = aust.Login()
    if status == 1:
        aust.page1()
        pages = [
            aust.page2, aust.page3, aust.page4, aust.page6,
            aust.page7, aust.page8, aust.page9, aust.page11, aust.page12,
            aust.page15, aust.page16, aust.page17, aust.page18, aust.page19,
            aust.page20, aust.pageDoc, aust.pagePay, aust.pageSuc,
        ]

        for page in pages:
            sleep(1)
            if page():
                break
    elif status == 2:
        aust.pageDoc()
    elif status == 3:
        aust.pagePay()
    elif status == 5:
        aust.pageSuc()
    else:
        return


if __name__ == "__main__":
    while 1:
        main()
    # aust = Implement_class(112, '', '', "1")
    # status = aust.Login()
    # print()