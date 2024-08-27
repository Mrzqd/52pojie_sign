#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: main.py(吾爱破解签到)
Author: Mrzqd
Date: 2024/8/22 18:30
cron: 30 7 * * *
new Env('吾爱破解签到');
"""
import os
import re
import sys
import urllib.parse
import random
from time import sleep

import requests
from bs4 import BeautifulSoup


import notify

# class notify:
#     @staticmethod
#     def send(title, content):
#         print(f"{title}: {content}")


sleep_time = [100, 200]  # 随机等待时间默认在100-200秒之间
# 多cookie使用&分割
token = os.environ.get("PJ52_TOKEN")
if not token:
    print("请在环境变量填入PJ52_TOKEN的值")
    sys.exit()

cookies = ''
if cookies == "":
    if os.environ.get("PJ52_COOKIE"):
        cookies = os.environ.get("PJ52_COOKIE")
    else:
        print("请在环境变量填写PJ52_COOKIE的值")
        sys.exit()
n = 1
for cookie in cookies.split("&"):
    sleep(random.randint(sleep_time[0], sleep_time[1]))
    url1 = 'https://www.52pojie.cn/'
    url2 = 'https://www.52pojie.cn/home.php?mod=task&do=apply&id=2&referer=%2F'
    # url3 = 'https://www.52pojie.cn/home.php?mod=task&do=draw&id=2'
    url4 = 'https://www.52pojie.cn/waf_zw_verify'
    cookie = urllib.parse.unquote(cookie)
    cookie_list = cookie.split(";")
    cookie = ''
    cookie = {'htVC_2132_auth': '',
              'htVC_2132_saltkey': ''}
    for i in cookie_list:
        key = i.split("=")[0]
        if "htVC_2132_saltkey" in key:
            cookie['htVC_2132_saltkey'] = urllib.parse.quote(i.split("=")[1])
        if "htVC_2132_auth" in key:
            cookie['htVC_2132_auth'] = urllib.parse.quote(i.split("=")[1])
    if cookie['htVC_2132_saltkey'] == '' or cookie['htVC_2132_auth'] == '':
        print(f"第{n}cookie中未包含htVC_2132_saltkey或htVC_2132_auth字段，请检查cookie")
        sys.exit()
    headers = {
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "sec-ch-ua": "\"Chromium\";v=\"104\", \" Not A;Brand\";v=\"99\", \"Google Chrome\";v=\"104\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "Referer": "https://www.52pojie.cn/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    session = requests.session()
    r = session.get(url1, headers=headers, cookies=cookie)
    # print(r.text)
    soup = BeautifulSoup(r.text,features="html.parser")
    login = soup.find('button', class_="pn vm")
    # print(login)
    if login != None:
        print(f"第{n}个账号Cookie 失效")
        message = f"第{n}个账号Cookie 失效"
        n += 1
        continue
    sign_check = list(filter(lambda node: node.get("src").endswith("qds.png") or node.get("src").endswith("wbs.png"),
                             soup.findAll('img', class_="qq_bind")))
    if sign_check is None or len(sign_check) == 0:
        print(f"第{n}个账号Cookie 失效")
        message = f"第{n}个账号Cookie 失效"
        n += 1
        continue
    sign_check = sign_check[0]
    if not sign_check.get("src").endswith("qds.png"):
        print(f"第{n}个账号今日已签到")
        message = f"第{n}个账号今日已签到"
        n += 1
        continue
    r = session.get(url2, headers=headers, cookies=cookie)
    pattern = r".*='([0-9]{4,})'.*='([0-9]{4,})'.*"
    result = re.match(pattern, r.text, re.S)
    if not result:
        print(f"第{n}个账号今日签到失败")
        message = f"第{n}个账号今日签到失败"
        n += 1
        continue
    lz = result.group(1)
    lj = result.group(2)
    pattern = r".*='([a-zA-Z0-9/+]{40,})'.*"
    result = re.match(pattern, r.text, re.S)
    if not result:
        print(f"第{n}个账号今日签到失败")
        message = f"第{n}个账号今日签到失败"
        n += 1
        continue
    le = result.group(1)
    result = requests.post("https://52pojie-sign-sever.zzboy.tk/api/52pojie",json={"lz": lz, "lj": lj, "le": le,"token":token})
    if result.status_code != 200:
        print(result.json()['msg'])
        print("请前往“https://zhustatus.azurewebsites.net/”查看“52POJIE-SIGN”的运行状态")
        sys.exit()
    # print(result.text)
    r = session.post(url4, headers=headers, cookies=cookie, data=result.text, proxies=None)
    # print(r.text)
    r = session.get(url2, headers=headers, cookies=cookie)
    # print(r.status_code, r.text)
    r_data = BeautifulSoup(r.text, "html.parser")
    # print(r_data)
    jx_data = r_data.find("div", id="messagetext").find("p").text
    if "您需要先登录才能继续本操作" in jx_data:
        print(f"第{n}个账号Cookie 失效")
        message = f"第{n}个账号Cookie 失效"
    elif "恭喜" in jx_data:
        print(f"第{n}个账号签到成功")
        message = f"第{n}个账号签到成功"
    elif "不是进行中的任务" in jx_data:
        print(f"第{n}个账号今日已签到")
        message = f"第{n}个账号今日已签到"
    else:
        print(f"第{n}个账号签到失败")
        message = f"第{n}个账号签到失败"
    n += 1
    notify.send("吾爱签到", message)
