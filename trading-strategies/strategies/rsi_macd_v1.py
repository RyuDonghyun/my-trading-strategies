from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta


class RSI_MACD_v1(IStrategy):
    """
    RSI + MACD + 볼린저밴드 복합 전략 (바이낸스 선물)
    
    Long  진입: RSI < 35  AND  MACD 골든크로스  AND  가격 < BB 하단
    Short 진입: RSI > 65  AND  MACD 데드크로스  AND  가격 > BB 상단
    청산:       RSI 중립대 복귀 OR BB 중심선 도달
    
    버전: 1.0.0
    작성: Claude (MCP 자동매매 파이프라인)
    최종수정: 2025-05-11
    """

    INTERFACE_VERSION = 3
    can_short = True                 # 선물: 숏 포지션 허용

    # ── 하이퍼파라미터 (최적화 가능) ──────────────────────────
    rsi_buy  = IntParameter(25, 40, default=35, space="buy")
    rsi_sell = IntParameter(60, 75, default=65, space="sell")
    bb_std   = DecimalParameter(1.5, 2.5, default=2.0, space="buy")

    # ── 기본 설정 ─────────────────────────────────────────────
    timeframe          = "15m"
    stoploss           = -0.03       # 3% 손절
    trailing_stop      = True
    trailing_stop_positive = 0.015   # 수익 1.5% 이후 트레일링
    minimal_roi        = {"0": 0.04, "30": 0.02, "60": 0.01}

    startup_candle_count = 50        # 지표 워밍업 캔들 수

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        # MACD
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"]        = macd["macd"]
        dataframe["macd_signal"] = macd["macdsignal"]
        dataframe["macd_hist"]   = macd["macdhist"]

        # 볼린저밴드
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=float(self.bb_std.value),
                       nbdevdn=float(self.bb_std.value))
        dataframe["bb_upper"]  = bb["upperband"]
        dataframe["bb_middle"] = bb["middleband"]
        dataframe["bb_lower"]  = bb["lowerband"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # ── Long 진입 ──────────────────────────────────────────
        dataframe.loc[
            (dataframe["rsi"] < self.rsi_buy.value) &
            (dataframe["macd"] > dataframe["macd_signal"]) &          # MACD 골든크로스
            (dataframe["macd"].shift(1) < dataframe["macd_signal"].shift(1)) &
            (dataframe["close"] < dataframe["bb_lower"]) &
            (dataframe["volume"] > 0),
            "enter_long",
        ] = 1

        # ── Short 진입 ─────────────────────────────────────────
        dataframe.loc[
            (dataframe["rsi"] > self.rsi_sell.value) &
            (dataframe["macd"] < dataframe["macd_signal"]) &          # MACD 데드크로스
            (dataframe["macd"].shift(1) > dataframe["macd_signal"].shift(1)) &
            (dataframe["close"] > dataframe["bb_upper"]) &
            (dataframe["volume"] > 0),
            "enter_short",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Long 청산: RSI 중립 복귀 OR BB 중심선 돌파
        dataframe.loc[
            (dataframe["rsi"] > 55) |
            (dataframe["close"] > dataframe["bb_middle"]),
            "exit_long",
        ] = 1

        # Short 청산: RSI 중립 복귀 OR BB 중심선 하향 돌파
        dataframe.loc[
            (dataframe["rsi"] < 45) |
            (dataframe["close"] < dataframe["bb_middle"]),
            "exit_short",
        ] = 1

        return dataframe
