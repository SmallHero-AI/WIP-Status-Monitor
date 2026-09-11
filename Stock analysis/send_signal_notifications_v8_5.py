# -*- coding: utf-8 -*-
"""
================================================================================
  V8.5 訊號自動推播發送工具 (send_signal_notifications_v8_5.py)
  
  用途：讀取 leaderboard_v8_5.json，篩選當日最新觸發之進場 (TRIGGER_ENTRY)
        與離場 (TRIGGER_EXIT) 訊號個股，格式化卡片訊息並透過 LINE Broadcast API
        全自動推播到使用者的 LINE 帳號。
        內建「當日防重複推播機制」，同一天相同訊號不會重複洗版發送。
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
PUSH_LOG_PATH = os.path.join(SCRIPT_DIR, "sent_push_log_v8_5.json")

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

def load_push_log():
    if os.path.exists(PUSH_LOG_PATH):
        try:
            with open(PUSH_LOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_push_log(log_data):
    try:
        with open(PUSH_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 寫入推播紀錄檔失敗: {e}")

def main():
    print("=" * 60)
    print("  [Start] V8.5 今日選股與觸發訊號自動推播程序...")
    print("=" * 60)

    force_send = "--force" in sys.argv or "-f" in sys.argv

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
        hd = item.get("holding")
        if not sig and not hd:
            continue

        tpPct = item.get("tp", 6.0)
        slPct = item.get("sl", 6.0)
        isShort = item.get("type") == "short"

        buyP = hd.get("buyPrice", 0) if hd else (sig.get("entryPrice") or sig.get("buyPrice", 0) if sig else 0)
        currP = hd.get("currentPrice", 0) if hd else (sig.get("currentPrice", 0) if sig else 0)

        isTp = False
        isSl = False
        tpVal = 0.0
        slVal = 0.0

        tpVal = (sig.get("tpPrice") if sig else None) or (hd.get("tpPrice") if hd else None)
        slVal = (sig.get("slPrice") if sig else None) or (hd.get("slPrice") if hd else None)

        if (tpVal is None or slVal is None) and buyP > 0:
            tpVal = buyP * (1 + (-1 if isShort else 1) * (tpPct / 100))
            slVal = buyP * (1 + (1 if isShort else -1) * (slPct / 100))

        if buyP > 0 and currP > 0 and tpVal is not None and slVal is not None:
            if not isShort:
                if currP >= tpVal: isTp = True
                if currP <= slVal: isSl = True
            else:
                if currP <= tpVal: isTp = True
                if currP >= slVal: isSl = True

        status = sig.get("status") if sig else None

        if sig:
            if isTp or isSl or status == "TRIGGER_EXIT":
                if isTp:
                    item["_exit_reason"] = f"🎯 達標停利 (現價 ${currP:.2f} 達預計停利價 ${tpVal:.2f})"
                elif isSl:
                    item["_exit_reason"] = f"🛑 觸發停損 (現價 ${currP:.2f} 觸及預計停損價 ${slVal:.2f})"
                else:
                    item["_exit_reason"] = sig.get("reason", "指標轉弱觸發離場")
                trigger_exits.append(item)
            elif status == "TRIGGER_ENTRY":
                trigger_entries.append(item)
            else:
                current_holdings.append(item)
        elif hd:
            if isTp or isSl:
                if isTp:
                    item["_exit_reason"] = f"🎯 達標停利 (現價 ${currP:.2f} 達預計停利價 ${tpVal:.2f})"
                elif isSl:
                    item["_exit_reason"] = f"🛑 觸發停損 (現價 ${currP:.2f} 觸及預計停損價 ${slVal:.2f})"
                trigger_exits.append(item)
            else:
                current_holdings.append(item)

    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # 解析最新 K 線行情實際觸發日期
    latest_k_date = None
    all_sigs = trigger_entries + trigger_exits + current_holdings
    if all_sigs:
        sample_sig = (all_sigs[0].get("signalInfo") or {})
        raw_d = str(sample_sig.get("triggerDate") or sample_sig.get("buyDate") or "").replace("-", "")
        if len(raw_d) == 8:
            latest_k_date = f"{raw_d[:4]}-{raw_d[4:6]}-{raw_d[6:]}"

    data_date_str = latest_k_date if latest_k_date else today_str

    print(f"[統計] 最新行情日期({data_date_str}) - 觸發進場: {len(trigger_entries)} 檔, 觸發出場: {len(trigger_exits)} 檔, 持倉中: {len(current_holdings)} 檔")

    # 生成當日訊號指紋
    entry_codes = sorted([x['code'] for x in trigger_entries])
    exit_codes = sorted([x['code'] for x in trigger_exits])
    signal_fingerprint = f"{data_date_str}_entry:{','.join(entry_codes)}_exit:{','.join(exit_codes)}"

    # 檢查當日防重複機制
    push_log = load_push_log()
    today_record = push_log.get(data_date_str)

    if today_record and not force_send:
        last_fingerprint = today_record.get("fingerprint")
        last_sent_time = today_record.get("sent_time", "未知時間")
        if last_fingerprint == signal_fingerprint:
            print(f"🛡️ [當日防重複保護] {data_date_str} 行情訊號已於 {last_sent_time} 推播完成，自動跳過發送！")
            print("💡 (提示: 若需強制重新推播，請帶入 --force 或 -f 參數執行)")
            return

    # 格式化訊息
    msg_lines = [
        f"📊 【股票量化分析 V8.5】最新個股觸發通知 ({data_date_str} 行情)\n"
    ]

    if trigger_entries:
        msg_lines.append("🔥 【今日剛觸發進場 (預計明日開盤執行)】")
        for idx, item in enumerate(trigger_entries[:8], 1): # 最多列出前8檔避免超長
            sig = item.get("signalInfo", {})
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
            sig = item.get("signalInfo") or {}
            hd = item.get("holding") or {}
            direction = sig.get("direction") or (item.get("posType") or "多單")
            code = item["code"]
            name = item["name"]
            reason = item.get("_exit_reason") or sig.get("reason", "指標轉弱觸發離場")
            roi = sig.get("roi") if (sig and sig.get("roi") is not None) else hd.get("roi", 0)
            msg_lines.append(f"{idx}. {code} {name} ({direction}) | 預估損益率: {roi:+.1f}%")
            msg_lines.append(f"   ► 原因: {reason}")
        if len(trigger_exits) > 8:
            msg_lines.append(f"   ...等共 {len(trigger_exits)} 檔個股觸發離場。\n")
        else:
            msg_lines.append("")

    if not trigger_entries and not trigger_exits:
        msg_lines.append("💡 今日無新增觸發之進出場訊號，策略持倉狀況維持穩定。")
        msg_lines.append(f"📦 【現正持倉總覽 (共 {len(current_holdings)} 檔)】")
        for idx, item in enumerate(current_holdings[:5], 1):
            hd = item.get("holding") or {}
            sig = item.get("signalInfo") or {}
            code = item["code"]
            name = item["name"]
            direction = hd.get("posType") or sig.get("direction", "多單")
            roi = hd.get("roi") if (hd and hd.get("roi") is not None) else sig.get("roi", 0)
            msg_lines.append(f"   {idx}. {code} {name} ({direction}) | 未實現 ROI: {roi:+.1f}%")
        if len(current_holdings) > 5:
            msg_lines.append(f"   ...等共 {len(current_holdings)} 檔續抱中。\n")
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
            # 更新防重複紀錄檔
            now_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            push_log[data_date_str] = {
                "sent_time": now_time_str,
                "fingerprint": signal_fingerprint,
                "entries_count": len(trigger_entries),
                "exits_count": len(trigger_exits)
            }
            save_push_log(push_log)
        else:
            status_c = res.status_code if res else "Unknown"
            resp_t = res.text if res else "No response"
            print(f"❌ [失敗] LINE 廣播推播失敗 ({status_c}): {resp_t}")

if __name__ == "__main__":
    main()

