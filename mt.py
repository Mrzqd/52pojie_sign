#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: mt.py(MT签到)
Author: Mrzqd
Date: 2023/8/27 08:00
cron: 30 7 * * *
new Env('MT论坛签到');
"""
from time import sleep
import notify
import requests
import re
import os
import sys
import urllib.parse
import random

sleep_time = [100, 200]  # 随机等待时间默认在100-200秒之间
# 多cookie使用&分割
cookies = ""

if cookies == "":
    if os.environ.get("MT_COOKIE"):
        cookies = os.environ.get("MT_COOKIE")
    else:
        print("请在环境变量填写MT_COOKIE的值")
        sys.exit()
n = 1
list_cookie = cookies.split("&")
for cookie in list_cookie:
    sleep_t = random.randint(sleep_time[0], sleep_time[1])
    print(f"第{n}个账号随机等待{sleep_t}秒")
    sleep(sleep_t)
    if cookie == "":
        break
    cookie = urllib.parse.unquote(cookie)
    cookie_list = cookie.split(";")
    cookie = ''
    for i in cookie_list:
        key = i.split("=")[0]
        if "cQWy_2132_saltkey" in key:
            cookie += "cQWy_2132_saltkey=" + urllib.parse.quote(i.split("=")[1]) + "; "
        if "cQWy_2132_auth" in key:
            cookie += "cQWy_2132_auth=" + urllib.parse.quote(i.split("=")[1]) + ";"
    if not ('cQWy_2132_saltkey' in cookie or 'cQWy_2132_auth' in cookie):
        print(f"第{n}cookie中未包含TWcq_2132_saltkey或TWcq_2132_auth字段，请检查cookie")
        sys.exit()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Cookie': cookie
    }
    getFormhashUrl = 'https://bbs.binmt.cc/k_misign-sign.html'
    try:
        r = requests.get(getFormhashUrl, headers=headers)
        if r.status_code != 200:
            print("获取formhash失败了~\n接口返回状态码:", str(r.status_code) + "\n接口返回内容:", r.text)
            notify.send("MT论坛签到", "获取formhash失败了~\n接口返回状态码:" + str(r.status_code) + "\n接口返回内容:" + r.text)
            continue
    except Exception as e:
        print("获取formhash失败了~\n错误原因:" + str(e))
        notify.send("MT论坛签到", "获取formhash失败了~\n错误原因:" + str(e))
        continue
    # print(r.text)
    pattern = r'<input\s+type="hidden"\s+name="formhash"\s+value="([^"]+)" />'
    match = re.search(pattern, r.text)
    if match:
        formhash = match.group(1)
        # print("formhash:", formhash)
    else:
        print("未正则到formhash，签到失败！")
        notify.send("MT论坛签到", "未正则到formhash，签到失败！")
        continue
    url = f'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&formhash={formhash}&format=empty&inajax=1&ajaxtarget='
    pattern = r"<!\[CDATA\[(.*?)\]\]>"
    try:
        r = requests.get(url, headers=headers)
        match = re.search(pattern, r.text)
        # print(r.text)
        # print(r.status_code)
        if r.status_code != 200:
            print("签到失败了~\n接口返回状态码:", str(r.status_code) + "\n接口返回内容:", r.text)
            notify.send("MT论坛签到", "MT论坛签到失败了~\n接口返回状态码:" + str(r.status_code) + "\n接口返回内容:" + r.text)
            continue
        if match:
            cdata_content = match.group(1)
            # print("CDATA内容:", cdata_content)
            if not cdata_content:
                print("签到成功~")
                notify.send("MT论坛签到", "MT论坛签到成功~")
            elif cdata_content == "今日已签":
                print("今天已经签到过了~")
                notify.send("MT论坛签到", "今天已经签到过了~")
            else:
                print("未知的签到内容，无法确定是否签到成功！\n接口返回内容:" + cdata_content)
                notify.send("MT论坛签到", "未知的签到内容，无法确定是否签到成功！\n接口返回内容:" + cdata_content)
        else:
            print("未正则到有效内容，无法确定是否签到成功！\n接口返回是：" + r.text)
            notify.send("MT论坛签到", "未正则到有效内容，无法确定是否签到成功！\n接口返回是：" + r.text)
    except Exception as e:
        print("签到失败了~\n错误原因:" + str(e))
        notify.send("MT论坛签到", "MT论坛签到失败了~\n错误原因:" + str(e))
