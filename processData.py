from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from redis import StrictRedis,ConnectionPool
import json
import time
import pandas as pd
from pyecharts import Line, Bar, Pie, Geo#制作Echart表
from collections import Counter#统计次数
import threading
import requests
from requests.exceptions import ReadTimeout, ConnectionError
from urllib.parse import urlencode
import urllib.parse
import re#截取
#用数据池连接Redis
pool = ConnectionPool(host='localhost',port=6379,db=5,decode_responses=True)
redis = StrictRedis(connection_pool=pool)
songKeys = redis.keys()
songTime = []#最开始获取的评论时间
songUserId = []#评论者id
songContentPath = 'songContent.txt'
with open(songContentPath,'w',encoding='utf-8') as file:
    for i in range(len(songKeys)):
        songId = songKeys[i]
        songLength = redis.llen(songId)#键长度
        for i in range(songLength):
            data_1 = redis.lindex(songId,i)
            data_2 = json.loads(data_1)
            content = data_2['content'].encode('GBK','ignore').decode('GBK')
            songTime.append(data_2['time'])
            songUserId.append(data_2['userId'])
            file.write(content)
            #print(data_2)
    file.close()

#制作词云图
bg_mask = np.array(Image.open('img.jpg'))
text = open(songContentPath, encoding='utf-8').read()
my_wordcloud = WordCloud(background_color='white',
                         mask=bg_mask,
                         max_words=2000, # 设置最大显示的字数
                         font_path=r'C:\Windows\Fonts\STZHONGS.TTF', #设置中文字体，使的词云可以显示
                         max_font_size=250, # 设置最大字体大小
                         random_state=30, # 设置有多少种随机生成状态,即有多少种配色方案
                         )
myword = my_wordcloud.generate(text)
plt.imshow(myword)
plt.axis('off')
plt.show()

#评论时间分析 可视化
#经过处理的时间
timeHMS = []
for i in range(len(songTime)):
    date = time.localtime(int(str(songTime[i])[:10]))
    date = time.strftime("%Y-%m-%d %H:%M:%S", date)
    #print(date)时间大多都集中在2018年4月到2019年5月
    date = date[:7]
    timeHMS.append(date)
result = Counter(timeHMS) #result类型<class 'collections.Counter'>
'''
#按照value排序时，只需把key迭代对象选择为x[1]就可以了。
sorted_dict = sorted(result.items(), key=lambda x:x[1], reverse=True)
print(sorted_dict)
#通过list将字典中的keys和values转化为列表
keys = list(sorted_dict.keys())
values = list(sorted_dict.values())'''
time_1 = ['2018-04','2018-05','2018-06','2018-07','2018-08','2018-09','2018-10','2018-11','2018-12','2019-01','2019-02','2019-03','2019-04','2019-05','2019-06']
time_2 = []
for i in time_1:
    if i in result.keys():
        time_2.append(result[i])
    else:
        time_2.append('0')
print(time_2)
bar = Bar("评论时间概率表")
bar.add("时间",time_1,time_2)
bar.show_config()
bar.render('评论时间概率表.html')#自动生成一个叫render.html文件，当然也可以自定义名字

#获取评论者的地区信息，制作地区分布图
userProvince = []#省份
userAge = []#年龄
userSex = []#性别
userFolloweds = []#粉丝数
userFollows = []#关注人数
def reJson(url):
    #头文件
    header = {
        'Host' : 'music.163.com',
        'Connection': "keep-alive",
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
        'X-Requested-With' : 'XMLHttpRequest',
    }
    #代理IP
    proxies = {
        'http:':'http://121.232.146.184',
        'https:':'https://144.255.48.197'
        }
    try:
        response = requests.get(url,headers=header,proxies=proxies)
        if response.status_code == 200:
            data = response.json()
            #print(data)验证是否抓取到数据
            data = data.get('profile')
            userProvince.append(str(data['province']))#省份
            #将其转化为年龄
            age_time = data['birthday']
            age = (2019-1970) - (int(age_time)/(1000*365*24*3600))
            age = re.findall(r'\d{1,3}',str(age))
            userAge.append(age[0])#年龄
            userSex.append(str(data['gender']))#性别
            userFolloweds.append(data['followeds'])
            userFollows.append(data['follows'])
    except requests.ConnectionError as e:
            print('Error',e.args)

