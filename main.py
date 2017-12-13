#!/usr/bin/python
# coding=utf-8
#environment: Python 3.6
#Crawler to download doujinshi from e sit

from urllib import request, parse
import http
import re
import io
import os
import sys
from queue import Queue
from threading import Thread
import time
import urllib
from http import cookiejar

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8') #change std output default to utf-8 (windows)


class EhentaiCrawler:
    regular_expression_books_item = '<div class="it5"><a href="(https://e-hentai\.org/g/.+?)" .+?>(.+?)<\/a><\/div>'
    regular_expression_book_size = '<td class="gdt1">File Size:</td><td class="gdt2">(.+?)</td>'
    regular_expression_book_pages_number = '<td class="gdt1">Length:</td><td class="gdt2">(.+?) pages</td>'
    regular_expression_book_image_webpage_url = r'<a href="(https://e-hentai\.org/s/.+?)"><img alt=.+?></a>'
    regular_expression_book_image = '<img id="img" src="(.+?)" style=".+?" onerror=".+?">'
    def __init__(self):
        self.pattern_item = re.compile(self.regular_expression_books_item)#Book item from book list
        self.pattern_book_size = re.compile(self.regular_expression_book_size)
        self.pattern_book_pages_number = re.compile(self.regular_expression_book_pages_number)
        self.pattern_book_image_webpage_url = re.compile(self.regular_expression_book_image_webpage_url)
        self.pattern_book_image = re.compile(self.regular_expression_book_image)
        return

    #Multiple threads to download images
    def download_image(self, book_name, queue):
        while True:
            (num, page_url) = queue.get()
            print("The url of the page: %s" % page_url)
            headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
                }

            #Seems donn't need cookie to get images...
            finished = False
            while not finished:
                try:
                    req = request.Request(page_url, headers=headers, method='GET')
                    page = request.urlopen(req).read() #add cookie
                    #page = opener.open(req).read()
                    page = page.decode('utf-8')
                    image_url_list = re.findall(self.pattern_book_image, page)
                    image_url = image_url_list[0]
                    finished = True
                except:
                    pass
            file_suffix = ".jpg"
            file_name = "{}{}{}{}".format(book_name, os.sep, num, file_suffix)
            finished = False
            while not finished:
                try:
                    urllib.request.urlretrieve(image_url, file_name)
                    finished = True
                except:
                    pass
            queue.task_done()

    #Get each images url with books url
    def download_book(self, book_url, book_name):
        headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
            }
        page_info={
                'p':0,
                'nw':'session',
                }
        print("book url is %s" % (book_url))
        
        #Cookie to store 'nw' parameter to access offensive contents
        cookie_filename = 'cookie.txt'#Currently store nothing in this file
        cookie = cookiejar.CookieJar()
        handler = request.HTTPCookieProcessor(cookie)
        opener = request.build_opener(handler)
        
        finished = False
        while not finished:
            try:
                data = parse.urlencode(page_info)
                print("URL: %s" % (book_url + '?' + data))
                req = request.Request(book_url + '?' + data, headers=headers, method='GET')
                #book = request.urlopen(req).read() #add cookie to access
                book = opener.open(req).read()
                #cookie.save(ignore_discard=True, ignore_expires=True)#(Keep when discard, cover when exist)
                book = book.decode('utf-8')
                file_size = re.findall(self.pattern_book_size, book)
                book_pages_number = re.findall(self.pattern_book_pages_number, book)
                finished = True
            except:
                pass
        print("Download start... (Book Size: %s pages, %s)" % (book_pages_number[0], file_size[0]))
        total_book_url_number = int(book_pages_number[0]) / 40
        if(int(book_pages_number[0]) % 40 != 0):
            total_book_url_number += 1
        book_image_webpage_url = re.findall(self.pattern_book_image_webpage_url, book)
        for i in range(1, int(total_book_url_number)):
            page_info['p'] = i,
            data = parse.urlencode(page_info)
            finished = False
            while not finished:
                try:
                    req = request.Request(book_url + '?' + data, headers=headers, method='GET')
                    #book = request.urlopen(req).read()
                    book = opener.open(req).read()
                    #cookie.save(ignore_discard=True, ignore_expires=True)#(Keep when discard, cover when exist)
                    book = book.decode('utf-8')
                    book_image_webpage_url += re.findall(self.pattern_book_image_webpage_url)
                    finished = True
                except:
                    pass
        print(book_image_webpage_url[0])
        if(os.path.exists(book_name) == False):
            os.mkdir(book_name)
        task_queue = Queue()
        for i in range(0, int(book_pages_number[0])):
            task_queue.put((i, book_image_webpage_url[i]))
        
        for tid in range(4):#threads number
            worker = Thread(target=EhentaiCrawler.download_image, args=(self, book_name, task_queue))
            worker.setDaemon(True)
            worker.start()
            
        task_queue.join()
        return;

    #Seach page submit then show result list
    def search(self, keyword='hiten', page_number=0):
        while(True):
            site_url = 'https://e-hentai.org/'
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
            }
            result_type={
                'page':page_number,
                'f_doujinshi':1,
                'f_manga':0,
                'f_artistcg':0,
                'f_gamecg':0,
                'f_western':0,
                'f_non-h':0,
                'f_imageset':0,
                'f_cosplay':0,
                'f_asianporn':0,
                'f_misc':0,
                'f_search':keyword,
                'f_apply':'Apply Filter',
            }
            data = parse.urlencode(result_type)
            req = request.Request(site_url + '?' + data, headers=headers, method='GET')
            page = request.urlopen(req).read()
            page = page.decode('utf-8')
            
            search_result = re.findall(self.pattern_item, page)
            
            print("The search result is shown below")
            if search_result:
                bid = 0
                print("ID\tBook Name")
                for item in search_result:
                    print("%d\t%s" % (bid, item[1]))
                    bid = bid + 1
                print("Page: %d" % (page_number))
            else:
                print("No results matched!")
            
            
            print("Command List:\nN: next page\nF: front page\nD: Goto download")
            print("R: Back to search\nE: Exit Program\n");
            
            command_input = input("Please input command:")
            while(command_input != 'N' and command_input != 'F' and command_input != 'D' and command_input != 'R' and command_input != 'E'):
                print("UNKNOWN command!\nPlease input again:")
                command_input = input("Please input command:")
            
            if(command_input == 'N'):
                page_number = page_number + 1
            
            if(command_input == 'F'):
                page_number = max(0, page_number - 1)
              
            if(command_input == 'D'):
                book_id = input("Input the book ID you need:")
                self.download_book(search_result[int(book_id)][0], search_result[int(book_id)][1]);
            
            if(command_input == 'R'):
                page_number = 0
                keyword = input("Please input search keyword:")
                while(len(keyword) == 0):
                    print("Empty input!")
                    keyword = input("Please input search keyword:")
            
            if(command_input == 'E'):
                return

    def start(self):
        search_keyword = '';
        search_keyword = input("Please input search keyword:")
        while(len(search_keyword) == 0):
            print("Empty input!")
            search_keyword = input("Please input search keyword:")
        print("Keyword: '" + search_keyword + "'")
        self.search(search_keyword)
        return;
        

crawler = EhentaiCrawler()

print("Welcome to EHCrawler!")
crawler.start()
