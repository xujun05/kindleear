#!/usr/bin/env python
# -*- coding:utf-8 -*-
#KindleEar <https://github.com/cdhigh/KindleEar>
#Author: cdhigh <https://github.com/cdhigh>
#自动加载books目录和子目录下的所有书籍文件，所有的自定义基类(不是最终的书籍实现)请以base.py结尾，比如xxxxbase.py
#各子目录下必须要有一个__init__.py文件，否则不会导入对应子目录下的书籍
import os
import logging

# 通过下面的方式进行简单配置输出方式与日志级别
logging.basicConfig(filename='logger.log', level=logging.INFO)
logger = logging.getLogger("simpleExample")

_booksclasses = []


def RegisterBook(book):
    if book.title:
        _booksclasses.append(book)


def BookClasses():
    return _booksclasses


def BookClass(title):
    for book in _booksclasses:
        if book.title == title:
            return book
    return None


bookRootDir = os.path.dirname(__file__)
listBkDirs = os.walk(bookRootDir)
for root, dirs, files in listBkDirs:
    for f in files:
        bkFile = os.path.join(root, f)
        baseName = os.path.basename(bkFile)
        initFileName = os.path.join(os.path.dirname(bkFile), '__init__.py') #保证对应子目录下有__init__.py
        if bkFile.endswith('.py') and not baseName.startswith('__') and not bkFile.endswith("base.py") and os.path.isfile(initFileName):
            fullName = bkFile.replace(bookRootDir, '')
            fullName = fullName.lstrip('/').lstrip('\\').replace('\\', '/')
            bookModuleName = os.path.splitext(fullName)[0].replace('/', '.')
            try:
                mBook = __import__('books.' + bookModuleName, fromlist='*')
                if hasattr(mBook, 'getBook'):
                    bk = mBook.getBook()
                    RegisterBook(bk)
            except Exception as e:
                logger.warn("Book '%s' import failed : %s" % (bookModuleName, e))
