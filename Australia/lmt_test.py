import inspect
import json
import os




# cond = {'ok':1}
# print(list(cond.keys()))
# keys = list(cond.keys())
# key = ", ".join([f"{k}=%s" for k in keys])
# print(keys)
#
# val = [cond[k] for k in keys]
# print(val)
#
# dirPath = os.path.dirname(inspect.currentframe().f_code.co_filename)
# print(dirPath)

# import configparser
#
# config = configparser.ConfigParser()
# config['DEFAULT'] = {'ServerAliveInterval': '45',
#                     'Compression': 'yes',
#                     'Compression': 'yes',
#                     'CompressionLevel': '9'}
# config['bitbucket.org'] = {}
# config['bitbucket.org']['User'] = 'hg'
# config['topsecret.server.com'] = {}
# topsecret = config['topsecret.server.com']
# topsecret['Port'] = '50022'     # mutates the parser
# topsecret['ForwardX11'] = 'no'  # same here
# config['DEFAULT']['ForwardX11'] = 'yes'
# with open('configTest.ini', 'w') as configfile:
#     config.write(configfile)
#
# print(config.get('DEFAULT','CompressionLevel'))


# 时间的模块.
# import time
# from time import strftime
# from datetime import datetime
#
# res= time.strftime("%Y-%m-%d", time.strptime('2017-07-06', "%Y-%m-%d"))
# print(res,type(res))
#
# dat = datetime(1970, 1, 1),type(datetime(1970, 1, 1))
# y, m, d, h = [int(i) for i in strftime("%Y-%m-%d-%H").split("-")]
# print(y, m, d, h)
# print(strftime("%Y-%m-%d-%H"))
# print(dat.total_seconds())

# kw  = {"好":1,'嘿嘿':2}
# keys = list(kw.keys())
# key = ", ".join([f"{k}=%s" for k in keys])
# print(key)
# val = [kw[k] for k in keys]
# print(val)



# --------------......selenium  webdiver
# import time
#
# from selenium import webdriver
# # 设置 chrome_options 属性
# from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
# import settings
#
# chrome_options = webdriver.ChromeOptions()
# # 设置浏览器窗口大小
# # chrome_options.add_argument('window-size=1800x2000')
# # 无界面
# # chrome_options.add_argument('--headless') if noWin else ""
# # 不加载图片
# chrome_options.add_argument('blink-settings=imagesEnabled=false')
# # 设置代理
# # chrome_options.add_argument('--proxy-server=http://127.0.0.1:1080')
# #
# # ----------页面打印版pdf下载-----------------
#
# download_dir=os.path.join(settings.BASEDIR, 'files')
# appState = {
#     "recentDestinations": [
#         {
#             "id": "Save as PDF",
#             "origin": "local"
#         }
#     ],
#     "selectedDestinationId": "Save as PDF",
#     "version": 2
# }
#
#
# # ----------网页版pdf直接下载-----------------
# profile = {
#     "plugins.plugins_list": [{
#         "enabled": False, "name": "Chrome PDF Viewer"
#     }],  # Disable Chrome's PDF Viewer
#     "download.default_directory": download_dir,
#     "profile.default_content_settings.popups": 0,
#     "download.extensions_to_open": "applications/pdf",
#     'printing.print_preview_sticky_settings.appState': json.dumps(appState),
#     # 'savefile.default_directory': download_dir
# }
#
# userName = '180256122@qq.com'
# password = 'C5678tyui'
#
#
# chrome_options.add_experimental_option('prefs', profile)
# chrome_options.add_argument('--kiosk-printing')
# driver = webdriver.Chrome(chrome_options=chrome_options)
# driver.get('https://online.immi.gov.au/lusc/login')
#
# element = WebDriverWait(driver, 20).until(
#                 EC.presence_of_element_located(((By.NAME, 'username'))))
#
# print('----------111',type(element),element)
# element.clear()
# element.send_keys(userName)
# element= WebDriverWait(driver,20).until(EC.presence_of_element_located(((By.XPATH, '//*[@id="password"]'))))
# element.clear()
# element.send_keys(password)
#
# # 登录 按钮
# element = WebDriverWait(driver, 10).until(
#                 EC.presence_of_element_located(((By.NAME, 'login'))))
# locator = (By.NAME, 'login')
# js = f'document.getElementsByName("{locator[1]}")[0].click()'
# driver.execute_script(js)
#
# #点击继续
# locator = (By.NAME, 'continue')
# element = WebDriverWait(driver, 2).until(
#                 EC.presence_of_element_located(locator))
# js = f'document.getElementsByName("{locator[1]}")[0].click()'
# driver.execute_script(js)
# #拿到网页源码
# text = driver.page_source
# print(text)
# # text.find()
# # with open('wy.html','w',encoding='utf8')  as f :
# #     f.write(text)
#
# # element.get_attribute("id")
# time.sleep(50)
# driver.close()


# import time
#
# t = (2009, 2, 17, 17, 3, 38, 1, 48, 0)
# t = time.mktime(t)
# print(t)
# print(time.gmtime(t))
# res = time.strftime(" %Y  %d %b  %H:%M:%S", time.gmtime(t))
# print(res)


# import time
#
# '''dateStr 2017-07-06'''
# #---看传的时间 是不是空,或者是None
# res = time.strftime("%Y-%m-%d", time.strptime('2017-07-06', "%Y-%m-%d"))
# print(time.strptime('2017-07-06', "%Y-%m-%d"))
# print(res,type(res))




# ---时间操作.
# from datetime import datetime
# res = datetime(1970, 1, 1)
# print(res)
#
# birthday_list = [1944,3,1]
# timestamp = (datetime(birthday_list[0], birthday_list[1], birthday_list[2]) - datetime(1970, 1, 1))
# print(timestamp)

# self.local_path = os.path.join(config.BASE_FILE_DIR, "112", self.passport)
# # 判断返回的是否是文件夹/目录
# if os.path.isdir(self.local_path):

from datetime import datetime
birthday_list = [1966, 10, 6]
res = datetime(birthday_list[0], birthday_list[1], birthday_list[2]) - datetime(1970, 1, 1)
print(res)

听着楼下的小孩，玩耍吵闹的声音、好无忧无虑。想想孩子的忧虑，永远写不完的作业，不敢给家长看的成绩单，班主任的问话。在想想大人的忧虑那就可多了，上有老下有小，工作还得看领导。
在看看自己，周末给自己找了一个借口，绷得太紧，休息一下。躺了一天，甚是颓废，拿着手机刷着抖音（China hooray）、刷着朋友圈（无聊的广告）、追着剧（找不到看的电影）、打着游戏（以前的爱好）、做着90岁以后能做的事，是不是有点过分了。其实想说的是，我爱你中国。
