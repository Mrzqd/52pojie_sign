#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: main.py (吾爱破解签到)
Author: Mrzqd
Date: 2024/8/22 18:30 (Original), 2025/06/25 (Refactor)
cron: 30 7 * * *
new Env('吾爱破解签到');
"""
import json
import os
import random
import re
import sys
import urllib.parse
from time import sleep
from typing import Dict, Tuple, Optional, List, Any

import requests
from bs4 import BeautifulSoup

# 尝试导入通知模块，如果失败则使用备用方案
try:
    import notify
except ImportError:
    class NotifyPlaceholder:
        @staticmethod
        def send(title: str, content: str) -> None:
            print(f"通知标题: {title}")
            print(f"通知内容: {content}")
    notify = NotifyPlaceholder()


# --- 配置与常量 ---
# 随机等待时间范围（秒）
SLEEP_TIME_RANGE: List[int] = [60, 180] # 稍微降低了默认值，原为 [100, 200]

# 网站URL
URL_BASE: str = "https://www.52pojie.cn/"
URL_HOME: str = URL_BASE
URL_TASK_PAGE: str = URL_BASE + "home.php?mod=task&do=apply&id=2&referer=%2F"
URL_WAF_VERIFY: str = URL_BASE + "waf_zw_verify"

# 外部API URL
URL_EXTERNAL_SIGN_API: str = "https://52pojie-sign-sever.zzboy.tk/api/52pojie"

# 请求头
COMMON_HEADERS: Dict[str, str] = {
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36", # 更新UA
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "sec-ch-ua": '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Referer": URL_BASE,
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 网络请求超时时间（秒）
REQUEST_TIMEOUT: int = 30

# --- 辅助函数 ---

def parse_cookie_str(cookie_str: str) -> Tuple[Optional[Dict[str, str]], str]:
    """
    解析原始Cookie字符串，提取必要的键值对。
    返回 (解析后的cookie字典, 错误信息或None)
    """
    if not cookie_str:
        return None, "Cookie字符串为空"

    try:
        decoded_cookie = urllib.parse.unquote(cookie_str)
    except Exception as e:
        return None, f"Cookie解码失败: {e}"

    cookies_for_requests = {}
    required_keys = {"htVC_2132_saltkey", "htVC_2132_auth"}
    found_keys = set()

    for item in decoded_cookie.split(';'):
        parts = item.split('=', 1)
        if len(parts) == 2:
            key, value = parts[0].strip(), parts[1].strip()
            if key in required_keys:
                # requests库会自动处理cookie值的编码，无需手动quote
                cookies_for_requests[key] = value
                found_keys.add(key)
            # 可以考虑也加入其他cookie，如果网站需要的话
            # elif key.startswith("htVC_2132_"):
            #     cookies_for_requests[key] = value


    if not required_keys.issubset(found_keys):
        missing = ", ".join(list(required_keys - found_keys))
        return None, f"Cookie中缺失必需字段: {missing}"
    
    return cookies_for_requests, ""


def check_status_and_get_params(
    session: requests.Session,
    user_cookies: Dict[str, str]
) -> Tuple[str, Optional[Dict[str, str]]]:
    """
    访问首页检查登录和签到状态，如果未签到则获取签到参数。
    返回 (状态消息, 签到参数字典或None)
    """
    try:
        response = session.get(URL_HOME, headers=COMMON_HEADERS, cookies=user_cookies, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. 检查是否需要登录
        if soup.find('button', class_="pn vm") is not None:
            return "Cookie失效 (需要登录)", None

        # 2. 检查是否已签到 (通过图片 src)
        sign_images = soup.find_all('img', class_="qq_bind") # 假设class是正确的
        qds_icon_found = False # 未签到图标 "qds.png"
        wbs_icon_found = False # 已签到/未补签图标 "wbs.png"
        
        for img_node in sign_images:
            src = img_node.get("src", "")
            if src.endswith("qds.png"):
                qds_icon_found = True
                break
            if src.endswith("wbs.png"):
                wbs_icon_found = True
                break
        
        if wbs_icon_found:
            return "今日已签到 (图片状态wbs.png)", None
        if not qds_icon_found and not wbs_icon_found: # 没有找到任何相关图标
            return "无法确定签到状态 (未找到签到相关图片，可能页面结构改变或Cookie问题)", None
        
        # 如果找到qds.png (未签到)，则继续获取参数
        if qds_icon_found:
            task_response = session.get(URL_TASK_PAGE, headers=COMMON_HEADERS, cookies=user_cookies, timeout=REQUEST_TIMEOUT)
            task_response.raise_for_status()
            task_text = task_response.text
        
            match_lz_lj = re.search(r" renversement\('(\d{4,})'\).* renversement\('(\d{4,})'\)", task_text, re.S)
            if not match_lz_lj:
                match_lz_lj = re.search(r".*='([0-9]{4,})'.*='([0-9]{4,})'.*", task_text, re.S)

            if not match_lz_lj:
                return "未查询到签到参数", None
            lz, lj = match_lz_lj.group(1), match_lz_lj.group(2)

            match_le = re.search(r".*='([a-zA-Z0-9/+]{40,})'.*", task_text, re.S)
            if not match_le:
                return "未查询到签到参数", None
            le = match_le.group(1)
            return "待签到 (参数已获取)", {"lz": lz, "lj": lj, "le": le}

    except requests.exceptions.RequestException as e:
        return f"网络请求失败: {e}", None
    except Exception as e:
        return f"解析页面或获取参数时发生未知错误: {e}", None
    
    return "未知初始状态", None # 默认情况


def execute_signin_flow(
    session: requests.Session,
    user_cookies: Dict[str, str],
    signin_params: Dict[str, str],
    global_token: str
) -> str:
    """执行签到流程，包括调用外部API和提交WAF验证."""
    try:
        # 1. 调用外部API获取WAF payload
        external_api_payload = {
            "lz": signin_params["lz"],
            "lj": signin_params["lj"],
            "le": signin_params["le"],
            "token": global_token
        }
        external_api_response = requests.post(
            URL_EXTERNAL_SIGN_API, json=external_api_payload, timeout=REQUEST_TIMEOUT
        )

        if external_api_response.status_code != 200:
            try:
                error_msg = external_api_response.json().get('msg', external_api_response.text)
            except json.JSONDecodeError:
                error_msg = external_api_response.text
            return f"外部签名API调用失败 ({external_api_response.status_code}): {error_msg}. 请检查API状态: https://zhustatus.azurewebsites.net/"
        
        waf_payload_data = external_api_response.text # 假设API直接返回waf_verify所需data字符串

        # 2. 提交WAF验证
        waf_response = session.post(
            URL_WAF_VERIFY, headers=COMMON_HEADERS, cookies=user_cookies, data=waf_payload_data, timeout=REQUEST_TIMEOUT
        )
        waf_response.raise_for_status() # 检查WAF提交是否成功 (HTTP层面)
        # WAF验证成功通常是302跳转或200 OK但内容提示，这里假定成功后可继续

        # 3. 再次访问任务页面或特定页面以确认/完成签到
        # 原脚本是再次GET url2 (URL_TASK_PAGE)
        final_check_response = session.get(URL_TASK_PAGE, headers=COMMON_HEADERS, cookies=user_cookies, timeout=REQUEST_TIMEOUT)
        final_check_response.raise_for_status()
        
        soup = BeautifulSoup(final_check_response.text, "html.parser")
        message_div = soup.find("div", id="messagetext")
        
        if not message_div:
            return "签到结果未知 (未找到消息区域)"

        message_p = message_div.find("p")
        if not message_p:
            return "签到结果未知 (未找到消息段落)"
            
        result_text = message_p.text.strip()

        if "您需要先登录才能继续本操作" in result_text:
            return "Cookie失效 (签到后验证)"
        if "恭喜" in result_text:
            return "签到成功"
        if "不是进行中的任务" in result_text or "已完成" in result_text: # 有些情况是这个提示
            return "今日已签到 (任务状态反馈)"
        
        return f"签到失败: {result_text}"

    except requests.exceptions.RequestException as e:
        return f"签到流程中网络请求失败: {e}"
    except Exception as e:
        return f"签到流程中发生未知错误: {e}"


def process_single_user(
    user_idx: int,
    user_json_str: str,
    global_token: str,
    session: requests.Session
) -> Dict[str, Any]:
    """处理单个用户的完整签到流程."""
    uid = "未知"
    raw_cookie = user_json_str
    if not raw_cookie:
        msg = "Cookie信息缺失"
        print(f"第 {user_idx} 个账号: {msg}")
        return {"msg": msg, "status_code": "CONFIG_ERROR"}

    user_cookies_dict, error_msg = parse_cookie_str(raw_cookie)
    if error_msg:
        print(f"第 {user_idx} 个账号 : {error_msg}")
        return {"msg": error_msg, "status_code": "COOKIE_PARSE_ERROR"}

    print(f"第 {user_idx} 个账号 : 开始处理...")
    
    status_message, sign_params = check_status_and_get_params(session, user_cookies_dict)

    if status_message == "待签到 (参数已获取)" and sign_params:
        print(f"第 {user_idx} 个账号 : 获取到签到参数，尝试执行签到...")
        final_status_message = execute_signin_flow(session, user_cookies_dict, sign_params, global_token)
        status_message = final_status_message # 更新最终状态
    elif status_message is None and sign_params is None: # 未知情况
        status_message = "检查状态时返回意外结果"


    print(f"第 {user_idx} 个账号 : 最终状态 - {status_message}")
    
    status_code = "SUCCESS"
    if "失败" in status_message or "失效" in status_message or "错误" in status_message or "未知" in status_message:
        status_code = "FAILURE"
    elif "已签到" in status_message:
        status_code = "ALREADY_SIGNED"
        
    return {"msg": status_message, "status_code": status_code}


# --- 主程序 ---
def main():
    global_token = os.environ.get("PJ52_TOKEN")
    if not global_token:
        print("错误: 请在环境变量填入PJ52_TOKEN的值")
        sys.exit(1)

    cookies_env_str = os.environ.get("PJ52_COOKIE")
    if not cookies_env_str:
        print("错误: 请在环境变量填写PJ52_COOKIE的值")
        sys.exit(1)

    user_configs = cookies_env_str.split("&")
    session = requests.Session() # 所有用户共享一个会话

    print(f"吾爱破解签到任务开始，共 {len(user_configs)} 个账号待处理。\n")

    for idx, user_json_config in enumerate(user_configs, 1):
        if idx > 1: # 第一个账号不等待
            sleep_duration = random.randint(SLEEP_TIME_RANGE[0], SLEEP_TIME_RANGE[1])
            print(f"\n--- 随机等待 {sleep_duration} 秒后处理下一个账号 ---")
            sleep(sleep_duration)
        
        print(f"--- 开始处理第 {idx} 个账号 ---")
        log_entry = process_single_user(idx, user_json_config, global_token, session)
        # 单独通知每个账号的结果
        notify.send(f"吾爱签到 - 账号 {idx}", log_entry["msg"])

    print("\n--- 所有账号处理完毕 ---")

    print("\n吾爱破解签到任务结束。")

if __name__ == "__main__":
    main()
