# -*- coding: utf-8 -*-
"""
================================================================================
  V8.5 訊號自動推播發送工具 (send_signal_notifications_v8_5.py)
  
  用途：讀取 leaderboard_v8_5.json，篩選當日最新觸發之進場 (TRIGGER_ENTRY)
        與離場 (TRIGGER_EXIT) 訊號個股，格式化卡片訊息並透過 LINE Broadcast API
        全自動推播到使用者的 LINE 帳號。
================================================================================
"""

import os
import sys
import json
import requests
import datetime

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

SCRIPT_DIR = r"E:\G-AI-1\Stock analysis"
LEADERBOARD_PATH = os.path.join(SCRIPT_DIR, "修正版_V6_Server", "public", "leaderboard_v8_5.json")

# LINE Channel 帳密 (用於自動產生發行 Token)
LINE_CHANNEL_ID = "2011494352"
LINE_CHANNEL_SECRET = "4d26129a2b224eec5ff2343ea11bc966"

def get_line_channel_access_token():
    url = "https://api.line.me/v2/oauth/accessToken"
    data = {
        "grant_type": "client_credentials",
        "client_id": LINE_CHANNEL_ID,
        "client_secret": LINE_CHANNEL_SECRET
    }
    try:
        res = requests.post(url, data=data, timeout=10)
        if res.status_code == 200:
            return res.json().get("access_token")
        else:
            print(f"⚠️ 取得 LINE OAuth Token 失敗 ({res.status_code}): {res.text}")
            return None
    except Exception as e:
        print(f"❌ 取得 LINE OAuth Token 異常: {e}")
        return None

def send_line_broadcast(token, text_message):
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "messages": [
            {
                "type": "text",
                "text": text_message
            }
        ]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        return res
    except Exception as e:
        print(f"❌ LINE 廣播請求失敗: {e}")
        return None

def main():
    print("=" * 60)
    print("  [Start] V8.5 今日選股與觸發訊號自動推播程序...")
    print("=" * 60)

    if not os.path.exists(LEADERBOARD_PATH):
        print(f"⚠️ 排行榜檔案不存在: {LEADERBOARD_PATH}，跳過推播。")
        return

    try:
        with open(LEADERBOARD_PATH, 'r', encoding='utf-8') as f:
            leaderboard = json.load(f)
    except Exception as e:
        print(f"❌ 讀取 {LEADERBOARD_PATH} 失敗: {e}")
        return

    trigger_entries = []
    trigger_exits = []
    current_holdings = []

    for item in leaderboard:
        sig = item.get("signalInfo")
        if not sig:
            continue
        status = sig.get("status")
        if status == "TRIGGER_ENTRY":
            trigger_entries.append(item)
        elif status == "TRIGGER_EXIT":
            trigger_exits.append(item)
        elif status == "HOLDING":
            current_holdings.append(item)

    today_str = datetime.date.today().strftime("%Y-%m-%d")

    print(f"[統計] 今日新觸發進場: {len(trigger_entries)} 檔, 今日新觸發出場: {len(trigger_exits)} 檔, 持倉中: {len(current_holdings)} 檔")

    if not trigger_entries and not trigger_exits:
        print("💡 今日無新增觸發之進出場訊號，跳過推播訊息發送。")
        return

    # 格式化訊息
    msg_lines = [
        f"📊 【股票量化分析 V8.5】今日最新個股觸發通知 ({today_str})\n"
    ]

    if trigger_entries:
        msg_lines.append("🔥 【今日剛觸發進場 (預計明日開盤執行)】")
        for idx, item in enumerate(trigger_entries[:8], 1): # 最多列出前8檔避免超長
            sig = item["signalInfo"]
            direction = sig.get("direction", "多單")
            code = item["code"]
            name = item["name"]
            strat = item["strategy"].split(" & ")[0]
            entry_p = sig.get("targetEntryPrice", 0)
            tp_p = sig.get("tpPrice", "-")
            sl_p = sig.get("slPrice", "-")
            msg_lines.append(f"{idx}. {code} {name} ({direction}) | 勝率: {item['winRate']:.1f}%")
            msg_lines.append(f"   ► 策略: {strat}")
            msg_lines.append(f"   ► 預計進場參考價: ${entry_p} (停利: ${tp_p} / 停損: ${sl_p})")

        if len(trigger_entries) > 8:
            msg_lines.append(f"   ...等共 {len(trigger_entries)} 檔個股觸發進場。\n")
        else:
            msg_lines.append("")

    if trigger_exits:
        msg_lines.append("⚠️ 【今日剛觸發平倉 (預計明日開盤執行)】")
        for idx, item in enumerate(trigger_exits[:8], 1):
            sig = item["signalInfo"]
            direction = sig.get("direction", "多單")
            code = item["code"]
            name = item["name"]
            reason = sig.get("reason", "指標觸發")
            roi = sig.get("roi", 0)
            msg_lines.append(f"{idx}. {code} {name} ({direction}) | 預估損益率: {roi:+.1f}%")
            msg_lines.append(f"   ► 原因: {reason}")
        if len(trigger_exits) > 8:
            msg_lines.append(f"   ...等共 {len(trigger_exits)} 檔個股觸發離場。\n")
        else:
            msg_lines.append("")

    msg_lines.append("--------------------------------------")
    msg_lines.append("🌐 完整選股與 K 線線圖請登入 Web 儀表板查看！")

    final_message = "\n".join(msg_lines)

    # 取得 OAuth Token 並發送
    token = get_line_channel_access_token()
    if token:
        res = send_line_broadcast(token, final_message)
        if res and res.status_code == 200:
            print("✅ [成功] LINE 廣播推播發送成功！所有訂閱用戶均已接收最新警示訊息。")
        else:
            status_c = res.status_code if res else "Unknown"
            resp_t = res.text if res else "No response"
            print(f"❌ [失敗] LINE 廣播推播失敗 ({status_c}): {resp_t}")

if __name__ == "__main__":
    main()
