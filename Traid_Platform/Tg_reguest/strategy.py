import asyncio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import time
import os
import telebot

# ================= CONFIG =================
BOT_TOKEN = "8736878634:AAFsQyL8z7hu0gq3n6Yrq43d_fsKHFMcfac"
CHAT_ID = "1420484889"                    # например -1001234567890 или твой ID

ZONE_TF = "5m"
ZONE_LIMIT = 1500
ATR_PERIOD = 100
MIN_MOVE_MULT = 2
LOOKAHEAD = 10
MAX_ZONES = 20
ZONE_TOLERANCE = 0.001
INVALIDATION_METHOD = "close"
SCAN_INTERVAL_SEC = 200
MAX_CONCURRENT = 12
CHART_CANDLES = 400

MIN_ZONE_SCORE = 7
SWING_LEFT = 2
SWING_RIGHT = 2
IMPULSE_MIN_ATR = 4
MAX_ZONE_ATR = 7

# ================= СИМВОЛЫ =================
SYMBOLS = [
    "BTC-USDT",
    "SOL-USDT",
    "ADA-USDT",
    "XRP-USDT",
    "JUP-USDT",
    "APT-USDT",
    "MANA-USDT",
    "SAND-USDT",
    "DOT-USDT",
    "AVAX-USDT",
    "ALGO-USDT",
    "JST-USDT",
    
]

# ================= EXCHANGE =================
API_KEY = '5fRzEbXkRe5aAVoHhOQRuDwJTmwSAjJJLyJHNZQpPAbVBfmaaGDiding9se5bsf3'
API_SECRET = 'hh3UWGoKhQ7yjorMu9H2snJnZlic13JXNSs65PawHEukQT0dKMMx8ps2aXsSrj8Q'

from binance_client import BinanceClient
bx = BinanceClient(API_KEY, API_SECRET, testnet=False)

# ================= TELEGRAM =================
bot = telebot.TeleBot(BOT_TOKEN)

def send_telegram(image_buffer, caption):
    """Отправка через telebot (самый стабильный вариант)"""
    try:
        image_buffer.seek(0)
        bot.send_photo(
            chat_id=CHAT_ID,
            photo=image_buffer,
            caption=caption,
            parse_mode="HTML"
        )
        print("✅ Сообщение успешно отправлено в Telegram")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return False

# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================
def is_zone_broken(df, zone):
    start_idx = zone['start_bar'] + 1
    if start_idx >= len(df):
        return False
    slice_df = df.iloc[start_idx:]
    if zone['type'] == 'supply':
        break_level = slice_df['close'].max() if INVALIDATION_METHOD == "close" else slice_df['high'].max()
        return break_level > zone['high']
    else:
        break_level = slice_df['close'].min() if INVALIDATION_METHOD == "close" else slice_df['low'].min()
        return break_level < zone['low']

def is_bullish_engulfing(df, i):
    if i < 1: return False
    prev = df.iloc[i-1]
    curr = df.iloc[i]
    return (prev['close'] >= prev['open'] and curr['close'] <= curr['open'] and
            curr['open'] < prev['close'] and curr['close'] > prev['open'])

def is_bearish_engulfing(df, i):
    if i < 1: return False
    prev = df.iloc[i-1]
    curr = df.iloc[i]
    return (prev['close'] <= prev['open'] and curr['close'] >= curr['open'] and
            curr['open'] > prev['close'] and curr['close'] < prev['open'])

def is_bullish_pinbar_df(df, i):
    candle = df.iloc[i]
    o, h, l, c = candle['open'], candle['high'], candle['low'], candle['close']
    body = abs(c - o)
    total_range = h - l
    if total_range == 0 or body > 0.3 * total_range or body == 0: return False
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    return c > o and lower_wick >= body * 2 and upper_wick <= body * 0.5

def is_bearish_pinbar_df(df, i):
    candle = df.iloc[i]
    o, h, l, c = candle['open'], candle['high'], candle['low'], candle['close']
    body = abs(c - o)
    total_range = h - l
    if total_range == 0 or body > 0.3 * total_range or body == 0: return False
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    return c < o and upper_wick >= body * 2 and lower_wick <= body * 0.5

def build_zone(df, i, zone_type):
    o = df['open'].iloc[i]
    c = df['close'].iloc[i]
    h = df['high'].iloc[i]
    l = df['low'].iloc[i]
    atr = df['atr'].iloc[i]
    max_size = atr * MAX_ZONE_ATR

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

def get_nearest_zones(price, zones, n=2):
    if not zones: return []
    def zone_distance(z):
        if price < z["low"]: return z["low"] - price
        if price > z["high"]: return price - z["high"]
        return 0
    return sorted(zones, key=zone_distance)[:n]

