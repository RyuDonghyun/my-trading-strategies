"""
slack_notify.py — Freqtrade 매매 신호 → Slack 자동 알림

사용법:
    python scripts/slack_notify.py --event entry --pair BTCUSDT \
        --side long --price 65000 --rsi 32.4 --macd cross_up
"""

import argparse
import json
import os
from datetime import datetime

import requests

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL", "")
CHANNEL       = os.environ.get("SLACK_TRADING_CHANNEL", "#trading-signals")


# ── 메시지 템플릿 ────────────────────────────────────────────
def build_entry_message(pair: str, side: str, price: float,
                         rsi: float, macd: str, size: float) -> dict:
    emoji  = ":chart_with_upwards_trend:" if side == "long" else ":chart_with_downwards_trend:"
    color  = "#2eb886" if side == "long" else "#e01e5a"
    action = "LONG 진입" if side == "long" else "SHORT 진입"
    now    = datetime.now().strftime("%Y-%m-%d %H:%M KST")

    return {
        "channel": CHANNEL,
        "attachments": [{
            "color": color,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{emoji} {action} — {pair}"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*진입가*\n`${price:,.2f}`"},
                        {"type": "mrkdwn", "text": f"*포지션 규모*\n`{size} USDT`"},
                        {"type": "mrkdwn", "text": f"*RSI (14)*\n`{rsi:.1f}`"},
                        {"type": "mrkdwn", "text": f"*MACD*\n`{macd}`"},
                    ]
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"Claude AutoTrader · {now}"}]
                }
            ]
        }]
    }


def build_exit_message(pair: str, side: str, entry_price: float,
                        exit_price: float, pnl: float, pnl_pct: float) -> dict:
    profit = pnl >= 0
    emoji  = ":white_check_mark:" if profit else ":x:"
    color  = "#2eb886" if profit else "#e01e5a"
    now    = datetime.now().strftime("%Y-%m-%d %H:%M KST")

    return {
        "channel": CHANNEL,
        "attachments": [{
            "color": color,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{emoji} 포지션 청산 — {pair}"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*방향*\n`{side.upper()}`"},
                        {"type": "mrkdwn", "text": f"*진입가 → 청산가*\n`${entry_price:,.2f}` → `${exit_price:,.2f}`"},
                        {"type": "mrkdwn", "text": f"*손익 (USDT)*\n`{'+'if profit else ''}{pnl:.2f}`"},
                        {"type": "mrkdwn", "text": f"*수익률*\n`{'+'if profit else ''}{pnl_pct:.2f}%`"},
                    ]
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"Claude AutoTrader · {now}"}]
                }
            ]
        }]
    }


def build_daily_summary(total_trades: int, win_rate: float,
                         daily_pnl: float, open_positions: int) -> dict:
    profit = daily_pnl >= 0
    color  = "#2eb886" if profit else "#e01e5a"
    today  = datetime.now().strftime("%Y-%m-%d")

    return {
        "channel": CHANNEL,
        "attachments": [{
            "color": color,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f":bar_chart: 일일 결산 — {today}"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*총 거래 수*\n`{total_trades}건`"},
                        {"type": "mrkdwn", "text": f"*승률*\n`{win_rate:.1f}%`"},
                        {"type": "mrkdwn", "text": f"*일 손익*\n`{'+'if profit else ''}{daily_pnl:.2f} USDT`"},
                        {"type": "mrkdwn", "text": f"*오픈 포지션*\n`{open_positions}개`"},
                    ]
                }
            ]
        }]
    }


# ── 전송 ────────────────────────────────────────────────────
def send_to_slack(payload: dict) -> bool:
    if not SLACK_WEBHOOK:
        print("[ERROR] SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
        return False

    resp = requests.post(SLACK_WEBHOOK, json=payload, timeout=10)
    if resp.status_code == 200:
        print(f"[OK] Slack 알림 전송 완료")
        return True
    else:
        print(f"[ERROR] Slack 전송 실패: {resp.status_code} {resp.text}")
        return False


# ── CLI ─────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Slack 트레이딩 알림")
    parser.add_argument("--event",  choices=["entry", "exit", "summary"], required=True)
    parser.add_argument("--pair",   default="BTCUSDT")
    parser.add_argument("--side",   choices=["long", "short"], default="long")
    parser.add_argument("--price",  type=float, default=0)
    parser.add_argument("--rsi",    type=float, default=0)
    parser.add_argument("--macd",   default="cross_up")
    parser.add_argument("--size",   type=float, default=50)
    parser.add_argument("--entry-price", type=float, default=0)
    parser.add_argument("--exit-price",  type=float, default=0)
    parser.add_argument("--pnl",    type=float, default=0)
    parser.add_argument("--pnl-pct",type=float, default=0)
    args = parser.parse_args()

    if args.event == "entry":
        payload = build_entry_message(args.pair, args.side, args.price,
                                       args.rsi, args.macd, args.size)
    elif args.event == "exit":
        payload = build_exit_message(args.pair, args.side, args.entry_price,
                                      args.exit_price, args.pnl, args.pnl_pct)
    else:
        payload = build_daily_summary(0, 0, 0, 0)

    send_to_slack(payload)
