# -*- coding: utf-8 -*-
import qbittorrentapi
import time
import sys
import json
from datetime import datetime
import os
import feedparser
import time
import urllib
from pymongo import MongoClient

sys.getdefaultencoding()

##MongoDB Connect
#client = MongoClient(host=['localhost'],username='rss',password='rssrss',authMechanism='SCRAM-SHA-1',authSource='admin')
client = MongoClient(host=['localhost'],username='rss',password='rssrss',authMechanism='SCRAM-SHA-1',authSource='mydb')
db = client['mydb']

##qBittorrent Connect
qbt_client = qbittorrentapi.Client(host='192.168.50.64', port=8080, username='admin', password='adminadmin')

def downloadRssFeed(url,category2,tags):
    try:
        print("parse start")
        d = feedparser.parse(url)
        print("parse end")
        for item in d.entries:
            db = client['mydb']
            #item
            # ['title', 'title_detail', 'links', 'link', 'id', 'guidislink', 'published', 'published_parsed', 'nyaa_seeders', 'nyaa_leechers', 'nyaa_downloads', 'nyaa_infohash', 'nyaa_category2id', 'nyaa_category2', 'nyaa_size', 'nyaa_comments', 'nyaa_trusted', 'nyaa_remake', 'summary', 'summary_detail']
            item['tags'] = tags
            item['category2'] = category2
            db.torrents.update_one({
                "nyaa_infohash": item['nyaa_infohash']
                },{"$set":item},upsert=True)  
               
        print('END:'+ url)
    except qbittorrentapi.LoginFailed as e:
        print(e)
    except urllib.error.URLError as e2:
        print(e2)


def downloadAVRssFeed(url,category2,tags):
    try:
        d = feedparser.parse(url)
        for item in d.entries:
            db = client['mydb']
            #item
            # ['title', 'title_detail', 'links', 'link', 'id', 'guidislink', 'published', 'published_parsed', 'nyaa_seeders', 'nyaa_leechers', 'nyaa_downloads', 'nyaa_infohash', 'nyaa_category2id', 'nyaa_category2', 'nyaa_size', 'nyaa_comments', 'nyaa_trusted', 'nyaa_remake', 'summary', 'summary_detail']
            item['category2'] = category2
            item['tags'] = tags
            db.torrentsav.update_one({
                "nyaa_infohash": item['nyaa_infohash']
                },{"$set":item},upsert=True)  
               
        print('END:'+ url)
    except qbittorrentapi.LoginFailed as e:
        print(e)
    except urllib.error.URLError as e2:
        print(e2)


##Download New Rss To qBittorrent
def downloadRss():
    try:
        count=0
        for item in db.torrents.find(projection = {'nyaa_infohash':1,'link':2,'category2':3,'tags':4,'download_status':5},filter={"download_status" : { "$exists" : False } }):
            count += 1
            time.sleep(1)
            qbt_client.torrents.add(urls=item['link'], category=item['category2'],use_auto_torrent_management=False,tags=item['tags'])
        

        for item in db.torrentsav.find(projection = {'nyaa_infohash':1,'link':2,'category2':3,'tags':4,'download_status':5},filter={"download_status" : { "$exists" : False } }):
            count += 1
            time.sleep(1)
            qbt_client.torrents.add(urls=item['link'], category=item['category2'],use_auto_torrent_management=False,tags=item['tags'])

        print(str(count)+'건 신규등록')

    except qbittorrentapi.LoginFailed as e:
        print(e)


#Check Rss Feed add to Qbit
def checkDownloadAdded():
    try:
        count = 0
        regCount = 0
        for item in db.torrents.find(projection = {'nyaa_infohash':1,'link':2,'category2':3,'tags':4,'download_status':5},filter={"download_status" : { "$exists" : False } }):
            count += 1
            time.sleep(1)
            torrent = qbt_client.torrents.info(status_filter='all',sort='added_on', torrent_hashes = item['nyaa_infohash'])
            if torrent:
                regCount += 1
                print(torrent[0].name)
                time.sleep(1)
                db.torrents.update_one({
                    "nyaa_infohash": item['nyaa_infohash']
                },{"$set":{"download_status":'added'}})

        for item in db.torrentsav.find(projection = {'nyaa_infohash':1,'link':2,'category2':3,'tags':4,'download_status':5},filter={"download_status" : { "$exists" : False } }):
            count += 1
            time.sleep(1)
            torrent = qbt_client.torrents.info(status_filter='all',sort='added_on', torrent_hashes = item['nyaa_infohash'])
            if torrent:
                regCount += 1
                print(torrent[0].name)
                time.sleep(1)
                db.torrentsav.update_one({
                    "nyaa_infohash": item['nyaa_infohash']
                },{"$set":{"download_status":'added'}})

        print(str(count)+'건 중' +str(regCount) + '건 신규등록 확인')

    except qbittorrentapi.LoginFailed as e:
        print(e)

