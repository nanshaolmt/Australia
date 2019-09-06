from inter_112 import Implement_class
from pipelines import Mysql
from settings import TB_INFO
import time
import os
from time import strftime


def run():
    while 1:
        mysql = Mysql()
        # def select_sql(self, tb, sel="*", cond=None, param="")
        #sql ----'SELECT COUNT(*) as c FROM dc_business_australia_info_eng WHERE status=%s '
        #val---[1] status 的值
        #"dc_business_australia_info_eng"  个人信息表.
        sql, val = mysql.select_sql(tb=TB_INFO, sel="COUNT(*) as c", cond={"status": 1})
        #查询 status 是1 的所有数据,取第一条.
        res = mysql.getOne(sql, val)

        #c  是查出来的值  count（*） as c    status  为1 的个数。
        if res["c"]:
            ic = Implement_class(112)
            ic.main()
        else:
            print('没有数据, 等待中...', strftime('%m/%d %H:%M:%S'))
            time.sleep(10)
            os.system("cls")
if __name__ == "__main__":
    run()

