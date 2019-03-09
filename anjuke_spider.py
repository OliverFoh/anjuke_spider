import requests
from requests.exceptions import RequestException
import re
import time
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import string
import lxml
import gc
import spider_sql
import datetime
# 请求房屋信息页
def get_one_page(url):
    headers={
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
        }
    response=requests.get(url,headers=headers)
    if response.status_code==200:
        return response.text
    return None

#匹配房屋价格
def price(content,room_list):
    soup=BeautifulSoup(content,'lxml')
    result=soup.find_all(attrs={'class':'favor-pos'})
    try:
        for i in range(len(result)):
            if(result[i].find_all(attrs={'class':'price'})): #均价+价格+单元价格
                room_list[i]['price'] = int((result[i].find_all(attrs={'class':'price'})[0]).span.string)
                s1 = re.findall('"price">(.*?)<', str(result[i].find_all(attrs={'class':'price'})[0]), re.S)
                s2 = re.findall('</span>(.*?)<', str(result[i].find_all(attrs={'class':'price'})[0]), re.S)
                room_list[i]['avg_price'] = s1[0]
                room_list[i]['unit_price'] = s2[0]
            if(result[i].find_all(attrs={'class':'price-txt'})):#售价待定
                room_list[i]['price_txt']=result[i].find_all(attrs={'class':'price-txt'})[0].string
            if(result[i].find_all(attrs={'class':'favor-tag around-price'})):#周边均价+价格+单元价格
                room_list[i]['price'] =int((result[i].find_all(attrs={'class':'favor-tag around-price'})[0]).span.string)
                s3 = re.findall('price">(.*?)<', str(result[i].find_all(attrs={'class':'favor-tag around-price'})[0]), re.S)
                s4 = re.findall('</span>(.*?)<', str(result[i].find_all(attrs={'class':'favor-tag around-price'})[0]), re.S)
                s3[0]=re.sub('[\n\s]','',s3[0])
                s4[0]=re.sub('[\n\s]','',s4[0])
                room_list[i]['around_price'] = s3[0]
                room_list[i]['unit_price'] = s4[0]
        return room_list
    except:
        print('failed,准备爬取下一页...')

#提取房屋信息
def get_ifo(content):

    room_list=[]
    room={'city_name':None,
          'save_time':None,
        'name':None,
          'huxing':None,
          'size':None,
          'sale':None,
          'type':None,
          'address':None,
          'price_txt':None,
          'around_price':None,
          'avg_price':None,
          'price':None,
          'unit_price':None,
          'tag':None
          }
    soup=BeautifulSoup(content,'lxml')
    result=soup.find_all(attrs={'class':'infos'})
    if(result):
        for i in range(len(result)):  # 列表初始化
            room_new = room.copy()
            room_list.append(room_new)
            del room_new
            gc.collect()
        for i in range(len(result)):
            room_list[i]['name']=result[i].find_all(attrs={'class':'items-name'})[0].string     #房屋名称
            room_list[i]['address']=re.sub('[\xa0]','',result[i].find_all(attrs={'class':'list-map'})[0].string)   #房屋地址
            if(result[i].find_all(attrs={'class':'huxing'})):   #户型与大小
                huxing=result[i].find_all(attrs={'class': 'huxing'})[0]
                s=huxing.find_all(name='span')
                str = ''
                for k in s:
                    str += k.string
                for m in range(len(str)):
                    if (str[m] == '积'):
                        s1 = str[(m + 2):]
                        s2 = str[:(m - 3)]
                        break
                if(s2!=''):
                    room_list[i]['huxing'] = s2
                room_list[i]['size'] = s1
            if(result[i].find_all(attrs={'class':'tag-panel'})):
                tags=result[i].find_all(attrs={'class':'tag-panel'})[0]
                if(tags.find_all(attrs={'class':'status-icon wuyetp'})):
                    room_list[i]['type'] =tags.find_all(attrs={'class': 'status-icon wuyetp'})[0].string  # 房屋类型
                if(tags.find_all(attrs={'class':'status-icon onsale'})):#判断在售
                    room_list[i]['sale']=tags.find_all(attrs={'class':'status-icon onsale'})[0].string
                if(tags.find_all(attrs={'class':'status-icon forsale'})):#判断待售
                    room_list[i]['sale']=tags.find_all(attrs={'class':'status-icon forsale'})[0].string
                if(tags.find_all(attrs={'class':'status-icon soldout'})):
                    room_list[i]['sale'] = tags.find_all(attrs={'class':'status-icon soldout'})[0].string
                if(tags.find_all(attrs={'class':'tag'})):#房屋亮点
                    room_tag=[]
                    for n in tags.find_all(attrs={'class':'tag'}):
                        room_tag.append(n.string)
                    room_list[i]['tag']=room_tag
        return room_list,len(room_list)
    else:
        return None