def getUserTotal(*arges):
    userIdUrl = []
    for i in arges:
        url = 'https://music.163.com/api/v1/user/detail/'+str(i)
        reJson(url)
        print("第"+str(i)+"位评论者的信息获取完成")
threads=[]
for i in range(len(songUserId)):
    t1 = threading.Thread(target=getUserTotal,args=(songUserId[i],))
    threads.append(t1)
for t2 in threads:
    t2.start()
for t3 in threads:
    t3.join()   

#制作性别比例饼图
result = Counter(userSex)
sex_1 = ['1','2','0']
sex_2 = []
for s in sex_1:
    if s in result.keys():
        sex_2.append(result[s])
    else:
        sex_2.append('0')
pie = Pie('性别饼图比例','1男生.2女生.0未知')
pie.add('性别饼图比例', sex_1, sex_2, is_label_show=True)
pie.render('sex.html')

#制作年龄分布
age_1 = ['00后','95后','90后','80后','80前']
age_2 = []
dic_3 = {}
for age in userAge:
    s0 = '00后'
    s1 = '95后'
    s2 = '90后'
    s3 = '80后'    
    s4 = '80前'    
    if(int(age) <= 19):#00后
        if s0 in dic_3.keys():
            dic_3[s0] = dic_3[s0]+1
        else:
            dic_3[s0] = 1
    elif(int(age) <= 24):
        if s1 in dic_3.keys():
            dic_3[s1] = dic_3[s1]+1
        else:
            dic_3[s1] = 1
    elif(int(age) <= 29):
        if s2 in dic_3.keys():
            dic_3[s2] = dic_3[s2]+1
        else:
            dic_3[s2] = 1
    elif(int(age) <= 39):
        if s3 in dic_3.keys():
            dic_3[s3] = dic_3[s3]+1
        else:
            dic_3[s3] = 1
    else:
        if s4 in dic_3.keys():
            dic_3[s4] = dic_3[s4]+1
        else:
            dic_3[s4] = 1
print(dic_3)
for i in age_1:
    if i in dic_3.keys():
        age_2.append(str(dic_3[i]))
    else:
        age_2.append('0')
line =Line("年龄分布折线图")
line.add("年龄", age_1, age_2, mark_point=["average"])
line.show_config()
line.render('age.html')

#制作地区分布
result = Counter(userProvince)
print(result)
pKeys = []
pValues = []
proList = []
for n, m in result.items():
    pKeys.append(n)
    pValues.append(m)
print(pKeys)
print(pValues)
pName = []#地区名
for p in pKeys:
    if result[p] >= 800:
        if p == '110000':
            pName.append('北京11')
        elif p == '330000':
            pName.append('浙江33')
        elif p == '340000':
            pName.append('安徽34')
        elif p == '420000':
            pName.append('湖北42')
        elif p == '430000':
            pName.append('湖南43')
        elif p == '370000':
            pName.append('山东37')
        elif p == '320000':
            pName.append('江苏32')
        elif p == '410000':
            pName.append('河南41')
        elif p == '430000':
            pName.append('湖南43')
        elif p == '440000':
            pName.append('广东44')
        elif p == '500000':
            pName.append('重庆50')
        elif p == '510000':
            pName.append('四川51')
        elif p == '610000':
            pName.append('陕西61')
        else:
            print('很神秘')
print(pName)
pNameValues = []#地区数
for v in pName:
    print(str(v[2:]))
    num = str(v[2:])+'0000'
    pNameValues.append(result[num])
print(pNameValues)
#制作地区分布
data = [('北京', 11),('上海', 31),('湖南', 43), ('重庆', 50), ('江苏', 32), ('湖北', 42), ('河南', 41), ('四川', 51), ('陕西', 61), ('山东', 37), ('广东', 44),('安徽', 34),('浙江', 33),('云南', 53),('江西',36),('河北',13),('福建',35),('辽宁',21),('山西',14),('贵州',52),('黑龙江',23),('甘肃',62),('宁夏',64),('青海',63),('广西',45)]#标记省份坐标
geo =Geo("评论者的地区分布", "data from User", title_color="#fff", title_pos="center", width=1200, height=600, background_color='#404a59')
attr, value =geo.cast(data)
geo.add("", attr, value, type="effectScatter", is_random=True, effect_scale=5)
geo.show_config()
geo.render('userProvince.html')#花费时长[Finished in 422.5s]