#move download file to Nas
def moveToNas():
    try:
        torrents = qbt_client.torrents.info(status_filter='completed',sort='completion_on',reverse=True)
        count = 0
        for torrent in torrents:
            if torrent.save_path.find('/Users/xenopen/Downloads/') != -1 or torrent.save_path.find('/Volumes/Downloads/') != -1:
                from datetime import datetime
                count += 1
                print(str(datetime.fromtimestamp(torrent.completion_on)) +':'+ torrent.category+':'+torrent.tags+':'+torrent.save_path)
                try:
                    time.sleep(1)
                    if torrent.category == torrent.tags:
                        qbt_client.torrents.set_location(location='/Volumes/'+torrent.category+'/', torrent_hashes=torrent.hash)
                    else:            
                        qbt_client.torrents.set_location(location='/Volumes/'+torrent.category+'/'+torrent.tags+'/', torrent_hashes=torrent.hash)
                except qbittorrentapi.exceptions.Conflict409Error as e:
                    print(e)
                    

    except qbittorrentapi.LoginFailed as e:
        print(e)

#Check Completed and Moved
def checkCompleted():
    try:
        count = 0
        regCount = 0

        for item in db.torrents.find(projection = {'nyaa_infohash':1,'link':2,'category2':3,'tags':4,'download_status':5},filter={"download_status" : "added" }):
            torrents = qbt_client.torrents.info(status_filter='completed',sort='added_on', torrent_hashes = item['nyaa_infohash'])
            for torrent in torrents:
                regCount += 1
                count += 1

                time.sleep(1)
                tfiles = qbt_client.torrents_files(torrent_hash=torrent.hash)
                for tfile in tfiles:
                    time.sleep(1)
                    filename, file_extension = os.path.splitext(tfile.name)
                    if tfile.name.find('[HANIME]') != -1:
                        print(tfile.name)
                        qbt_client.torrents_renameFile(torrent_hash=item['nyaa_infohash'], old_path=tfile.name,new_path=tfile.name.replace('[HANIME]',''))


                    if tfile.name.find('['+item['tags']+']') == -1:
                        #print(list(tfile.keys()))
                        #['availability', 'is_seed', 'name', 'piece_range', 'priority', 'progress', 'size', 'id']
                        #print(list(torrent.keys()))
                        #['added_on', 'amount_left', 'auto_tmm', 'availability', 'category2', 'completed', 'completion_on', 'content_path', 'dl_limit', 'dlspeed', 'downloaded', 'downloaded_session', 'eta', 'f_l_piece_prio', 'force_start', 'hash', 'last_activity', 'magnet_uri', 'max_ratio', 'max_seeding_time', 'name', 'num_complete', 'num_incomplete', 'num_leechs', 'num_seeds', 'priority', 'progress', 'ratio', 'ratio_limit', 'save_path', 'seeding_time_limit', 'seen_complete', 'seq_dl', 'size', 'state', 'super_seeding', 'tags', 'time_active', 'total_size', 'tracker', 'trackers_count', 'up_limit', 'uploaded', 'uploaded_session', 'upspeed']
                        cat = item['category2']
                        if cat in {'AV'}:
                            qbt_client.torrents_renameFile(torrent_hash=item['nyaa_infohash'], old_path=tfile.name,new_path='['+item['tags']+']'+tfile.name)
                
                time.sleep(1)
                db.torrents.update_one({
                    "nyaa_infohash": item['nyaa_infohash']
                },{"$set":{"download_status":'completed'}})

        for item in db.torrentsav.find(projection = {'nyaa_infohash':1,'link':2,'category2':3,'tags':4,'download_status':5},filter={"download_status" : "added" }):
            torrents = qbt_client.torrents.info(status_filter='completed',sort='added_on', torrent_hashes = item['nyaa_infohash'])
            for torrent in torrents:
                regCount += 1
                count += 1

                time.sleep(1)
                tfiles = qbt_client.torrents_files(torrent_hash=torrent.hash)
                for tfile in tfiles:
                    time.sleep(1)
                    filename, file_extension = os.path.splitext(tfile.name)
                    if tfile.name.find('[HANIME]') != -1:
                        print(tfile.name)
                        qbt_client.torrents_renameFile(torrent_hash=item['nyaa_infohash'], old_path=tfile.name,new_path=tfile.name.replace('[HANIME]',''))


                    if tfile.name.find('['+item['tags']+']') == -1:
                        #print(list(tfile.keys()))
                        #['availability', 'is_seed', 'name', 'piece_range', 'priority', 'progress', 'size', 'id']
                        #print(list(torrent.keys()))
                        #['added_on', 'amount_left', 'auto_tmm', 'availability', 'category2', 'completed', 'completion_on', 'content_path', 'dl_limit', 'dlspeed', 'downloaded', 'downloaded_session', 'eta', 'f_l_piece_prio', 'force_start', 'hash', 'last_activity', 'magnet_uri', 'max_ratio', 'max_seeding_time', 'name', 'num_complete', 'num_incomplete', 'num_leechs', 'num_seeds', 'priority', 'progress', 'ratio', 'ratio_limit', 'save_path', 'seeding_time_limit', 'seen_complete', 'seq_dl', 'size', 'state', 'super_seeding', 'tags', 'time_active', 'total_size', 'tracker', 'trackers_count', 'up_limit', 'uploaded', 'uploaded_session', 'upspeed']
                        cat = item['category2']
                        if cat in {'AV'}:
                            qbt_client.torrents_renameFile(torrent_hash=item['nyaa_infohash'], old_path=tfile.name,new_path='['+item['tags']+']'+tfile.name)
            
                time.sleep(1)
                db.torrentsav.update_one({
                    "nyaa_infohash": item['nyaa_infohash']
                },{"$set":{"download_status":'completed'}})

        print(str(count)+'건 중' +str(regCount) + '건 확인')

    except qbittorrentapi.LoginFailed as e:
        print(e)

