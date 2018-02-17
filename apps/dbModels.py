#!/usr/bin/env python
# -*- coding:utf-8 -*-

from operator import attrgetter
from apps.utils import ke_encrypt,ke_decrypt
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

#--------------db models----------------
#对应到每一个”书“，注意，同一个用户的”自定义RSS“会归到同一本书内
class Book(db.Model):
    title = db.Column(db.String(255), required=True)
    description = db.Column(db.TEXT)
    users = db.Column(db.Text)
    builtin = db.Column(db.Boolean)
    needs_subscription = db.Column(db.Boolean) #是否需要登陆网页
    separate = db.Column(db.Boolean) #是否单独推送
    
    #====自定义书籍
    language = db.Column(db.String(255))
    mastheadfile = db.Column(db.String(255)) # GIF 600*60
    coverfile = db.Column(db.String(255))
    keep_image = db.Column(db.Boolean)
    oldest_article = db.Column(db.Integer)
    
    #这三个属性只有自定义RSS才有意义
    @property
    def feeds(self):
        try:
            return Feed.all().filter('book = ', self.key()).order('time')
        except NeedIndexError: #很多人不会部署，经常出现没有建立索引的情况，干脆碰到这种情况直接消耗CPU时间自己排序得了
            return sorted(Feed.all().filter("book = ", self.key()), key=attrgetter('time'))
            
    @property
    def feedscount(self):
        fc = self.feeds.count()
        return fc
    @property
    def owner(self):
        return KeUser.all().filter('ownfeeds = ', self.key())
    
class KeUser(db.Model): # kindleEar User
    name = db.Column(db.String(255), required=True)
    passwd = db.Column(db.String(255), required=True)
    secret_key = db.Column(db.String(255))
    kindle_email = db.Column(db.String(255))
    enable_send = db.Column(db.Boolean)
    send_days = db.Column(db.TEXT)
    send_time = db.Column(db.Integer)
    timezone = db.Column(db.Integer)
    book_type = db.Column(db.String(255)) #mobi,epub
    device = db.Column(db.String(255))
    expires = db.Column(db.DateTime) #超过了此日期后账号自动停止推送
    ownfeeds = db.RelationshipProperty(Book) # 每个用户都有自己的自定义RSS???
    use_title_in_feed = db.Column(db.Boolean) # 文章标题优先选择订阅源中的还是网页中的
    titlefmt = db.Column(db.String(255)) #在元数据标题中添加日期的格式
    merge_books = db.Column(db.Boolean) #是否合并书籍成一本
    
    share_fuckgfw = db.Column(db.Boolean) #归档和分享时是否需要翻墙
    evernote = db.Column(db.Boolean) #是否分享至evernote
    evernote_mail = db.Column(db.String(255)) #evernote邮件地址
    wiz = db.Column(db.Boolean) #为知笔记
    wiz_mail = db.Column(db.String(255))
    pocket = db.Column(db.Boolean, default=False) #send to add@getpocket.com
    pocket_access_token = db.Column(db.String(255), default='')
    pocket_acc_token_hash = db.Column(db.String(255), default='')
    instapaper = db.Column(db.Boolean)
    instapaper_username = db.Column(db.String(255))
    instapaper_password = db.Column(db.String(255))
    xweibo = db.Column(db.Boolean)
    tweibo = db.Column(db.Boolean)
    facebook = db.Column(db.Boolean) #分享链接到facebook
    twitter = db.Column(db.Boolean)
    tumblr = db.Column(db.Boolean)
    browser = db.Column(db.Boolean)
    qrcode = db.Column(db.Boolean) #是否在文章末尾添加文章网址的QRCODE
    cover = db.Column(db.BLOB) #保存各用户的自定义封面图片二进制内容
    
    book_mode = db.Column(db.String(255)) #added 2017-08-31 书籍模式，'periodical'|'comic'，漫画模式可以直接全屏
    expiration_days = db.Column(db.Integer) #added 2018-01-07 账号超期设置值，0为永久有效
    
    @property
    def whitelist(self):
        return WhiteList.all().filter('user = ', self.key())
    
    @property
    def urlfilter(self):
        return UrlFilter.all().filter('user = ', self.key())
    
    #获取此账号对应的书籍的网站登陆信息
    def subscription_info(self, title):
        return SubscriptionInfo.all().filter('user = ', self.key()).filter('title = ', title).get()

#自定义RSS订阅源
class Feed(db.Model):
    book = db.foreign(Book)
    title = db.Column(db.String(255))
    url = db.Column(db.String(255))
    isfulltext = db.Column(db.Boolean)
    datetime = db.Column(db.DateTime) #源被加入的时间，用于排序

#书籍的推送历史记录
class DeliverLog(db.Model):
    username = db.Column(db.String(255))
    to = db.Column(db.String(255))
    size = db.Column(db.Integer)
    time = db.Column(db.String(255))
    datetime = db.Column(db.DateTime)
    book = db.Column(db.String(255))
    status = db.Column(db.String(255))

#added 2017-09-01 记录已经推送的期数/章节等信息，可用来处理连载的漫画/小说等
class LastDelivered(db.Model):
    username = db.Column(db.String(255))
    bookname = db.Column(db.String(255))
    num = db.Column(db.Integer, default=0) #num和record可以任选其一用来记录，或使用两个配合都可以
    record = db.Column(db.String(255), default='') #record同时也用做在web上显示
    datetime = db.Column(db.DateTime)
    
class WhiteList(db.Model):
    mail = db.Column(db.String(255))
    user = db.foreign(KeUser)

class UrlFilter(db.Model):
    url = db.Column(db.String(255))
    user = db.foreign(KeUser)
    
class SubscriptionInfo(db.Model):
    title = db.Column(db.String(255))
    account = db.Column(db.String(255))
    encrypted_pwd = db.Column(db.String(255))
    user = db.foreign(KeUser)
    
    @property
    def password(self):
        return ke_decrypt(self.encrypted_pwd, self.user.secret_key)
        
    @password.setter
    def password(self, pwd):
        self.encrypted_pwd = ke_encrypt(pwd, self.user.secret_key)
        