def find_supply_demand_zones(df):
    if len(df) < ATR_PERIOD + 30 or df.empty:
        return [], []

    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(abs(df['high'] - df['close'].shift(1)),
                   abs(df['low'] - df['close'].shift(1)))
    )
    df['atr'] = df['tr'].rolling(window=ATR_PERIOD).mean()

    supply_zones = []
    demand_zones = []
    min_idx = max(ATR_PERIOD + 10, SWING_LEFT)
    max_idx = len(df) - LOOKAHEAD - 1

    for i in range(min_idx, max_idx):
        if pd.isna(df['atr'].iloc[i]): continue
        atr_val = df['atr'].iloc[i]

        if is_bullish_pinbar_df(df, i) or is_bullish_engulfing(df, i):
            zone = build_zone(df, i, "demand")
            if i + LOOKAHEAD < len(df):
                future_high = df['high'].iloc[i+1:i+1+LOOKAHEAD].max()
                move = future_high - zone['high']
                if move >= atr_val * MIN_MOVE_MULT:
                    zone["score"] = 5.0
                    demand_zones.append(zone)

        if is_bearish_pinbar_df(df, i) or is_bearish_engulfing(df, i):
            zone = build_zone(df, i, "supply")
            if i + LOOKAHEAD < len(df):
                future_low = df['low'].iloc[i+1:i+1+LOOKAHEAD].min()
                move = zone['low'] - future_low
                if move >= atr_val * MIN_MOVE_MULT:
                    zone["score"] = 5.0
                    supply_zones.append(zone)

    supply_zones = [z for z in supply_zones if not is_zone_broken(df, z)]
    demand_zones = [z for z in demand_zones if not is_zone_broken(df, z)]

    supply_zones = list({(z["start_bar"], z.get("high"), z.get("low")): z for z in supply_zones}.values())
    demand_zones = list({(z["start_bar"], z.get("high"), z.get("low")): z for z in demand_zones}.values())

    supply_zones = sorted(supply_zones, key=lambda z: z["start_bar"], reverse=True)[:MAX_ZONES]
    demand_zones = sorted(demand_zones, key=lambda z: z["start_bar"], reverse=True)[:MAX_ZONES]

    return supply_zones, demand_zones

def price_in_zone(price, zone):
    return (zone["low"] * (1 - ZONE_TOLERANCE) <= price <= zone["high"] * (1 + ZONE_TOLERANCE))

def check_short_signal(symbol, df_5m, zones):
    if len(df_5m) < 2: return None
    last = df_5m.iloc[-2]
    price = float(last["close"])
    timestamp = int(pd.to_datetime(last["time"]).timestamp())
    for zone in zones:
        if price_in_zone(price, zone):
            key = f"{symbol}_{timestamp}_short"
            if key in sent_signals: return None
            sent_signals[key] = True
            return zone
    return None

def check_long_signal(symbol, df_5m, zones):
    if len(df_5m) < 2: return None
    last = df_5m.iloc[-2]
    price = float(last["close"])
    timestamp = int(pd.to_datetime(last["time"]).timestamp())
    for zone in zones:
        if price_in_zone(price, zone):
            key = f"{symbol}_{timestamp}_long"
            if key in sent_signals: return None
            sent_signals[key] = True
            return zone
    return None

def normalize_time(df):
    if 'time' in df.columns:
        if not np.issubdtype(df['time'].dtype, np.datetime64):
            unit = 'ms' if df['time'].iloc[0] > 1e12 else 's'
            df['time'] = pd.to_datetime(df['time'], unit=unit)
    return df

