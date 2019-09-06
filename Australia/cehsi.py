#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File  : cehsi.py
@Author: ChenLei
@Date  : 2019/7/15
"""

from pipelines import Mysql
import huilian_selenium
from time import sleep
from lxml import etree



with open(r'C:\Users\Administrator\Desktop\new 8.html', encoding='utf-8') as f:
    response = f.read()


html = etree.HTML(response)
value = html.xpath('//*[@id="overseas_territories"]/option/@value')
v_list = []
for i in value[1:]:
    v_list.append(i)
text = html.xpath('//*[@id="overseas_territories"]/option/text()')
t_list = []
for j in text[1:]:
    t_list.append(j)
v_t_zip = zip(v_list, t_list)
v_t_list = list(v_t_zip)
print(v_t_list)

class Selvisa(huilian_selenium.Huilian):
    mysql = Mysql()
    tb = 'dc_business_thailand_setting'

    def __init__(self, app_id=""):
        print(app_id)
        pass
    def pageSuc(self):
        # 保存状态至数据库
        v_t_list = [('BJS', '北京'), ('TNA', '济南'), ('XIY', '西安'), ('SHA', '上海'), ('HGH', '杭州'), ('NKG', '南京'), ('CAN', '广州'), ('SZX', '深圳'), ('FOC', '福州'), ('CNG', '成都'), ('CKG', '重庆'), ('KMG', '昆明'), ('WUH', '武汉'), ('CSX', '长沙'), ('SHE', '沈阳')]
        for k, v in v_t_list:
            print(f'正在更新的是：{v}')
            update_data = {
                "status": 11,
                "mpid": 44,
                "type": "法国领区",
                "china_name": v,
                "english_name": v,
                "china_value": k,
                "english_value": k,

            }
            sqls = self.asql.insert_sql(tb=self.tb, **update_data)
            self.asql.update(*sqls)
            sleep(1)
    # 数据库操作
    @property
    def asql(self):
        return Mysql()

def run():
    Selvisa().pageSuc()

if __name__ == "__main__":
    run()








