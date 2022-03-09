# -*- coding: utf-8 -*-
import qbittorrentapi
import time
import sys
from datetime import datetime
import feedparser
import time
import urllib
from pymongo import MongoClient

sys.getdefaultencoding()

#MongoDB Connect
client = MongoClient(host=['localhost'],username='rss',password='rssrss',authMechanism='SCRAM-SHA-1',authSource='mydb')
db = client['mydb']

#Get Master data
masterdata = db.data.find().next()

#download RssFeed
def downloadRssFeed(url,category2,tags):
    try:
        print("CATE:"+category2 + " TAGS:"+tags +" URL:"+url)
        d = feedparser.parse(url)
        for item in d.entries:
            #item
            # ['title', 'title_detail', 'links', 'link', 'id', 'guidislink', 'published', 'published_parsed', 'nyaa_seeders', 'nyaa_leechers', 'nyaa_downloads', 'nyaa_infohash', 'nyaa_category2id', 'nyaa_category2', 'nyaa_size', 'nyaa_comments', 'nyaa_trusted', 'nyaa_remake', 'summary', 'summary_detail']
            item['tags'] = tags
            item['category2'] = category2
            result = db.torrents.update_one({
                "nyaa_infohash": item['nyaa_infohash']
                },{"$set":item},upsert=True)  
            
            if result.modified_count == 1 and result.matched_count == 0:
                db.data.update_one({"_id": masterdata["_id"]},{"$set":
                        {
                            "DATE":{
                                "value":datetime.now(),
                                category2+"DATE":{
                                    "value":datetime.now(),
                                    tags:datetime.now()
                                }
                            }
                        }
                    }
                )
            else:
                db.data.update_one({"_id": masterdata["_id"]},{"$set":{"CHECKDATE":datetime.now()}})
    except qbittorrentapi.LoginFailed as e:
        print(e)
    except urllib.error.URLError as e2:
        print(e2)

def downloadAVRssFeed(url,category2,tags):
    try:
        print("CATE:"+category2 + " TAGS:"+tags +" URL:"+url)
        d = feedparser.parse(url)
        for item in d.entries:
            db = client['mydb']
            #item
            # ['title', 'title_detail', 'links', 'link', 'id', 'guidislink', 'published', 'published_parsed', 'nyaa_seeders', 'nyaa_leechers', 'nyaa_downloads', 'nyaa_infohash', 'nyaa_category2id', 'nyaa_category2', 'nyaa_size', 'nyaa_comments', 'nyaa_trusted', 'nyaa_remake', 'summary', 'summary_detail']
            item['category2'] = category2
            item['tags'] = tags
            result = db.torrentsav.update_one({
                "nyaa_infohash": item['nyaa_infohash']
                },{"$set":item},upsert=True)  

            if result.modified_count == 1 and result.matched_count == 0:
                db.data.update_one({"_id": masterdata["_id"]},{"$set":
                        {
                            "DATE":{
                                "value":datetime.now(),
                                category2+"DATE":{
                                    "value":datetime.now(),
                                    tags:datetime.now()
                                }
                            }
                        }
                    }
                )
            else:
                db.data.update_one({"_id": masterdata["_id"]},{"$set":{"CHECKDATE":datetime.now()}})
    except qbittorrentapi.LoginFailed as e:
        print(e)
    except urllib.error.URLError as e2:
        print(e2)


print("start")
from datetime import datetime
now = datetime.now()
current_time = now.strftime("%Y/%m/%d %H:%M:%S")
print(current_time)
#HANIME
downloadRssFeed('https://sukebei.nyaa.si/?page=rss&c=1_1&f=0&u=hikiko123','HANIME','HANIME')

#COMIC
for rssurl in masterdata["COMIC"]:
    downloadRssFeed('https://sukebei.nyaa.si/?page=rss&q=COMIC+'+urllib.parse.quote(rssurl)+'&c=1_4&f=2','COMIC',rssurl)

#DOUGIN(NAMED)
for rssurl in masterdata["DOUGIN"]:
    downloadRssFeed('https://sukebei.nyaa.si/?page=rss&q=%22%5B'+urllib.parse.quote(rssurl)+'%5D%22&c=1_2&f=2','DOUGIN',rssurl)


#NAMED(MANGA)
for rssurl in masterdata["NAMED"]:
    downloadRssFeed('https://sukebei.nyaa.si/?page=rss&q=%22%5B'+urllib.parse.quote(rssurl)+'%5D%22&c=1_4&f=2','NAMED',rssurl)

#AV
for rssurl in masterdata["AV"]:
    downloadAVRssFeed('https://sukebei.nyaa.si/?page=rss&q=%22Uncensored%22+%22'+urllib.parse.quote(rssurl)+'%22&c=2_2&f=2','AV',rssurl)