# ================= ГРАФИК =================
def generate_chart(symbol, klines_or_df, supply_zones, demand_zones, signal_zone=None):
    if isinstance(klines_or_df, pd.DataFrame):
        df_full = klines_or_df.copy()
    else:
        df_full = pd.DataFrame(klines_or_df)

    for col in ["open", "high", "low", "close"]:
        df_full[col] = pd.to_numeric(df_full[col], errors='coerce')

    if 'time' in df_full.columns:
        df_full['datetime'] = pd.to_datetime(df_full['time'])
    elif 'timestamp' in df_full.columns:
        ts = pd.to_numeric(df_full['timestamp'], errors='coerce')
        df_full['datetime'] = pd.to_datetime(ts, unit='ms' if ts.iloc[0] > 1e12 else 's')

    offset = max(0, len(df_full) - CHART_CANDLES)
    df = df_full.iloc[offset:].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(20, 10))
    for i in range(len(df)):
        o, h, l, c = df['open'].iloc[i], df['high'].iloc[i], df['low'].iloc[i], df['close'].iloc[i]
        color = 'green' if c > o else 'red'
        ax.add_patch(patches.Rectangle((i - 0.2, min(o, c)), 0.4, abs(c - o), facecolor=color, edgecolor=color))
        ax.plot([i, i], [l, min(o, c)], color='black', linewidth=1)
        ax.plot([i, i], [max(o, c), h], color='black', linewidth=1)

    for zone in supply_zones:
        rel_start = max(0, zone['start_bar'] - offset)
        if rel_start >= len(df): continue
        ax.add_patch(patches.Rectangle((rel_start, zone['low']), len(df) - rel_start,
                                       zone['high'] - zone['low'], facecolor='red', alpha=0.2, edgecolor='red'))

    for zone in demand_zones:
        rel_start = max(0, zone['start_bar'] - offset)
        if rel_start >= len(df): continue
        ax.add_patch(patches.Rectangle((rel_start, zone['low']), len(df) - rel_start,
                                       zone['high'] - zone['low'], facecolor='blue', alpha=0.2, edgecolor='blue'))

    if signal_zone:
        rel_start = max(0, signal_zone['start_bar'] - offset)
        if rel_start < len(df):
            color = 'red' if signal_zone.get('type') == 'supply' else 'blue'
            ax.add_patch(patches.Rectangle((rel_start, signal_zone['low']), len(df) - rel_start,
                                           signal_zone['high'] - signal_zone['low'],
                                           facecolor='none', edgecolor=color, linewidth=3))

    ax.set_title(f"{symbol} TF:{ZONE_TF}")
    step = max(1, len(df) // 10)
    ax.set_xticks(range(0, len(df), step))
    ax.set_xticklabels(df['datetime'][::step].dt.strftime('%Y-%m-%d %H:%M'), rotation=45, ha='right')
    ax.grid(True)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight')
    buffer.seek(0)

    os.makedirs("charts", exist_ok=True)
    filename = f"charts/{symbol.replace('/', '-')}_{ZONE_TF}_{int(time.time())}.png"
    with open(filename, "wb") as f:
        f.write(buffer.getvalue())
    print(f"✅ График сохранён: {filename}")

    plt.close(fig)
    buffer.seek(0)
    return buffer

# ================= ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =================
sent_signals = {}
used_zones = {}

# ================= ОБРАБОТКА СИМВОЛА =================
async def process_symbol(symbol, semaphore):
    async with semaphore:
        try:
            df_zone = bx.get_klines(symbol, ZONE_TF, ZONE_LIMIT)
            if len(df_zone) < ATR_PERIOD + 20 or df_zone.empty:
                return
            df_zone = normalize_time(df_zone)

            supply_zones, demand_zones = find_supply_demand_zones(df_zone)
            current_price = float(df_zone['close'].iloc[-2])

            nearest_supply = get_nearest_zones(current_price, supply_zones, 2)
            nearest_demand = get_nearest_zones(current_price, demand_zones, 2)

            used = used_zones.get(symbol, set())
            nearest_supply = [z for z in nearest_supply if (z['high'], z['low']) not in used]
            nearest_demand = [z for z in nearest_demand if (z['high'], z['low']) not in used]

            if not nearest_supply and not nearest_demand:
                return

            df_5m = bx.get_klines(symbol, "5m", 15)
            df_5m = normalize_time(df_5m)
            if len(df_5m) < 3 or df_5m.empty:
                return

            short_zone = check_short_signal(symbol, df_5m, nearest_supply)
            if short_zone:
                is_short = True
                zone = short_zone
            else:
                long_zone = check_long_signal(symbol, df_5m, nearest_demand)
                if long_zone:
                    is_short = False
                    zone = long_zone
                else:
                    return

            if symbol not in used_zones:
                used_zones[symbol] = set()
            used_zones[symbol].add((zone['high'], zone['low']))

            chart = generate_chart(symbol, df_zone, supply_zones, demand_zones, signal_zone=zone)

            signal_type = "Short" if is_short else "Long"
            current_price = float(df_5m['close'].iloc[-2])
            stop_price = float(df_5m['high'].iloc[-2]) if is_short else float(df_5m['low'].iloc[-2])

            caption = (
                f"🚨 <b>{symbol} {signal_type} Signal</b>\n"
                f"TF: {ZONE_TF}\n"
                f"Zone: {zone['low']:.6f} — {zone['high']:.6f}\n"
                f"Цена входа: {current_price:.6f}\n"
                f"Stop: {stop_price:.6f}"
            )

            print(caption)
            send_telegram(chart, caption)
            print(f"Signal отправлен: {symbol} {signal_type}")

        except Exception as e:
            print(f"{symbol} error: {e}")

async def main_loop():
    print(f"Мониторим {len(SYMBOLS)} пар: {SYMBOLS}")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] Начинаем сканирование...")
        tasks = [process_symbol(symbol, semaphore) for symbol in SYMBOLS]
        await asyncio.gather(*tasks)
        print(f"[{time.strftime('%H:%M:%S')}] Сканирование завершено\n")
        await asyncio.sleep(SCAN_INTERVAL_SEC)

if __name__ == "__main__":
    print("=== DEBUG ===")
    df_test = bx.get_klines("BTC-USDT", ZONE_TF, 5)
    print(f"Данные получены: {len(df_test)} свечей")
    asyncio.run(main_loop())