from random import choice, randint

from pymysql import connect

from randsite.randPage import RandomSite


def getConfInfo(section):
    try:
        host = section["IP地址"]
        port = section["端口"]
        user = section["用户"]
        password = section["密码"]
        db = section["库名"]
    except KeyError as e:
        print("配置文件未找到%s项\n程序退出" % e)
    else:
        return host, port, user, password, db


def connDB(host, port, user, password, db):
    try:
        conn = connect(host=host, port=int(port), user=user, password=password, db=db)
    except BaseException as e:
        print("数据库连接失败：%s" % e)
        print("请检查原因重新运行程序")
        input("按下Enter键结束程序...")
        exit(0)
    else:
        cursor = conn.cursor()
        print("数据库连接成功")
        return conn, cursor


def modify(host, port, user, password, db):
    conn, cursor = connDB(host, port, user, password, db)

    sql = "SELECT vod_id, vod_actor, vod_director FROM mac_vod WHERE vod_pwd_down='';"
    cursor.execute(sql)

    # usql = "UPDATE mac_vod SET vod_name=%s, vod_blurb=%s, vod_content=%s,vod_pwd_down='1' WHERE vod_id=%s"
    # values = []
    for line in cursor.fetchall():
        # print(line)
        p = rs.genIntro(randint(200, 500)).replace("'", "").replace('"', "")
        # values.append((choice(rs.bk), p[:100], p, line[0]))
        sql = "UPDATE mac_vod SET "
        sql += "vod_name='%s'," % choice(rs.whiteKeywords)
        if not line[1]:
            sql += "vod_actor='%s'," % choice(rs.whiteKeywords)
        if not line[2]:
            sql += "vod_director='（编导）%s'," % choice(rs.whiteKeywords)
        sql += "vod_blurb='%s'," % p[:100]
        sql += "vod_content='%s',vod_pwd_down='1' WHERE vod_id='%s';" % (p, line[0])

        try:
            cursor.execute(sql)
        except Exception as e:
            print(e)
        print(line[0])


def main():
    # input("按下Enter键开始程序...")
    for section in rs.config.sections():
        if section.startswith("修改"):
            try:
                host, port, user, password, db = getConfInfo(rs.config[section])
            except Exception as e:
                print(section, e)
                continue
            modify(host, port, user, password, db)


if __name__ == '__main__':
    rs = RandomSite()
    main()
