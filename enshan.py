#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: enshan.py(恩山签到)
Author: Mrzqd
Date: 2023/8/17 08:00
cron: 30 7 * * *
new Env('恩山签到');
"""

import datetime
import os
import sys
import urllib.parse
import random
from time import sleep

import notify
import requests
from bs4 import BeautifulSoup

sleep_time = [100, 200]  # 随机等待时间默认在100-200秒之间
# 多cookie使用&分割
# cookies = ""
cookies = ""

if cookies == "":
    if os.environ.get("ENSHAN_COOKIE"):
        cookies = os.environ.get("ENSHAN_COOKIE")
    else:
        print("请在环境变量填写ENSHAN_COOKIE的值")
        sys.exit()
n = 1
list_cookie = cookies.split("&")
for cookie in list_cookie:
    sleep_t = random.randint(sleep_time[0], sleep_time[1])
    print(f"第{n}个随机等待{sleep_t}秒")
    sleep(sleep_t)
    if cookie == "":
        break
    cookie = urllib.parse.unquote(cookie)
    cookie_list = cookie.split(";")
    cookie = ''
    for i in cookie_list:
        key = i.split("=")[0]
        if "TWcq_2132_saltkey" in key:
            cookie += "TWcq_2132_saltkey=" + urllib.parse.quote(i.split("=")[1]) + "; "
        if "TWcq_2132_auth" in key:
            cookie += "TWcq_2132_auth=" + urllib.parse.quote(i.split("=")[1]) + ";"
    if not ('TWcq_2132_saltkey' in cookie or 'TWcq_2132_auth' in cookie):
        print(f"第{n}cookie中未包含TWcq_2132_saltkey或TWcq_2132_auth字段，请检查cookie")
        sys.exit()
    url = "https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit&op=log&suboperation=creditrulelog"
    print(url)
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Cookie": cookie,
        "Host": "www.right.com.cn",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.200",
        "sec-ch-ua": "\"Not/A)Brand\";v=\"99\", \"Microsoft Edge\";v=\"115\", \"Chromium\";v=\"115\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    r = requests.get(url, headers=headers)
    print(r.status_code)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        trs = soup.find("table", summary="积分获得历史").find_all("tr")
        for tr in trs:
            tds = tr.find_all("td")
            if len(tds) == 0:
                continue
            if tds[0].text == "每天登录" and tds[5].text[:10] == datetime.datetime.now().strftime("%Y-%m-%d"):
                message = f"第{n}个账号签到成功"
                print(message)
                n += 1
                notify.send("恩山签到", message)
                break
        else:
            message = f"第{n}个账号签到失败"
            print(message)
            n += 1
            notify.send("恩山签到", message)
    else:
        message = f"第{n}个账号可能cookie过期"
        print(message)
        n += 1
        notify.send("恩山签到", message)
