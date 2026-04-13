from freqtrade.strategy import IStrategy
from pandas import DataFrame
import pandas as pd
import numpy as np
from datetime import datetime


class SupplyDemandZones(IStrategy):
    """
    Supply/Demand зоны (4h) + вход при касании зоны на 5m
    Порт твоего бота под Freqtrade (без bias)
    """

    INTERFACE_VERSION = 3

    # ================= НАСТРОЙКИ =================
    timeframe = '15m'
    informative_timeframe = '4h'

    ATR_PERIOD = 100
    MAX_ZONES = 20
    ZONE_TOLERANCE = 0.003
    INVALIDATION_METHOD = "close"
    MAX_ZONE_ATR = 7

    # Freqtrade параметры (подставь свои)
    minimal_roi = {"0": 0.09}
    stoploss = -0.04
    trailing_stop = False
    use_custom_stoploss = False
    process_only_new_candles = True
    startup_candle_count: int = 200

    # ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================
    def is_zone_broken(self, df: DataFrame, zone: dict) -> bool:
        start_idx = zone['start_bar'] + 1
        if start_idx >= len(df):
            return False
        slice_df = df.iloc[start_idx:]
        if zone['type'] == 'supply':
            break_level = slice_df['close'].max() if self.INVALIDATION_METHOD == "close" else slice_df['high'].max()
            return break_level > zone['high']
        else:  # demand
            break_level = slice_df['close'].min() if self.INVALIDATION_METHOD == "close" else slice_df['low'].min()
            return break_level < zone['low']

    def build_zone(self, df: DataFrame, i: int, zone_type: str) -> dict:
        o = df['open'].iloc[i]
        c = df['close'].iloc[i]
        h = df['high'].iloc[i]
        l = df['low'].iloc[i]
        atr = df['atr'].iloc[i]
        max_size = atr * self.MAX_ZONE_ATR

        if zone_type == 'demand':
            low = l
            high = min(o, c)
            if (high - low) > max_size:
                high = low + max_size
            return {"low": low, "high": high, "start_bar": i, "type": "demand"}
        else:
            low = max(o, c)
            high = h
            if (high - low) > max_size:
                low = high - max_size
            return {"low": low, "high": high, "start_bar": i, "type": "supply"}

    def is_bullish_engulfing(self, df: DataFrame, i: int) -> bool:
        if i < 1:
            return False
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        return (prev['close'] >= prev['open'] and
                curr['close'] <= curr['open'] and
                curr['open'] < prev['close'] and curr['close'] > prev['open'])

    def is_bearish_engulfing(self, df: DataFrame, i: int) -> bool:
        if i < 1:
            return False
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        return (prev['close'] <= prev['open'] and
                curr['close'] >= curr['open'] and
                curr['open'] > prev['close'] and curr['close'] < prev['open'])

    def is_bullish_pinbar_df(self, df: DataFrame, i: int) -> bool:
        candle = df.iloc[i]
        o, h, l, c = candle['open'], candle['high'], candle['low'], candle['close']
        body = abs(c - o)
        total_range = h - l
        if total_range == 0 or body > 0.3 * total_range or body == 0:
            return False
        if c <= o:
            return False
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        return lower_wick >= body * 2 and upper_wick <= body * 0.5

    def is_bearish_pinbar_df(self, df: DataFrame, i: int) -> bool:
        candle = df.iloc[i]
        o, h, l, c = candle['open'], candle['high'], candle['low'], candle['close']
        body = abs(c - o)
        total_range = h - l
        if total_range == 0 or body > 0.3 * total_range or body == 0:
            return False
        if c >= o:
            return False
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        return upper_wick >= body * 2 and lower_wick <= body * 0.5

    def price_in_zone(self, price: float, zone: dict) -> bool:
        return (zone["low"] * (1 - self.ZONE_TOLERANCE) <= price <= zone["high"] * (1 + self.ZONE_TOLERANCE))

    def _add_atr(self, df: DataFrame) -> DataFrame:
        df = df.copy()
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window=self.ATR_PERIOD).mean()
        return df

    def _compute_active_zones(self, informative: DataFrame) -> DataFrame:
        informative = informative.reset_index(drop=True)
        informative = self._add_atr(informative)

        active_supply = []
        active_demand = []

        informative['active_supply_zones'] = None
        informative['active_demand_zones'] = None

        min_idx = self.ATR_PERIOD + 10

        for i in range(len(informative)):
            if i < min_idx or pd.isna(informative['atr'].iloc[i]):
                informative.at[i, 'active_supply_zones'] = []
                informative.at[i, 'active_demand_zones'] = []
                continue

            # Формирование новых зон (без lookahead!)
            if self.is_bullish_pinbar_df(informative, i) or self.is_bullish_engulfing(informative, i):
                zone = self.build_zone(informative, i, "demand")
                active_demand.append(zone)

            if self.is_bearish_pinbar_df(informative, i) or self.is_bearish_engulfing(informative, i):
                zone = self.build_zone(informative, i, "supply")
                active_supply.append(zone)

            # Проверка пробития
            current_slice = informative.iloc[:i+1]
            active_supply = [z for z in active_supply if not self.is_zone_broken(current_slice, z)]
            active_demand = [z for z in active_demand if not self.is_zone_broken(current_slice, z)]

            # Ограничение по количеству + сортировка по свежести
            active_supply = sorted(active_supply, key=lambda z: z["start_bar"], reverse=True)[:self.MAX_ZONES]
            active_demand = sorted(active_demand, key=lambda z: z["start_bar"], reverse=True)[:self.MAX_ZONES]

            # Сохраняем
            informative.at[i, 'active_supply_zones'] = active_supply.copy()
            informative.at[i, 'active_demand_zones'] = active_demand.copy()

        return informative

    def _is_in_any_demand_zone(self, row) -> bool:
        zones = row.get('active_demand_zones')
        if not isinstance(zones, list) or not zones:
            return False
        price = row['close']
        return any(self.price_in_zone(price, z) for z in zones)

    def _is_in_any_supply_zone(self, row) -> bool:
        zones = row.get('active_supply_zones')
        if not isinstance(zones, list) or not zones:
            return False
        price = row['close']
        return any(self.price_in_zone(price, z) for z in zones)

    # ================= ОСНОВНАЯ ЛОГИКА =================
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Получаем 4h данные
        informative = self.dp.get_pair_dataframe(metadata['pair'], self.informative_timeframe)

        if len(informative) < self.ATR_PERIOD + 30:
            dataframe['enter_long'] = 0
            dataframe['enter_short'] = 0
            return dataframe

        # Прогрессивно считаем активные зоны (без bias)
        informative = self._compute_active_zones(informative)

        # Мержим зоны на 5m таймфрейм (последние актуальные)
        informative_merge = informative[['date', 'active_supply_zones', 'active_demand_zones']].copy()
        dataframe = pd.merge_asof(
            dataframe.sort_values('date'),
            informative_merge.sort_values('date'),
            on='date',
            direction='backward'
        )

        # Сигналы
        dataframe['in_demand_zone'] = dataframe.apply(self._is_in_any_demand_zone, axis=1)
        dataframe['in_supply_zone'] = dataframe.apply(self._is_in_any_supply_zone, axis=1)

        dataframe['enter_long'] = (dataframe['in_demand_zone']).astype(int)
        dataframe['enter_short'] = (dataframe['in_supply_zone']).astype(int)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Просто возвращаем уже посчитанные колонки
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['exit_long'] = 0
        dataframe['exit_short'] = 0
        return dataframe