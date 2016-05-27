#-*-coding:utf-8 -*-

from urllib.request import urlopen
from bs4 import BeautifulSoup
import pymysql
import re
from time import time
from time import sleep
import datetime
from urllib.parse import urlparse
import logging

conn = None
cur = None
log = None

def getLog():
    global log
    if log is None:
        return openLog()
    return log

def openLog():
    global log
    log = open('log.log', encoding='UTF-8', mode='a')
    return log

def writeLog(message):
    logger = getLog()
    logger.write(message)
    logger.flush()

def getDb():
    global cur
    if dbIsActive():
        return cur
    openDb()
    return cur

def dbIsActive():
    global conn
    global cur
    if conn == None:
        return False
    #判断连接是否有效
    try:
        cur.execute('Show databases')
        if cur.rowcount == 0:
            return False
        return True 
    except Exception:
        conn = None
        cur = None
    return False

def openDb():
    global conn
    global cur
    if conn == None:
        conn = pymysql.connect(host="127.0.0.1", user="root", passwd="root", db="mysql", charset="utf8")
        cur = conn.cursor()
        cur.execute('USE scraping')

def getWebsites():
    cur = getDb()
    cur.execute('SELECT id, url FROM website')
    if cur.rowcount == 0:
        return None
    return cur.fetchall()

def insertScrapy(url, id, count=0):
    if count >= 3:
        return 1
    #对url进行解析，分析url的跟地址
    parse = urlparse(url)
    baseUrl = parse.scheme +'://' + parse.netloc
    currentUrl = parse.scheme +'://'+ parse.netloc + parse.path
    try:
        webFd = urlopen(url)
        bsObj = BeautifulSoup(webFd.read())
        webFd.close()
        title = bsObj.title
        if title is not None:
            title = title.getText()
            if title.strip()=='':
                print("Title is Empty:Skip") 
            else:
                created = int(time())
                date = datetime.datetime.now()
                date = date.strftime('%Y-%m-%d %H:%m')
                try:
                    cur = getDb()
                    cur.execute('INSERT INTO scraping (url, title, websiteId,created, strcreated) VALUES (%s,%s,%s,%s, %s)', (url, title, int(id), int(created), date))
                    conn.commit()
                    print('INSERT %s'%(title))
                    title = None
                except Exception as e:
                    print('Exception : %s' %(e))
                    title = None
                    sleep(5)
                    #return 
        else :
            print("%s Title is None"%(url))
        aTags = bsObj.findAll('a', {'href':re.compile('^.*[^\s]+.*$')})
        #aTags = bsObj.findAll('a')
        for aTag in aTags:
            href = aTag.attrs['href']
            if href == '' or href == '#':
                continue
            #编译url正则
            absolute = re.compile('^(http://|https://)')
            relative = re.compile('^/')
            javascript = re.compile('^(javascript:)')
            if absolute.match(href):
                pass
            elif relative.match(href):
                href = baseUrl + href
            elif javascript.match(href):
                continue
            else:
                href = currentUrl+href
            cur.execute('SELECT id FROM scraping WHERE url=%s',(href))
            if cur.rowcount == 0:
                times = count
                times = times+1
                insertScrapy(href, id, times)
            else:
                print('%s is exist'%(href))
    except Exception as e:
        print('Exception:%s'%(e))
        sleep(5)

def main():
    websites = getWebsites()
    for website in websites:
        date = datetime.datetime.now()
        date = date.strftime('%Y-%m-%d %H:%m:%S')
        url = website[1]
        id = website[0]
        writeLog(date+':scrapy root:' + url+"\n")
        insertScrapy(url, id)
        sleep(2)

if __name__ == '__main__':
    try:
        while  1:
            main()
            print('scrapy down:sleep a day')
            sleep(3600*24)
    except (Exception,KeyboardInterrupt) as e:
        print("Exception:%s"%(e))
        raise e
    finally:
        if log is not None:
            log.close()
        if conn is not None:
            conn.close()
    
