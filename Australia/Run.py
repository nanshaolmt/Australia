# import subprocess
# try:
#     subprocess.Popen("celery -A tasks worker -l info", shell=True)
# except KeyboardInterrupt:
#     print("用户退出")
# print("=== OVER ===")

from tasks import main
from time import sleep
ls = []
for j in range(5):
    sleep(1)
    ls.append(main.delay())


for i in ls:
    while not i.ready(): 
        print("i:", i)
        sleep(1)
    print(i.get())
""" 

activate aust
python Run.py

redis-cli -a 5678tyui

"""
