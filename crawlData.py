from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import re
from selenium.webdriver import ActionChains
import lxml.html
import selenium.webdriver.support.ui as ui
from selenium.webdriver import DesiredCapabilities
import configparser
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
from redis import StrictRedis,ConnectionPool
from requests.exceptions import RequestException
from urllib.parse import urlencode
import json
from redis import StrictRedis
import urllib.parse
from time import sleep,ctime
import threading
import time
def getSongUrl():
    songUrl = []
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=chrome_options)#声明浏览器对象
    matchList = []#方便下面存放获取的数据
    url = 'https://music.163.com/'#网易云
    # 设置一个很长的网页加载数据，省的有些情况还得滚动页面
    driver.set_window_size(1920,5000)
    try:
        driver.get(url)#输入url
        time.sleep(5)
        intput = driver.find_element(By.XPATH,'//*[@id="srch"]')#获取输入框节点
        intput.send_keys('浮生'+'\n')#输入想看的东西 因找不到搜索按钮，所以直接用转义字符代替
        #search = driver.find_element(By.XPATH,'//*[@id="g_search"]')
        time.sleep(10)
        print(driver.current_url)#当前在哪个页面
        current_url = driver.current_url
        driver.get(current_url) 
        iframe = driver.find_element_by_class_name('g-iframe')
        driver.switch_to.frame(iframe)
        html = driver.page_source#id=12205361">刘莱斯
        #select = re.findall(r'id=(.*?)>刘莱斯',html)
        #print(select[0])
        bsObj = BeautifulSoup(html, 'html.parser')
        dataId = bsObj.findAll(name = 'a', attrs = {'href':re.compile(r'/artist.id=\d{1,10}')})#匹配数字出现1次至10次
        artist = dataId[0]
        href = "http://music.163.com"+artist.attrs['href']
        print(href)
        driver.get(href)
        time.sleep(10)#
        iframe = driver.find_element_by_class_name('g-iframe')
        driver.switch_to.frame(iframe)
        htmlSong = driver.page_source
        bsObjSong = BeautifulSoup(htmlSong, 'html.parser')
        songList = bsObjSong.findAll(name = 'a', attrs = {'href':re.compile(r'/song.id=\d{1,10}')})
        for song in songList:
            print(song.attrs['href'])
            s = song.attrs['href']
            s = s.replace(s[:9],'',1)
            songUrl.append(s)
        driver.close()
        return songUrl
    except requests.ConnectionError as e:
        driver.close()
        print('Error',e.args)

def insertTo(name, data):
    redis.lpush(name,data)

def getAndSave(songId, limit, offset):
    #表示请求的url前半部分
    url = 'https://music.163.com/api/v1/resource/comments/R_SO_4_'+songId+'?'
    #参数
    fromData = {
        'limit':limit,
        'offset':offset,
    }
    #头文件
    header = {
        'Host' : 'music.163.com',
        'Referer' : 'https://music.163.com/song?',
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
        'X-Requested-With' : 'XMLHttpRequest',
    }
    #代理IP
    proxies = {
        'http:':'http://121.232.146.184',
        'https:':'https://144.255.48.197'
        }
    # 调用urlencode()方法将参数转化为URL的GET请求参数,与url合成新的URL
    url_1 = url + urlencode(fromData)
    try:
        response = requests.post(url_1,headers=header,proxies=proxies)
        if response.status_code == 200:
            #response.content返回的是一串json数据
            if offset == 0:
                for i in json.loads(response.content).get('hotComments'):
                    list_1 = {
                    'userId': i['user']['userId'],
                    'nickname': i['user']['nickname'],
                    'content': i['content'],
                    'likeCount': i['likedCount'],
                    'beReplied': len(i['beReplied']),
                    'imgUrl': i['user']['avatarUrl'],
                    'time': i['time']
                    }
                    data = json.dumps(list_1)
                    insertTo(songId,data)  
            for i in json.loads(response.content).get('comments'):
                list_1 = {
                'userId': i['user']['userId'],
                'nickname': i['user']['nickname'],
                'content': i['content'],
                'likeCount': i['likedCount'],
                'beReplied': len(i['beReplied']),
                'imgUrl': i['user']['avatarUrl'],
                'time': i['time']
                }
                data = json.dumps(list_1)
                insertTo(songId,data)
    except requests.ConnectionError as e:
            print('Error',e.args)
    sleep(5)
    global count
    count += 1

start = time.time()
print("开始时间："+str(start))
songId = getSongUrl()
count = 0
#用数据池连接Redis
pool = ConnectionPool(host='localhost',port=6379,db=5,decode_responses=True)
redis = StrictRedis(connection_pool=pool)
#threads=[]
for d in range(0,7):
    threads=[]
    for i in range(250):
        t1 = threading.Thread(target=getAndSave,args=(songId[d],20,i*20))
        threads.append(t1)
    for t2 in threads:
        t2.start()
    for t3 in threads:
        t3.join()#join（）方法的作用是调用线程等待该线程完成后，才能继续用下运行。
    print('第'+str(d)+'首歌曲完成')
end = time.time()
print("结束时间："+str(end))
print('耗费时间：'+str(end - start))
print("运行多少次："+str(count))