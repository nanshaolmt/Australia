# #!/usr/bin/env python
# # coding: utf-8
# """
# @Author : ZhaoBin
# @Date   : 2018-11-29 11:00:00
# @Last Modified by   : ZhaoBin
# @Last Modified time : 2018-12-11 10:06:57
# """
# import os
# import warnings
#
# warnings.filterwarnings('ignore')
#
# NC = "NOCLICK"
# BASEDIR = os.path.dirname(__file__)
# LOGIN_URL = "https://online.immi.gov.au/lusc/login"
# REGISTER_URL = "https://online.immi.gov.au/lusc/register"
# # EMAIL_NAME = "di44965sedan@163.com"
# # EMAIL_PASSWORD = "tong56"
# # EMAIL_NAME = "di44965sedan@163.com"
# # EMAIL_PASSWORD = "tong56"
# EMAIL_NAME = "flyvisa@163.com"
# EMAIL_PASSWORD = "5678tyui"
# VISA_PASSWORD = "QWEqwe123"
#
# # BROKER_URL = 'amqp://root:123456@192.168.0.158:5672'
# # BROKER_URL = 'redis://:5678tyui@localhost:6379/0'
# BROKER_URL = 'redis://:5678tyui@182.92.69.238:6379/2'
#
# # 可见性超时
# BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}  # 1 hour.
#
# # 广播信息默认队所有虚拟主机可见
# # BROKER_TRANSPORT_OPTIONS = {'fanout_prefix': True}
#
# # 如果你也想在 Redis 中存储任务的状态和返回值，你应该配置这些选项
# # CELERY_RESULT_BACKEND = 'redis://:5678tyui@localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://:5678tyui@182.92.69.238:6379/2'
# # CELERY_RESULT_BACKEND = 'amqp://root:123456@192.168.0.158:5672'
#
#
# PD_ID = "108534"
# PD_KEY = "XLEQruFUk1cqp/i7blRc5qH8JhWfEm93"
# APP_ID = "308532"
# APP_KEY = "QtUAXB6ust+uJm5cW2qLwA/RR1VlEA0F"
# FATEA_PRED_URL = "http://pred.fateadm.com"
#
# extension_path = r'C:\Users\Administrator\Desktop\automation\tools\ChroPath.crx'
#
# DBHOST = '60.205.119.77'
# DBUSER = 'mobtop'
# DBPWD = 'CSY5t6y7u8i'
# DBNAME = 'mobtop'
# DBPORT = 3306
# DBCHAR = "utf8mb4"
#
# MON = {
#     "01": "JAN",
#     "02": "FEB",
#     "03": "MAR",
#     "04": "APR",
#     "05": "MAY",
#     "06": "JUN",
#     "07": "JUL",
#     "08": "AUG",
#     "09": "SEP",
#     "10": "OCT",
#     "11": "NOV",
#     "12": "DEC",
# }
#
# TB_INFO = "dc_business_australia_info_eng"
# TB_VISA = "dc_business_visa_account"
# VISA_API = "https://visa.dllm.cn/index.php?s=/Api/MalaysiaApi/australia_pay/id/{}/mpid/{}/pay_money/{}"  # 扣签证费
# PAY_API = "http://visa.dllm.cn/index.php?s=/Api/MalaysiaApi/AustraliaRefund/id/{}/mpid/{}"  # 退回费
# # VISA_API = "http://djd.dllm.cn/index.php?s=/Api/MalaysiaApi/australia_pay/id/{}/mpid/{}/pay_money/{}"
# # PAY_API = "http://visa.dllm.cn/index.php?s=/Api/MalaysiaApi/AustraliaRefund/id/{}/mpid/{}"

# lis = [0,1,2,3,4,5,6,7]
# print(lis[1:3])
# print(lis[1:-3])
# print(lis[-4:])
# print(lis[::1])

print([1, 2] in [1, 2, 3])
print(('helleo') * 3)
print(['helleo'] * 3)