def removeCompleted():
    try:
        count = 0
        regCount = 0
        torrents = qbt_client.torrents.info(status_filter='completed')
        for torrent in torrents:
            count += 1
            print(torrent.save_path)
            
            if 'Volumes' in torrent.save_path:
                time.sleep(1)
                qbt_client.torrents.delete(delete_files=False, torrent_hashes=torrent.hash)
                db.torrentsav.update_one({"nyaa_infohash": torrent.hash},{"$set":{"download_status":'moved'}})
            

        print(str(count)+'건 중' +str(regCount) + '건 신규등록 확인')

    except qbittorrentapi.LoginFailed as e:
        print(e)


def removeOld():
    try:
        count = 0
        regCount = 0
        torrents = qbt_client.torrents.info(sort='added_on')
        for torrent in torrents:
            count += 1
            print(round(time.time()))
            print(torrent.added_on)
            print(round(time.time())-torrent.added_on)
            print(torrent.added_on+(60) < round(time.time()))
            if torrent.added_on+(60*60*24*5) < round(time.time()):
                print(torrent.name)
                time.sleep(1)
                qbt_client.torrents.delete(delete_files=True, torrent_hashes=torrent.hash)
                db.torrentsav.update_one({"nyaa_infohash": torrent.hash},{"$set":{"download_status":'deleted'}})
            

        print(str(count)+'건 중' +str(regCount) + '건 신규등록 확인')

    except qbittorrentapi.LoginFailed as e:
        print(e)


print("start")
downloadRssFeed('https://sukebei.nyaa.si/?page=rss&c=1_1&f=0&u=hikiko123','HANIME','HANIME')

#COMIC
masterdata = db.data.find().next()
for rssurl in masterdata["COMIC"]:
    db.data.update_one({"_id": masterdata["_id"]},{"$set":{"COMICDATE":datetime.now()}})
    print(rssurl)
    time.sleep(1)
    downloadRssFeed('https://sukebei.nyaa.si/?page=rss&q=COMIC+'+urllib.parse.quote(rssurl)+'&c=1_4&f=2','COMIC',rssurl)

#DOUGIN(NAMED)
NAMED=[
    '毛玉牛乳 (玉之けだま)'
]
for rssurl in NAMED:
    print(rssurl)
    downloadRssFeed('https://sukebei.nyaa.si/?page=rss&q=%22%5B'+urllib.parse.quote(rssurl)+'%5D%22&c=1_2&f=2','DOUGIN',rssurl)


#NAMED(MANGA)
for rssurl in masterdata["NAMED"]:
    print(rssurl)
    time.sleep(1)
    downloadRssFeed('https://sukebei.nyaa.si/?page=rss&q=%22%5B'+urllib.parse.quote(rssurl)+'%5D%22&c=1_4&f=2','NAMED',rssurl)

#AV
for rssurl in masterdata["AV"]:
    print(rssurl)
    time.sleep(1)
    downloadAVRssFeed('https://sukebei.nyaa.si/?page=rss&q=%22Uncensored%22+%22'+urllib.parse.quote(rssurl)+'%22&c=2_2&f=2','AV',rssurl)
