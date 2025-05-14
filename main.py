#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: main.py(吾爱破解签到)
Author: Mrzqd
Date: 2024/8/22 18:30 (Original)
Last Modified: 2025/05/14 (Optimization Date)
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

# 尝试导入notify模块，如果失败，则使用内置的简单打印版本
try:
    import notify
except ImportError:
    print("未找到 notify 模块，将使用print输出通知。")
    class notify:
        @staticmethod
        def send(title, content):
            print(f"通知 - {title}: {content}")

# --- 配置区域 ---
# 随机等待时间范围（秒）
SLEEP_TIME_RANGE = [100, 200]

# 吾爱破解相关URL
URL_HOME = 'https://www.52pojie.cn/'
URL_TASK_APPLY = 'https://www.52pojie.cn/home.php?mod=task&do=apply&id=2&referer=%2F'
# URL_TASK_DRAW = 'https://www.52pojie.cn/home.php?mod=task&do=draw&id=2' # 似乎未使用
URL_WAF_VERIFY = 'https://www.52pojie.cn/waf_zw_verify'
EXTERNAL_SIGN_API = "https://52pojie-sign-sever.zzboy.tk/api/52pojie" # 注意：依赖外部API

# 请求头
HEADERS = {
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", # 更新了UA
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "sec-ch-ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "Referer": "https://www.52pojie.cn/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
# --- 配置区域结束 ---

def parse_cookie_string(cookie_str):
    """解析单个cookie字符串为requests库所需的字典格式，并提取特定键值"""
    cookie_str_unquoted = urllib.parse.unquote(cookie_str)
    cookie_dict = {}
    required_values = {'htVC_2132_auth': None, 'htVC_2132_saltkey': None}

    for item in cookie_str_unquoted.split(';'):
        item = item.strip()
        if not item:
            continue
        if '=' in item:
            key, value = item.split('=', 1)
            if key in required_values:
                required_values[key] = urllib.parse.quote(value) # 重新URL编码以备用

    if not all(required_values.values()):
        missing_keys = [k for k, v in required_values.items() if v is None]
        return None, f"Cookie中未包含以下关键字段: {', '.join(missing_keys)}"

    # requests库可以直接使用分号分隔的cookie字符串，但为了明确，这里构造字典
    # 实际上requests的cookies参数可以直接接受分号连接的字符串，
    # 但为了显式控制和检查，这里我们解析并只使用我们关心的部分构造字典。
    # 如果要使用requests自动处理，可以直接传递原始的cookie_str_unquoted。
    # 但原脚本逻辑是提取特定键值，我们遵循此逻辑。
    # 然而，requests 的 `cookies` 参数接受一个字典，键是 cookie 名称，值是 cookie 值。
    # 所以，这里应该返回一个可以直接用于 `requests.get/post` 的 cookies 参数的字典。
    # 这里的 `required_values` 就是我们要的字典。
    return required_values, None


def process_account(account_index, raw_cookie_str, token):
    """处理单个吾爱破解账户的签到流程"""
    message = ""
    print(f"--- 开始处理第 {account_index} 个账号 ---")

    cookie_dict, error_msg = parse_cookie_string(raw_cookie_str)
    if error_msg:
        print(f"第 {account_index} 个账号 Cookie 解析失败: {error_msg}")
        return f"第 {account_index} 个账号 Cookie 解析失败: {error_msg}"

    session = requests.session()
    session.headers.update(HEADERS) # 更新会话的默认请求头
    # 对于requests的cookies参数，它应该是一个字典。
    # 我们传递解析后的cookie_dict

    try:
        # 1. 访问首页检查登录状态和签到状态
        print(f"账号 {account_index}: 访问首页...")
        r_home = session.get(URL_HOME, cookies=cookie_dict)
        r_home.raise_for_status() # 如果请求失败则抛出异常
        soup_home = BeautifulSoup(r_home.text, "html.parser")

        # 检查是否需要登录 (如果找到登录按钮，则表示Cookie失效)
        login_button = soup_home.find('button', class_="pn vm")
        if login_button is not None and "登录" in login_button.text:
            message = f"第 {account_index} 个账号 Cookie 失效或已过期。"
            print(message)
            return message

        # 检查今日是否已签到
        # 吾爱破解的签到状态图片：
        # 未签到: .../static/image/common/qds.png
        # 已签到: .../static/image/common/wbs.png 或 hby_s.png (红包已领)
        sign_img_elements = soup_home.select('img.qq_bind[src*="qds.png"], img.qq_bind[src*="wbs.png"], img.qq_bind[src*="hby_s.png"]')

        if not sign_img_elements:
            # 如果没有找到签到相关的图片，可能是页面结构改变或者cookie问题
            # 进一步检查用户名是否存在来判断是否真的登录
            user_info_element = soup_home.select_one('#umenu > p:nth-child(1) > strong > a')
            if not user_info_element:
                message = f"第 {account_index} 个账号 Cookie 失效 (无法找到用户信息)。"
                print(message)
                return message
            else:
                # 这种情况比较少见，可能是不再显示签到图标或有其他提示
                print(f"第 {account_index} 个账号：未找到明确的签到状态图片，但用户已登录。尝试继续签到流程。")
                # 此时不直接返回，尝试继续签到流程，后续步骤会再次确认

        elif any("qds.png" not in img['src'] for img in sign_img_elements):
             # 如果存在任何一个非qds.png的图片 (如wbs.png, hby_s.png), 则认为已签到
            message = f"第 {account_index} 个账号今日已签到 (通过首页图片判断)。"
            print(message)
            return message
        
        print(f"账号 {account_index}: 检测到未签到 (qds.png)，尝试签到...")

        # 2. 访问任务页面获取签到参数
        print(f"账号 {account_index}: 访问任务页面获取参数...")
        r_task_page = session.get(URL_TASK_APPLY, cookies=cookie_dict)
        r_task_page.raise_for_status()
        task_page_content = r_task_page.text

        # 使用re.search可能更安全，因为它匹配字符串中任何位置的模式
        # re.match只从字符串开头匹配
        match_lz_lj = re.search(r" renversement\('(\d{4,})'\).* renversement\('(\d{4,})'\)", task_page_content, re.S)
        # 原正则: pattern = r".*='([0-9]{4,})'.*='([0-9]{4,})'.*"
        # 在实际页面中，参数可能是被包裹在 renversement JS函数中的，例如：
        # <script> renversement('XXXX'); renversement('YYYY'); </script>
        # 或者在 input hidden 的 value 中。需要根据实际页面结构调整。
        # 假设这里的参数是直接在 JS 变量或隐藏域中。
        # 为了安全，这里使用一个更通用的方式寻找数字。
        # 更新：根据原脚本的上下文，这些参数似乎是为了一个外部API。
        # 我们暂时保留原有的匹配逻辑，但加上re.S

        # 如果上面的找不到，尝试原作者的正则
        if not match_lz_lj:
             match_lz_lj = re.search(r".*='([0-9]{4,})'.*='([0-9]{4,})'.*", task_page_content, re.S)

        if not match_lz_lj:
            message = f"第 {account_index} 个账号获取签到参数 (lz, lj) 失败。页面内容可能已更改。"
            print(message)
            print("获取参数失败的页面片段:", task_page_content[:500]) # 打印部分内容用于调试
            return message
        lz, lj = match_lz_lj.group(1), match_lz_lj.group(2)

        match_le = re.search(r".*='([a-zA-Z0-9/+]{40,})'.*", task_page_content, re.S)
        if not match_le:
            message = f"第 {account_index} 个账号获取签到参数 (le) 失败。页面内容可能已更改。"
            print(message)
            print("获取参数失败的页面片段:", task_page_content[:500])
            return message
        le = match_le.group(1)
        print(f"账号 {account_index}: 获取到参数 lz, lj, le。")

        # 3. 调用外部API获取WAF验证数据
        print(f"账号 {account_index}: 调用外部API获取WAF验证数据...")
        api_payload = {"lz": lz, "lj": lj, "le": le, "token": token}
        try:
            r_api = requests.post(EXTERNAL_SIGN_API, json=api_payload, timeout=30)
            r_api.raise_for_status()
            waf_data_str = r_api.text # API返回的应该是字符串格式的data
            if not waf_data_str.strip(): # 检查返回是否为空
                 raise ValueError("外部API返回了空的WAF数据")
            print(f"账号 {account_index}: 外部API调用成功。")
        except requests.exceptions.RequestException as e:
            print(f"第 {account_index} 个账号调用外部API失败: {e}")
            print("请前往“https://zhustatus.azurewebsites.net/”查看“52POJIE-SIGN”的运行状态 (如果API提供者是该网站)")
            message = f"第 {account_index} 个账号调用外部签到API失败: {e}"
            return message
        except ValueError as e:
            print(f"第 {account_index} 个账号调用外部API后获取数据异常: {e}")
            message = f"第 {account_index} 个账号调用外部签到API后数据异常: {e}"
            return message


        # 4. 提交WAF验证
        print(f"账号 {account_index}: 提交WAF验证...")
        # waf_data 应该是 key=value&key=value 格式的字符串
        # 如果API返回的是JSON，需要转换；如果直接是form-data字符串，则直接用
        # 假设API直接返回了可用于POST的字符串数据
        r_waf = session.post(URL_WAF_VERIFY, cookies=cookie_dict, data=waf_data_str)
        r_waf.raise_for_status()
        # print(f"账号 {account_index}: WAF验证提交响应状态: {r_waf.status_code}")
        # print(f"账号 {account_index}: WAF响应内容片段: {r_waf.text[:200]}")


        # 5. 再次访问任务页面以完成/确认签到
        # 这一步是关键，因为之前的apply只是领取任务，这一步可能是通过访问来触发完成，或者检查结果
        print(f"账号 {account_index}: 再次访问任务页面确认签到状态...")
        r_task_final = session.get(URL_TASK_APPLY, cookies=cookie_dict)
        r_task_final.raise_for_status()
        soup_final = BeautifulSoup(r_task_final.text, "html.parser")
        
        # 检查签到结果
        msg_element = soup_final.find("div", id="messagetext")
        if msg_element and msg_element.find("p"):
            result_text = msg_element.find("p").text.strip()
            print(f"账号 {account_index}: 签到结果消息: '{result_text}'")
            if "您需要先登录才能继续本操作" in result_text:
                message = f"第 {account_index} 个账号签到失败：Cookie失效 (操作中提示登录)。"
            elif "恭喜您" in result_text or "已完成" in result_text or "任务已完成" in result_text:
                message = f"第 {account_index} 个账号签到成功: {result_text}"
            elif "不是进行中的任务" in result_text or "任务已过期" in result_text or "已申请过此任务" in result_text:
                # "不是进行中的任务" 可能意味着已经签到过了，或者任务流程不对
                message = f"第 {account_index} 个账号今日已签到或任务状态异常: {result_text}"
            else:
                message = f"第 {account_index} 个账号签到失败: {result_text}"
        else:
            # 如果没有找到标准的消息框，再次检查首页的签到图片
            r_home_check = session.get(URL_HOME, cookies=cookie_dict)
            soup_home_check = BeautifulSoup(r_home_check.text, "html.parser")
            sign_img_elements_check = soup_home_check.select('img.qq_bind[src*="qds.png"], img.qq_bind[src*="wbs.png"], img.qq_bind[src*="hby_s.png"]')
            if any("qds.png" not in img['src'] for img in sign_img_elements_check):
                message = f"第 {account_index} 个账号签到成功 (通过最终首页图片确认)。"
            else:
                message = f"第 {account_index} 个账号签到失败：未能获取明确的签到结果消息，且首页仍显示未签到。"
                print(f"账号 {account_index}: 最终确认页面内容片段: {r_task_final.text[:500]}")

    except requests.exceptions.RequestException as e:
        message = f"第 {account_index} 个账号处理时发生网络错误: {e}"
    except Exception as e:
        message = f"第 {account_index} 个账号处理时发生未知错误: {e}"
    
    print(message)
    return message

def main():
    # 从环境变量获取 TOKEN
    pj52_token = os.environ.get("PJ52_TOKEN")
    if not pj52_token:
        print("错误：请在环境变量中设置 PJ52_TOKEN 的值。")
        notify.send("吾爱破解签到错误", "环境变量 PJ52_TOKEN 未设置")
        sys.exit(1)

    # 从环境变量获取 COOKIEs
    cookies_env = os.environ.get("PJ52_COOKIE")
    if not cookies_env:
        print("错误：请在环境变量中设置 PJ52_COOKIE 的值。")
        notify.send("吾爱破解签到错误", "环境变量 PJ52_COOKIE 未设置")
        sys.exit(1)

    raw_cookie_list = cookies_env.split("&")
    num_accounts = len(raw_cookie_list)
    print(f"检测到 {num_accounts} 个账号配置。")

    overall_summary = []

    for i, raw_cookie in enumerate(raw_cookie_list):
        account_num = i + 1
        # 随机延时，避免请求过于频繁
        if i > 0 : # 第一个账号不需要前置延时
            delay = random.randint(SLEEP_TIME_RANGE[0], SLEEP_TIME_RANGE[1])
            print(f"账号 {account_num}: 等待 {delay} 秒后开始处理...")
            sleep(delay)
        
        result_message = process_account(account_num, raw_cookie.strip(), pj52_token)
        notify.send(f"吾爱破解签到通知 (账号 {account_num})", result_message)
        overall_summary.append(result_message)
        print(f"--- 第 {account_num} 个账号处理完毕 ---\n")

    print("所有账号处理完成。")
    if num_accounts > 1 :
        final_summary_message = "吾爱破解签到任务总结:\n" + "\n".join(overall_summary)
        # 对于多账号，可以发送一个总的通知，如果notify支持长消息的话
        # notify.send("吾爱破解签到总结", final_summary_message)
        print(final_summary_message)


if __name__ == "__main__":
    main()
