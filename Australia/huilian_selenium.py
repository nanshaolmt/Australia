
import json
import os
import subprocess
import time
# coding=utf-8
# 下载文件需要的lib
import urllib.request
# 时间转换模块
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import TimeoutException  # 导入所有的异常类
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

import settings
import config


def chromeOptions(noWin=False, noImg=False, pdf=False, download_dir=os.path.join(settings.BASEDIR, 'files')):
    # 设置 chrome_options 属性
    chrome_options = webdriver.ChromeOptions()
    # 设置浏览器窗口大小
    # chrome_options.add_argument('window-size=1800x2000')
    # 无界面
    # chrome_options.add_argument('--headless') if noWin else ""
    # 不加载图片
    chrome_options.add_argument('blink-settings=imagesEnabled=false') if noImg else ""
    # 设置代理
    # chrome_options.add_argument('--proxy-server=http://127.0.0.1:1080')
    #
    # ----------页面打印版pdf下载-----------------
    appState = {
        "recentDestinations": [
            {
                "id": "Save as PDF",
                "origin": "local"
            }
        ],
        "selectedDestinationId": "Save as PDF",
        "version": 2
    }
    # ----------网页版pdf直接下载-----------------
    profile = {
        "plugins.plugins_list": [{
            "enabled": False, "name": "Chrome PDF Viewer"
        }],  # Disable Chrome's PDF Viewer
        "download.default_directory": download_dir,
        "profile.default_content_settings.popups": 0,
        "download.extensions_to_open": "applications/pdf",
        'printing.print_preview_sticky_settings.appState': json.dumps(appState),
        # 'savefile.default_directory': download_dir
    }

    chrome_options.add_experimental_option('prefs', profile) if pdf else ""
    chrome_options.add_argument('--kiosk-printing')
    return chrome_options


class Tools():
    def __init__(self, *args, **kwargs):

        #kwargs
        self.logger = kwargs.get("logger", None)
        if not self.logger:
            self.logger = config.get_log("Tools")

    def is_empty(self, obj):
        if obj is None:
            return True
        pass
        if obj == 'None':
            return True
        pass
        if str(obj).strip() == '':
            return True
        pass
        return False
    pass

    def convertProvinceForAustralia(self, province):
        if self.is_empty(province):
            return ''
        if province == 'XIZANG':
            province = 'XIZANG ZIZHIQU'
        elif province == 'GUANGXI':
            province = 'GUANGXI ZHUANGZU ZIZHIQU'
        elif province == 'InnerMongolia':
            province = 'NEI MONGOL ZIZHIQU'
        elif province == 'NINGXIA':
            province = 'NINGXIA HUIZI ZIZHIQU'
        elif province == 'XINJIANG':
            province = 'XINJIANG UYGUR ZIZHIQU'
        elif province == 'SHANGHAI' or province == 'BEIJING' or province == 'TIANJIN' or province == 'CHONGQING':
            province = province + ' SHI'
        else:
            province = province + ' SHENG'
        return province
        pass

    def convertDateForAustralia(self, dateStr, splitstr='-'):
        '''dateStr 2017-07-06'''
        #---看传的时间 是不是空,或者是None
        if self.is_empty(dateStr):
            return ''
        return time.strftime("%Y-%m-%d", time.strptime(dateStr, "%Y-%m-%d"))
    pass


    #########start 获取文件路径、文件名、后缀名############
    def jwkj_get_filePath_fileName_fileExt(self, filename):
        (filepath, tempfilename) = os.path.split(filename)
        (shotname, extension) = os.path.splitext(tempfilename)
        return filepath, shotname, extension
    pass


