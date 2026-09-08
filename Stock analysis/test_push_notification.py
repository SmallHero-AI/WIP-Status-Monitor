# -*- coding: utf-8 -*-
"""
================================================================================
  V8.5 即時訊號推播測試工具 (test_push_notification.py)
  
  用途：獨立測試 LINE Bot / Telegram / Discord 推播 API 是否運作正常。
  用法：
    1. 測試 LINE Bot:
       python test_push_notification.py --channel line --token "<YOUR_LINE_TOKEN>" --target "<YOUR_USER_ID>"
    2. 測試 Discord Webhook:
       python test_push_notification.py --channel discord --url "<YOUR_DISCORD_WEBHOOK_URL>"
    3. 測試 Telegram Bot:
       python test_push_notification.py --channel telegram --token "<YOUR_TG_TOKEN>" --target "<YOUR_CHAT_ID>"
================================================================================
"""

import argparse
import sys
import json
import requests

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def send_line_push(token, target, message):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    payload = {
        'to': target,
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    return response

def send_discord_push(webhook_url, message):
    headers = {'Content-Type': 'application/json'}
    payload = {'content': message}
    response = requests.post(webhook_url, headers=headers, json=payload, timeout=10)
    return response

def send_telegram_push(token, chat_id, message):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, json=payload, timeout=10)
    return response

def main():
    parser = argparse.ArgumentParser(description="V8.5 即時訊號推播測試工具")
    parser.add_argument("--channel", choices=["line", "discord", "telegram"], required=True, help="推播管道 (line/discord/telegram)")
    parser.add_argument("--token", help="LINE Channel Access Token 或 Telegram Bot Token")
    parser.add_argument("--target", help="LINE User ID 或 Telegram Chat ID")
    parser.add_argument("--url", help="Discord Webhook URL")
    
    args = parser.parse_args()
    
    test_msg = (
        "🚀 【股票量化分析 V8.5】推播連線測試成功！\n"
        "--------------------------------------\n"
        "🔥 [觸發進場測試] 2330 台積電 (多單)\n"
        "📈 策略型態：突破樞軸(Pivot)+RSI轉強\n"
        "💰 預計明日開盤參考價：$950.0\n"
        "🎯 目標停利：+8.0% ($1,026.0)\n"
        "🛡️ 觸發停損：-6.0% ($893.0)\n"
        "--------------------------------------\n"
        "✅ 系統即時連線正常，自動化推播已準備就緒！"
    )
    
    print("=" * 60)
    print(f"  [Start] 正在發送 {args.channel.upper()} 推播測試...")
    print("=" * 60)
    
    try:
        if args.channel == "line":
            if not args.token or not args.target:
                print("❌ 錯誤：測試 LINE 推播時必須提供 --token 與 --target (User ID)")
                return
            res = send_line_push(args.token, args.target, test_msg)
            if res.status_code == 200:
                print("🎉 【LINE 推播成功！】您的手機 LINE 應已收到測試卡片訊息！")
            else:
                print(f"❌ 【LINE 推播失敗】狀態碼: {res.status_code}, 回應: {res.text}")
                
        elif args.channel == "discord":
            if not args.url:
                print("❌ 錯誤：測試 Discord 推播時必須提供 --url (Webhook URL)")
                return
            res = send_discord_push(args.url, test_msg)
            if res.status_code in [200, 204]:
                print("🎉 【Discord 推播成功！】您的 Discord 頻道應已收到測試卡片訊息！")
            else:
                print(f"❌ 【Discord 推播失敗】狀態碼: {res.status_code}, 回應: {res.text}")
                
        elif args.channel == "telegram":
            if not args.token or not args.target:
                print("❌ 錯誤：測試 Telegram 推播時必須提供 --token 與 --target (Chat ID)")
                return
            res = send_telegram_push(args.token, args.target, test_msg)
            if res.status_code == 200:
                print("🎉 【Telegram 推播成功！】您的 Telegram 應已收到測試卡片訊息！")
            else:
                print(f"❌ 【Telegram 推播失敗】狀態碼: {res.status_code}, 回應: {res.text}")
                
    except Exception as e:
        print(f"❌ 推播執行異常: {e}")

if __name__ == "__main__":
    main()
