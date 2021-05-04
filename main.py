from flask import Flask, request, render_template, redirect
from UserModel import videoInfo
from setting import session
from sqlalchemy import *
from sqlalchemy.orm import *
import json
# from bs4 import BeautifulSoup
import requests
import os
from dotenv import load_dotenv
from os.path import join, dirname

video = []


# インスタンス化し、videoリストに入れる(nico)
def nico_res(word):
    # 動画情報取得
    url = "https://api.search.nicovideo.jp/api/v2/snapshot/video/contents/search"
    # クエリパラメータの設定
    params = {'q': word,
              'targets': 'title,tags',
              'fields': 'title,description,contentId,thumbnailUrl,viewCounter',
              '_sort': '-viewCounter',
              '_context': 'apiguide',
              '_limit': '10'
              }

    req = requests.get(url, params=params)
    res = json.loads(req.text)

    # 各種パラメータを取得する関数
    def getId(i):
        return res["data"][i]["contentId"]

    def getTitle(i):
        return res["data"][i]["title"]

    def getChannel(i):
        chaUrl = "https://ext.nicovideo.jp/api/getthumbinfo/" + res["data"][i]["contentId"]
        chareq = requests.get(chaUrl)
        channel = chareq.text[chareq.text.find('<user_nickname>') + 15:chareq.text.find('</user_nickname>')]
        return channel

    def getDescription(i):
        description = res["data"][i]["description"].replace("<br />", "")
        return description

    def getViewCounter(i):
        return res["data"][i]["viewCounter"]

    def getVideoURL(i):
        return "https://nico.ms/" + res["data"][i]["contentId"]

    def getImageURL(i):
        return res["data"][i]["thumbnailUrl"]

    for i in range(len(res["data"])):
        resvideo = videoInfo(getId(i), getTitle(i), getChannel(i), getDescription(i), getViewCounter(i), getVideoURL(i),
                             getImageURL(i), "ニコニコ動画")
        video.append(resvideo)


# インスタンス化し、videoリストに入れる(Youtube)
def you_res(word):
    # YoutubeAPIキーはセキュリティ対策のため.envファイル(ローカルに保存)からロード
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)

    # 動画情報取得
    url = "https://www.googleapis.com/youtube/v3/search"
    # クエリパラメータの設定
    params = {'type': 'video',
              'part': 'snippet',
              'q': word,
              'key': os.environ.get("Youtube_API_KEY"),
              'maxResults': '1',
              'regionCode': 'jp',
              'fields': 'items(id(videoId),snippet(title,description,channelTitle,thumbnails(high(url))))'
              }

    req = requests.get(url, params=params)
    res = json.loads(req.text)

    # 各種パラメータを取得する関数
    def getId(i):
        return res["items"][i]["id"]["videoId"]

    def getTitle(i):
        return res["items"][i]["snippet"]["title"]

    def getChannel(i):
        return res["items"][i]["snippet"]["channelTitle"]

    def getDescription(i):
        return res["items"][i]["snippet"]["description"]

    def getViewCounter(i):
        counturl = "https://www.googleapis.com/youtube/v3/videos"
        params2 = {'part': 'statistics',
                   'id': getId(i),
                   'key': os.environ.get("Youtube_API_KEY"),
                   'fields': 'items(statistics(viewCount))'
                   }
        req = requests.get(counturl, params=params2)
        res = json.loads(req.text)
        return res["items"][0]["statistics"]["viewCount"]

    def getVideoURL(i):
        return "https://www.youtube.com/watch?v=" + res["items"][i]["id"]["videoId"]

    def getImageURL(i):
        return res["items"][i]["snippet"]["thumbnails"]["high"]["url"]

    for i in range(len(res["items"])):
        # パラメータの設定
        resvideo = videoInfo(getId(i), getTitle(i), getChannel(i), getDescription(i), getViewCounter(i), getVideoURL(i),
                             getImageURL(i), "Youtube")
        video.append(resvideo)


# appという名前でFlaskのインスタンスを作成
app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


# 登録処理
@app.route('/', methods=["POST"])
def register_record():
    word = request.form.get("word")
    session.query(videoInfo).delete()

    # ニコニコ動画
    nico_res(word)
    you_res(word)
    for i in range(len(video)):
        new_video = videoInfo(id=video[i].id, title=video[i].title, channel=video[i].channel,
                              description=video[i].description, viewCount=video[i].viewCount,
                              videoURL=video[i].videoURL, imageURL=video[i].imageURL, kind=video[i].kind)
        session.add(new_video)

    session.commit()
    return redirect("/")


# 取得処理
@app.route('/', methods=["GET"])
def fetch_record():
    db_videoInfo = session.query(videoInfo).all()

    # return render_template("index.html", name=name, message=message)


if __name__ == '__main__':
    app.run()
    