class Huilian(object):
    """基于原生的 selenium 框架做了二次封装."""

    def __init__(self, driver, **kwargs):
        """启动浏览器参数化，默认启动 Chrom."""
        self.logger = kwargs.get("logger", None)
        if not self.logger:
            self.logger = config.get_log("huilian")

        if driver:
            self.driver = driver
        # else:
        #     chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chromedriver"
        #     self.driver = webdriver.Chrome(executable_path=chrome_path)

    def open(self, url, t='', timeout=10):
        '''
        使用 get 打开 url 后，最大化窗口，判断 title 符合预期
        Usage:
        driver = Huilian()
        driver.open(url,t='')
        '''
        if url != '-1':
            self.driver.get(url)
        # self.driver.maximize_window()
        try:
            WebDriverWait(self.driver, timeout).until(EC.title_contains(t))
        except TimeoutException:
            self.logger.debug("open %s title error" % url)
        except Exception as msg:
            self.logger.debug("Error:%s" % msg)
        pass

    @property
    def page(self):
        """ 返回网页源码 """
        return self.driver.page_source

    # 判断元素是否存在
    def is_element_exist(self, locator):
        try:
            s = self.find_element(locator, 3)
            return True
        except TimeoutException as e:
            self.logger.debug('未找到按钮...')
            return False
        pass
    pass

    def find_element_by_id(self, id):
        return self.driver.find_element_by_id(id)
        pass


    def find_element(self, locator, timeout=30, type=1):
        '''定位元素，参数
        locator 是元祖类型
        Usage:locator = ("id","xxx")
        driver.find_element(locator)
        CLASS_NAME = 'class name'
        CSS_SELECTOR = 'css selector'
        ID = 'id'
        LINK_TEXT = 'link text'
        NAME = 'name'
        PARTIAL_LINK_TEXT = 'partial link text'
        TAG_NAME = 'tag name'
        XPATH = 'xpath'
        '''

        # self.logger.info(( 'locators:'+str(locators) ))
        # element = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(*locator))
        # element = WebDriverWait(self.driver, 20).until(lambda x: x.find_element(*locator))
        # element = WebDriverWait(driver,10).until(self.driver.find_element(by=By.ID,value='su'))

        # 当我们不关心元素是否可见，只关心元素是否存在在页面中 presence_of_element_located
        if type == 1 or type == 2:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator))
                #----是否出现,符合条件的元素加载出来   (By.NAME, 'username')
        elif type == 3:
            # find_visibility_element 当我们需要找到元素，并且该元素也可见
            element = self.find_visibility_element(locator)
        pass
        # if locator[0] == "id" :
        #     elemet = self.driver.find_element_by_id(locator[1])
        # elif locator[0] == "name" :
        #     elemet = self.driver.find_element_by_name(locator[1])
        # elif locator[0] == "xpath" :
        #     elemet = self.driver.find_element_by_xpath(locator[1])
        # elif locator[0] == "css" :
        #     elemet = self.driver.find_element_by_css_selector(locator[1])
        # elif locator[0] == "class" :
        #     elemet = self.driver.find_element_by_class_name(locator[1])
        # elif locator[0] == "link" :
        #     elemet = self.driver.find_element_by_link_text(locator[1])
        # elif locator[0] == "partial_link" :
        #     elemet = self.driver.find_element_by_partial_link_text(locator[1])
        # elif locator[0] == "tag" :
        #     elemet = self.driver.find_element_by_tag_name(locator[1])
        return element

    # 等待并获取隐藏的元素
    def find_visibility_element(self, locator, timeout=60):
        '''等待并获取隐藏的元素
        定位元素，参数
        locator 是元组类型
        Usage:locator = ("id","xxx")
        driver.find_element(locator)
        CLASS_NAME = 'class name'
        CSS_SELECTOR = 'css selector'
        ID = 'id'
        LINK_TEXT = 'link text'
        NAME = 'name'
        PARTIAL_LINK_TEXT = 'partial link text'
        TAG_NAME = 'tag name'
        XPATH = 'xpath'

'title_contains

以下两个条件验证元素是否出现，传入的参数都是元组类型的locator，
如(By.ID, ‘kw’)
顾名思义，一个只要一个符合条件的元素加载出来就通过；
另一个必须所有符合条件的元素都加载出来才行 '




        '''
        element = WebDriverWait(self.driver, 60).until(
            EC.visibility_of_element_located(locator))


        return element


    def find_elements(self, locator, timeout=10):
        '''定位一组元素'''
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located(locator))
        except TimeoutException:
            elements = []
        # if locator[0] == "id" :
        #     elemet = self.driver.find_elements_by_id(locator[1])
        # elif locator[0] == "name" :
        #     elemet = self.driver.find_elements_by_name(locator[1])
        # elif locator[0] == "xpath" :
        #     elemet = self.driver.find_elements_by_xpath(locator[1])
        # elif locator[0] == "css" :
        #     elemet = self.driver.find_elements_by_css_selector(locator[1])
        # elif locator[0] == "class" :
        #     elemet = self.driver.find_elements_by_class_name(locator[1])
        # elif locator[0] == "link" :
        #     elemet = self.driver.find_elements_by_link_text(locator[1])
        # elif locator[0] == "partial_link" :
        #     elemet = self.driver.find_elements_by_partial_link_text(locator[1])
        # elif locator[0] == "tag" :
        #     elemet = self.driver.find_elements_by_tag_name(locator[1])

        return elements

    def click(self, locator, type=1):
        '''点击操作
        Usage:locator = ('id','xxx')
        driver.click(locator)
        '''
        element = self.find_element(locator, 10)
        if type == 1:
            if str(locator[0]) == 'name':
                js = f'document.getElementsByName("{locator[1]}")[0].click()'
                self.js_execute(js)
            elif str(locator[0]) == 'id':
                js = f'document.getElementById("{locator[1]}").click()'
                self.js_execute(js)
            else:
                element.click()
        else:
            element.click()
        pass

    def e_click(self, locator):
        element = self.find_element(locator, 30)
        element.click()
    pass

    def visibility_click(self, locator):
        '''等待隐藏按钮出现后,点击操作
        '''
        element = self.find_element(locator, 30, 3)
        element.click()

    def double_click(self, locator):
        '''双击
        Usage:locator = ("id","xxx")
        driver.click(locator)
        '''
        element = self.find_element(locator)
        ActionChains(self.driver).double_click(element).perform()
        pass

    def context_click(self, locator):
        '''右键
        Usage:locator = ("id","xxx")
        driver.click(locator)
        '''
        element = self.find_element(locator)
        ActionChains(self.driver).context_click(element).perform()
        pass

    def elem_send_keys(self, element, text):
        """ 根据已有元素发送字符 """
        element.clear()
        element.send_keys(text)

    def send_keys(self, locator, text, type=1):
        '''
        type == 1 js 优先,type == 2是等待按钮,type == 3 是等待隐藏按钮
                        収送文本，清空后输入
        Usage:
        locator = ("id","xxx")   (By.NAME, 'username')
        driver.send_keys(locator, text)
        '''
        element = self.find_element(locator, 30, type)
        element.clear()
        element.send_keys(text)

    def send_keys_wait(self, locator, text):
        """ 等待元素可点击后发送 """
        self.is_clickable_time(locator)
        self.send_keys(locator, text)

    def is_text_in_element(self, locator, text, timeout=10):
        '''判断文本在元素里,没定位到元素返回 False，定位到元素返回判断结果布尔值result = driver.text_in_element(locator, text)'''
        try:
            result = WebDriverWait(self.driver, timeout).until(
                EC.text_to_be_present_in_element(locator, text))
        except TimeoutException:
            self.logger.debug("元素没定位到：%s" % str(locator))
            return False
        else:
            return result
        pass

    def is_text_in_value(self, locator, value, timeout=10):
        ''' 判断元素的 value 值，没定位到元素返回 false,定位到返回 判断结果布尔值 result = driver.text_in_element(locator, text)'''
        try:
            result = WebDriverWait(self.driver, timeout).until(
                EC.text_to_be_present_in_element_value(locator, value))
        except TimeoutException:
            self.logger.debug("元素没定位到：%s" % str(locator))
            return False
        else:
            return result
        pass

    def is_title(self, title, timeout=10):
        '''判断 title 完全等于'''
        result = WebDriverWait(self.driver, timeout).until(EC.title_is(title))
        return result

    def is_title_contains(self, title, timeout=10):
        '''判断 title 包括'''
        result = WebDriverWait(self.driver, timeout).until(
            EC.title_contains(title))
        return result

    def is_selected(self, locator, timeout=10):
        '''判断元素被选中，返回布尔值,'''
        result = WebDriverWait(self.driver, timeout).until(
            EC.element_located_to_be_selected(locator))
        return result

    def is_selected_be(self, locator, selected=True, timeout=10):
        '''判断元素的状态，selected 是期望的参数 true/False 返回布尔值'''
        result = WebDriverWait(self.driver, timeout).until(
            EC.element_located_selection_state_to_be(locator, selected))
        return result

    def is_alert_present(self, timeout=10):
        '''判断页面是否有 alert，返回回 alert(注意返里是返回 alert,不是 True)没有返回 False'''
        result = WebDriverWait(self.driver, timeout).until(
            EC.alert_is_present())
        return result

    def is_visibility(self, locator, timeout=10):
        '''元素可见返回本身，不可见返回 Fasle'''
        result = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator))
        return result

    def is_invisibility(self, locator, timeout=10):
        '''元素可见返回本身，不可见返回 True，没找到元素也返回 True'''
        result = WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(locator))
        return result

    def is_clickable(self, locator, timeout=1):
        '''元素可以点击 is_enabled 返回本身，不可点击返回 Fasle'''
        try:
            result = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator))
        except TimeoutException:
            result = False
        return result

    def is_clickable_time(self, locator, timeout=10):
        """
        在 timeout 秒内判断元素是否可以被选中
        """
        # time.sleep(1)
        for _ in range(timeout):
            if self.is_clickable(locator):
                return True
            time.sleep(0.1)
        return False

    def is_located(self, locator, timeout=10):
        '''判断元素有没被定位到（幵元意味着可见），定位到返回 element,没定位到返回 False'''
        result = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator))
        return result

    def move_to_element(self, locator):
        '''鼠标悬停操作
        Usage:
        locator = ("id","xxx")
        driver.move_to_element(locator)
        '''
        element = self.find_element(locator)
        ActionChains(self.driver).move_to_element(element).perform()

    def back(self):
        """
        Back to old window.
        Usage:driver.back()
        """
        self.driver.back()

    def forward(self):
        '''Forward to old window.Usage:driver.forward()'''
        self.driver.forward()

    def close(self):
        ''' Close the windows.  Usage: driver.close() '''
        self.driver.close()

    def quit(self):
        ''' Quit the driver and close all the windows.Usage:driver.quit()'''
        self.driver.quit()

    def get_title(self):
        '''获取 title'''
        return self.driver.title

    def get_current_url(self):
        '''获取 url'''
        return self.driver.current_url

    def get_text(self, locator):
        '''获取文本'''
        element = self.find_element(locator)
        return element.text

    def get_attribute(self, locator=None, element=None, name=None):
        '''获取属性'''
        if locator:
            element = self.find_element(locator)
        return element.get_attribute(name)

    def js_execute(self, js):
        '''执行 js'''
        return self.driver.execute_script(js)

    def js_focus_element(self, locator):
        '''聚焦元素'''
        target = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView();", target)

    def js_scroll_top(self):
        '''滚动到顶部'''
        js = "window.scrollTo(0,0)"
        self.driver.execute_script(js)

    def js_scroll_end(self):
        '''滚动到底部'''
        js = "window.scrollTo(0,document.body.scrollHeight)"
        self.driver.execute_script(js)

    def select_by_index(self, locator, index, element=None):
        '''通过索引,index 是索引第几个，从 0 开始'''
        self.is_clickable_time(locator)
        element = self.find_element(locator)
        Select(element).select_by_index(index)

    def select_by_value(self, locator, value, element=None):
        '''通过 value 属性'''
        self.is_clickable_time(locator)
        element = self.find_element(locator)
        Select(element).select_by_value(value)

    def select_by_text(self, locator, text, element=None):
        '''通过文本值定位'''
        self.is_clickable_time(locator)
        element = self.find_element(locator)
        #select  的使用  根据文本值选择

        Select(element).select_by_visible_text(text)

    def select_by_text_60(self, locator, text, element=None):
        '''通过文本值定位'''
        self.is_clickable_time(locator)
        element = self.find_element(locator, 60)
        #
        Select(element).select_by_visible_text(text)

    # 等待隐藏元素出现并选择
    def select_visibility_by_text(self, locator, text, element=None):
        """ 等待隐藏元素出现并选择
        通过文本值定位
        """
        self.is_clickable_time(locator)
        element = self.find_element(locator, 30, 3)
        Select(element).select_by_visible_text(text)

    def select_has_element(self, element, **kwargs):
        """  """
        ids = element.get_attribute("id")
        locator = ("id", ids)
        self.is_clickable_time(locator)
        if kwargs.get("index"):
            Select(element).select_by_index(kwargs.get("index"))
        elif kwargs.get("value"):
            Select(element).select_by_value(kwargs.get("value"))
        elif kwargs.get("text"):
            Select(element).select_by_text(kwargs.get("text"))
        elif kwargs.get("text_60"):
            Select(element).select_by_text_60(kwargs.get("text_60"))
        elif kwargs.get("visibility"):
            Select(element).select_by_visibility(kwargs.get("visibility"))

    def get_screenshot_as_file(self, savepath):
        '''通过文本值定位 "D:\\Program Files\\NM.bmp"'''
        self.driver.get_screenshot_as_file(savepath)
        pass

    def screenshot_as_png(self, locator, type=1):
        '''截屏'''
        element = self.find_element(locator, 30, type)
        return element.screenshot_as_png()
