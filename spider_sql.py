import time
import pymysql
#写入mysql
def wr_mysql(room_list,host,user,password,database):
    db = pymysql.connect(host,user,password,database)
    cursor = db.cursor()
    sql1="create table if not exists anjuke_house(城市 varchar(10),时间 varchar(15),名称 varchar(30),户型 varchar(20),大小 varchar (20),状态 varchar(10),类型 varchar(5),地址 varchar(50),价格说明 varchar (10),周边均价 varchar (10),价格标准 char(5),价格 int,单元价格 char(10),房屋亮点 varchar(50),primary key (名称,时间))ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1"
    sql2="insert into anjuke_house values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql1)
    try:
        list1=[]
        for i in range(len(room_list)):
            tuple1=(room_list[i]['city_name'],room_list[i]['save_time'],room_list[i]['name'],str(room_list[i]['huxing']),str(room_list[i]['size']),str(room_list[i]['sale']),str(room_list[i]['type']),room_list[i]['address'],str(room_list[i]['price_txt']),
                    str(room_list[i]['around_price']),str(room_list[i]['avg_price']),room_list[i]['price'],str(room_list[i]['unit_price']),str(room_list[i]['tag']))
            list1.append(tuple1)
        cursor.executemany(sql2,list1)
        db.commit();
        print('写入成功')
    except Exception as e:
        db.rollback()
        print('写入失败')
        print(e)
    db.close()

