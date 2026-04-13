from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
from pandas import DataFrame
import talib.abstract as ta
import pandas as pd
import os
import json

class CombinedConstructorStrategy(IStrategy):
    INTERFACE_VERSION = 3

    # Общие настройки (можно переопределять в config.json)
    minimal_roi = {"0": 0.02}
    stoploss = -0.10
    trailing_stop = False
    use_custom_stoploss = False
    timeframe = '5m'
    startup_candle_count: int = 200
    process_only_new_candles = True

    # ==================== ПАРАМЕТРЫ СТРАТЕГИЙ ====================
    min_buy_votes = IntParameter(1, 6, default=3, space='buy')
    min_sell_votes = IntParameter(1, 6, default=3, space='sell')

    use_rsi = True
    rsi_buy = IntParameter(20, 40, default=30, space='buy')
    rsi_sell = IntParameter(60, 80, default=70, space='sell')

    use_macd = True
    macd_fast = IntParameter(8, 20, default=12, space='buy')
    macd_slow = IntParameter(21, 30, default=26, space='buy')
    macd_signal = IntParameter(5, 15, default=9, space='buy')

    use_ema = True
    ema_fast = IntParameter(5, 15, default=8, space='buy')
    ema_slow = IntParameter(15, 30, default=21, space='buy')

    use_bb = True
    bb_period = IntParameter(15, 30, default=20, space='buy')
    bb_std = DecimalParameter(1.5, 2.5, default=2.0, space='buy')

    use_adx = True
    adx_period = IntParameter(10, 30, default=14, space='buy')
    adx_threshold = IntParameter(15, 35, default=25, space='buy')

    use_stoch = True
    stoch_k = IntParameter(5, 15, default=14, space='buy')
    stoch_d = IntParameter(3, 10, default=3, space='buy')
    stoch_buy = IntParameter(10, 30, default=20, space='buy')

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.load_json_settings()

    def load_json_settings(self):
        """Загружает настройки из strategy_settings.json"""
        json_path = os.path.join(os.path.dirname(__file__), "strategy_settings.json")
        
        if not os.path.exists(json_path):
            print("ℹ  Файл strategy_settings.json не найден. Будут использованы значения по умолчанию.")
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                settings = json.load(f)

            # Загружаем флаги включения стратегий
            for flag in ['use_rsi', 'use_macd', 'use_ema', 'use_bb', 'use_adx', 'use_stoch']:
                if flag in settings:
                    setattr(self, flag, bool(settings[flag]))

            # Загружаем все параметры
            param_map = {
                'min_buy_votes': self.min_buy_votes,
                'min_sell_votes': self.min_sell_votes,
                'rsi_buy': self.rsi_buy,
                'rsi_sell': self.rsi_sell,
                'macd_fast': self.macd_fast,
                'macd_slow': self.macd_slow,
                'macd_signal': self.macd_signal,
                'ema_fast': self.ema_fast,
                'ema_slow': self.ema_slow,
                'bb_period': self.bb_period,
                'bb_std': self.bb_std,
                'adx_period': self.adx_period,
                'adx_threshold': self.adx_threshold,
                'stoch_k': self.stoch_k,
                'stoch_d': self.stoch_d,
                'stoch_buy': self.stoch_buy,
            }

            for name, param in param_map.items():
                if name in settings:
                    param.value = settings[name]

            print(f" Настройки успешно загружены из {json_path}")
        except Exception as e:
            print(f" Ошибка при загрузке strategy_settings.json: {e}")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        macd = ta.MACD(dataframe, fastperiod=self.macd_fast.value,
                       slowperiod=self.macd_slow.value,
                       signalperiod=self.macd_signal.value)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=self.ema_fast.value)
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=self.ema_slow.value)

        bb = ta.BBANDS(dataframe, timeperiod=self.bb_period.value,
                       nbdevup=self.bb_std.value, nbdevdn=self.bb_std.value)
        dataframe['bb_lowerband'] = bb['lowerband']
        dataframe['bb_middleband'] = bb['middleband']
        dataframe['bb_upperband'] = bb['upperband']

        dataframe['adx'] = ta.ADX(dataframe, timeperiod=self.adx_period.value)
        dataframe['plus_di'] = ta.PLUS_DI(dataframe, timeperiod=self.adx_period.value)
        dataframe['minus_di'] = ta.MINUS_DI(dataframe, timeperiod=self.adx_period.value)

        stoch = ta.STOCH(dataframe, fastk_period=self.stoch_k.value,
                         slowk_period=self.stoch_d.value,
                         slowd_period=self.stoch_d.value)
        dataframe['stoch_k'] = stoch['slowk']
        dataframe['stoch_d'] = stoch['slowd']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'enter_long'] = 0
        votes_buy = pd.Series(0, index=dataframe.index)

        if self.use_rsi:
            votes_buy += (dataframe['rsi'] < self.rsi_buy.value).astype(int)
        if self.use_macd:
            votes_buy += ((dataframe['macd'] > dataframe['macdsignal']) & 
                         (dataframe['macdhist'] > 0)).astype(int)
        if self.use_ema:
            votes_buy += (dataframe['ema_fast'] > dataframe['ema_slow']).astype(int)
        if self.use_bb:
            votes_buy += (dataframe['close'] < dataframe['bb_lowerband']).astype(int)
        if self.use_adx:
            votes_buy += ((dataframe['adx'] > self.adx_threshold.value) & 
                         (dataframe['plus_di'] > dataframe['minus_di'])).astype(int)
        if self.use_stoch:
            votes_buy += ((dataframe['stoch_k'] < self.stoch_buy.value) & 
                         (dataframe['stoch_d'] < self.stoch_buy.value)).astype(int)

        dataframe.loc[votes_buy >= self.min_buy_votes.value, 'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, 'exit_long'] = 0
        votes_sell = pd.Series(0, index=dataframe.index)

        if self.use_rsi:
            votes_sell += (dataframe['rsi'] > self.rsi_sell.value).astype(int)
        if self.use_macd:
            votes_sell += (dataframe['macd'] < dataframe['macdsignal']).astype(int)
        if self.use_ema:
            votes_sell += (dataframe['ema_fast'] < dataframe['ema_slow']).astype(int)
        if self.use_bb:
            votes_sell += (dataframe['close'] > dataframe['bb_upperband']).astype(int)
        if self.use_adx:
            votes_sell += ((dataframe['adx'] > self.adx_threshold.value) & 
                          (dataframe['plus_di'] < dataframe['minus_di'])).astype(int)
        if self.use_stoch:
            votes_sell += ((dataframe['stoch_k'] > 80) & 
                          (dataframe['stoch_d'] > 80)).astype(int)

        dataframe.loc[votes_sell >= self.min_sell_votes.value, 'exit_long'] = 1
        return dataframe
    