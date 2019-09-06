from inter_112_less import Implement_class
from pipelines import Mysql
from settings import TB_INFO
import time
import os
from time import strftime


def run():
    while 1:
        mysql = Mysql()
        # def select_sql(self, tb, sel="*", cond=None, param="")
        sql, val = mysql.select_sql(tb=TB_INFO, sel="COUNT(*) as c", cond={"status": 8})
        res = mysql.getOne(sql, val)
        if res["c"]:
            ic = Implement_class(112)
            ic.main()
        else:
            print('没有数据, 等待中...', strftime('%m/%d %H:%M:%S'))
            time.sleep(10)
            os.system("cls")

if __name__ == "__main__":
    run()

