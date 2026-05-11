# Trading Strategies

Claude + MCP 기반 바이낸스 선물 자동매매 전략 저장소

## 구조

```
trading-strategies/
├── strategies/          # Freqtrade 전략 파일
│   ├── rsi_macd_v1.py
│   └── bb_cross_v1.py
├── backtests/           # 백테스트 결과
│   └── YYYY-MM-DD/
│       ├── result.json
│       └── summary.md
├── config/              # 거래소·봇 설정
│   ├── config_dryrun.json
│   └── config_live.json
├── logs/                # 매매 로그
│   └── YYYY-MM-DD.log
├── notebooks/           # 분석 노트북
│   └── strategy_analysis.ipynb
└── scripts/             # 유틸리티 스크립트
    ├── slack_notify.py
    └── backtest_runner.py
```

## 전략 목록

| 전략 | 버전 | 상태 | 승률 | PnL |
|------|------|------|------|-----|
| RSI+MACD | v1 | 드라이런 | - | - |
| BB+Cross | v1 | 개발 중 | - | - |

## 빠른 시작

```bash
# 드라이런 시작
freqtrade trade --config config/config_dryrun.json --strategy RSI_MACD_v1

# 백테스트
freqtrade backtesting --config config/config_dryrun.json --strategy RSI_MACD_v1 --timerange 20240101-20241231
```

## 커밋 컨벤션

```
feat(strategy): RSI_MACD_v1 롱 진입 조건 추가
fix(config): 레버리지 5x → 3x 조정
backtest(RSI_MACD_v1): 2024Q1 결과 기록
log(trade): 2025-05-11 매매 일지
```