#获取各个城市分站地址
def get_city(list_url):
    city_list=[]
    city_name={
        'name':None,
        'link':None,
        'num':None
    }
    content=get_one_page(list_url)
    soup=BeautifulSoup(content,'lxml')
    result = soup.find_all(attrs={'class':'city_list'})
    for i in range(len(result)):
        city=result[i].contents
        city_new=[]
        for j in range(len(city)):
            if(city[j]!='\n' and city[j]!=' '):
                city_name['name']=city[j].string
                city_name['link']=city[j].attrs['href']
                city_new.append(city_name.copy())
        city_list.append(city_new)
    return city_list

#城市网址拼接
def split_url(city_list):
    for i in range(len(city_list)):
        for j in range(len(city_list[i])):
            flag=city_list[i][j]['link'].index('.')
            s1=city_list[i][j]['link'][:flag]
            s2=city_list[i][j]['link'][flag:]
            s=s1+'.fang'+s2+'/loupan/all/'
            city_list[i][j]['link']=s
    return city_list
#指定城市
def exclude_url(list_link):
    link=[]
    #B
    link.append(list_link[1][0])#北京
    #C
    link.append(list_link[2][0])#成都
    link.append(list_link[2][1])#重庆
    link.append(list_link[2][2])#长沙
    link.append(list_link[2][4])#长春
    #D
    link.append(list_link[3][0])#大连
    link.append(list_link[3][1])#东莞
    #F
    link.append(list_link[5][0])#佛山
    link.append(list_link[5][1])#福州
    #G
    link.append(list_link[6][0])#广州
    link.append(list_link[6][1])#贵阳
    #H
    link.append(list_link[7][0])#杭州
    link.append(list_link[7][1])#合肥
    link.append(list_link[7][2])#哈尔冰
    link.append(list_link[7][3])#海口
    link.append(list_link[7][4])#惠州
    link.append(list_link[7][5])#呼和浩特
    #J
    link.append(list_link[8][0])#济南
    #k
    link.append(list_link[9][0])#昆明
    #L
    link.append(list_link[10][0])#兰州
    #N
    link.append(list_link[12][0])#南京
    #Q
    link.append(list_link[14][0])#青岛
    #S
    link.append(list_link[16][0])#上海
    link.append(list_link[16][1])#深圳
    link.append(list_link[16][2])#苏州
    link.append(list_link[16][3])#石家庄
    link.append(list_link[16][4])#三亚
    #T
    link.append(list_link[17][0])#天津
    #W
    link.append(list_link[18][0])#武汉
    #X
    link.append(list_link[19][0])#西安
    #Z
    link.append(list_link[21][0])#郑州
    return link
#获取当前城市与时间
def assignCityTime(room_list,city_name):
    for i in range(len(room_list)):
        room_list[i]['city_name']=city_name
        room_list[i]['save_time']=datetime.datetime.now().strftime('%F')
    return room_list
if __name__ == '__main__':
   ''' link_search=get_city('https://www.anjuke.com/sy-city.html')
    list_link=split_url(link_search)
    list_link=exclude_url(list_link)
    sum_count=0
    for m in range(len(list_link)):
        base_url=list_link[m]['link']
        count=0
        i=0
        while True:
            count_new=0
            i+=1
            params = 'p' + str(i) + '/'
            url = base_url + params
            content = get_one_page(url)
            if(content==None):
                break
            list1=get_ifo(content)
            if(list1==None):
                break
            list2=price(content,list1[0])
            count_new=list1[1]
            sum_count+=count_new
            count+=count_new
            print('总共已爬取%d条信息' % sum_count)
            print('已爬取%s%d条信息'%(list_link[m]['name'],count))
            assignCityTime(list2,list_link[m]['name'])
            spider_sql.wr_mysql(list2,'localhost','root','Fswmysql','spider_data')
            time.sleep(3)'''
   print(get_one_page('https://read.qidian.com/chapter/5bcpH7zSu_9wKI0S3HHgow2/O__Yc_7ekQS2uJcMpdsVgA2'))























#抓取猫眼电影排行
'''def get_one_page(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None


def parse_one_page(html):
    pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a'
                         + '.*?>(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>'
                         + '.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>', re.S)
    items = re.findall(pattern, html)
    for item in items:
        yield {
            'index': item[0],
            'image': item[1],
            'title': item[2],
            'actor': item[3].strip()[3:],
            'time': item[4].strip()[5:],
            'score': item[5] + item[6]
        }


def write_to_file(content):
    with open('result.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')


def main(offset):
    url = 'http://maoyan.com/board/4?offset=' + str(offset)
    html = get_one_page(url)
    for item in parse_one_page(html):
        print(item)
        write_to_file(item)


if __name__ == '__main__':
    for i in range(10):
        main(offset=i * 10)
        time.sleep(2)'''

