# _*_ coding=utf-8 _*_

import json
import os
import sys
import time
import requests
import config


headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"
    }

class FileTools():

    '''图片转PDF'''
    errinfo = []

    def __init__(self, *args, **kwargs):
        self.logger = kwargs.get("logger", None)
        self.user = kwargs.get("user", "")
        if not self.logger:
            self.logger = config.get_log("filetools")

    '''下载文件'''
    def down_file(self, url, local_path, app_id, now_down_index, count):
        # 检查目录是否存在,不存在就创建目录
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        pass
        self.app_id = app_id
        self.local_path = local_path
        self.filedir = local_path.replace("\\\\", "\\").split("\\")[-1]
        filepath, shotname, extension = self.jwkj_get_filePath_fileName_fileExt(url)
        self.filename = shotname + extension
        # self.filename = "{}_{}.jpg".format(self.filedir, now_down_index)
        self.now_down_index = now_down_index
        self.count = count
        local = os.path.join(self.local_path, self.filename)
        while 1:
            try:
                # urllib.request.urlretrieve(url, local, self.Schedule)
                # url = 'http://qiniuyun.mobtop.com.cn/jpg1556419173_65631103.jpg'
                # request = urllib.request.Request(url, headers=header)
                # response = urllib.request.urlopen(request)
                # url = url + '?imageMogr2/auto-orient/interlace/1'
                response = requests.get(url, headers=headers, timeout=20)
                if response.status_code == 200:
                    with open(local, "wb") as f:
                        print(f"save ->{local}")
                        f.write(response.content)
                        break
                # response.close()
            except requests.exceptions.ConnectionError:
                print('ConnectionError -- please wait 1 seconds')
                time.sleep(1)
            except requests.exceptions.ChunkedEncodingError:
                print('ChunkedEncodingError -- please wait 1 seconds')
                time.sleep(1)
            except:
                print('Unfortunitely -- An Unknow Error Happened, Please wait 1 seconds')
                time.sleep(1)
            # except urllib.error.URLError:
            #     errinfo = {
            #         "errmsg": f"下载文件 {self.filedir + self.filename} 失败",
            #         "url": url,
            #         "local_path": self.local_path,
            #         "filedir": self.filedir,
            #         "filename": self.filename,
            #     }
            #     self.logger.error(errinfo["errmsg"])
            #     self.errinfo.append(errinfo)
            time.sleep(0.3)
    pass

    '''获取文件路径、文件名、后缀名'''

    def jwkj_get_filePath_fileName_fileExt(self, filename):
        (filepath, tempfilename) = os.path.split(filename)
        (shotname, extension) = os.path.splitext(tempfilename)
        return filepath, shotname, extension
    pass

    '''下载输出百分比'''

    def Schedule(self, dbnum, dbsize, size):
        # dbnum:已经下载的数据块
        # dbsize:数据块的大小
        # size:远程文件的大小
        # print_true = False
        per = 100.0 * dbnum * dbsize / size
        if per < 100:
            print(
                '\rINFO huilian_file_tools[line:{}]    {}[{}][({}/{})({}) === {: >6.2f}%] {}'.format(
                    str(sys._getframe().f_lineno),
                    self.user,
                    self.app_id,
                    self.now_down_index,
                    self.count,
                    self.filename,
                    per,
                    self.filedir
                ),
                end="\r"
            )
        elif per >= 100:
            per = 100
            print("\r", end="\r")
            self.logger.info('{}[{}][({}/{})({}) === {: >6.2f}%] {}'.format(self.user, self.app_id, self.now_down_index, self.count, self.filename, per, self.filedir))
        pass
        # if per >= 20 and per < 21:
        #     print_true = True
        # # elif per >= 40 and per < 41:
        #     # print_true = True;
        # elif per >= 60 and per < 61:
        #     print_true = True
        # # elif per >= 80 and per < 81:
        #     # print_true = True;
        # elif per >= 100:
        #     print_true = True
        # pass
        # if print_true:
        #     self.logger.info('{}[{}][({}/{})({}) === {:.2f}] {}'.format(self.user, self.app_id, self.now_down_index, self.count, self.filename, per, self.filedir))
        #     sys.stdout.flush()
        # pass
