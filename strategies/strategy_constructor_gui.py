import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(page_title="Freqtrade Strategy Constructor", layout="wide")
st.title("🚀 Freqtrade Конструктор стратегий")
st.markdown("**Выбери стратегии, настрой параметры и сохрани.** JSON автоматически подхватывается стратегией.")

# Путь к JSON (лежит рядом с GUI и стратегией)
json_path = os.path.join(os.path.dirname(__file__), "strategy_settings.json")

# Загрузка текущих настроек
if os.path.exists(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            current = json.load(f)
    except:
        current = {}
else:
    current = {}

# ====================== ОБЩИЕ НАСТРОЙКИ ======================
st.header("1. Общие настройки")

col1, col2, col3 = st.columns(3)
with col1:
    min_buy_votes = st.slider("Минимум голосов для входа (Buy)", 
                              min_value=1, max_value=6, 
                              value=current.get("min_buy_votes", 3))

with col2:
    min_sell_votes = st.slider("Минимум голосов для выхода (Sell)", 
                               min_value=1, max_value=6, 
                               value=current.get("min_sell_votes", 3))

with col3:
    timeframe = st.selectbox("Таймфрейм", 
                             ["1m", "5m", "15m", "30m", "1h", "4h", "1d"], 
                             index=["1m","5m","15m","30m","1h","4h","1d"].index(current.get("timeframe", "5m")))

# ====================== СТРАТЕГИИ ======================
st.header("2. Выбор и настройка стратегий")

strategies_config = {
    "RSI": {
        "use_key": "use_rsi",
        "default_use": True,
        "params": {
            "rsi_buy": ("Уровень покупки (Buy)", 10, 45, current.get("rsi_buy", 30)),
            "rsi_sell": ("Уровень продажи (Sell)", 55, 90, current.get("rsi_sell", 70))
        }
    },
    "MACD": {
        "use_key": "use_macd",
        "default_use": True,
        "params": {
            "macd_fast": ("Fast период", 8, 20, current.get("macd_fast", 12)),
            "macd_slow": ("Slow период", 21, 35, current.get("macd_slow", 26)),
            "macd_signal": ("Signal период", 5, 15, current.get("macd_signal", 9))
        }
    },
    "EMA Crossover": {
        "use_key": "use_ema",
        "default_use": True,
        "params": {
            "ema_fast": ("Быстрая EMA", 5, 20, current.get("ema_fast", 8)),
            "ema_slow": ("Медленная EMA", 15, 40, current.get("ema_slow", 21))
        }
    },
    "Bollinger Bands": {
        "use_key": "use_bb",
        "default_use": True,
        "params": {
            "bb_period": ("Период BB", 10, 40, current.get("bb_period", 20)),
            "bb_std": ("StdDev (ширина)", 1.0, 3.0, current.get("bb_std", 2.0), 0.1)
        }
    },
    "ADX + DI": {
        "use_key": "use_adx",
        "default_use": True,
        "params": {
            "adx_period": ("Период ADX", 10, 30, current.get("adx_period", 14)),
            "adx_threshold": ("Порог ADX", 15, 40, current.get("adx_threshold", 25))
        }
    },
    "Stochastic": {
        "use_key": "use_stoch",
        "default_use": True,
        "params": {
            "stoch_k": ("%K период", 5, 21, current.get("stoch_k", 14)),
            "stoch_d": ("%D период", 3, 10, current.get("stoch_d", 3)),
            "stoch_buy": ("Уровень покупки", 5, 35, current.get("stoch_buy", 20))
        }
    }
}

settings = {
    "min_buy_votes": min_buy_votes,
    "min_sell_votes": min_sell_votes,
    "timeframe": timeframe
}

for name, cfg in strategies_config.items():
    with st.expander(f"🔹 Стратегия: {name}", expanded=True):
        use_this = st.checkbox(f"Включить {name}", 
                               value=current.get(cfg["use_key"], cfg["default_use"]))
        settings[cfg["use_key"]] = use_this

        if use_this:
            for param_key, param_info in cfg["params"].items():
                if len(param_info) == 4:          # int slider
                    label, minv, maxv, default = param_info
                    settings[param_key] = st.slider(label, minv, maxv, default)
                else:                             # decimal slider (bb_std)
                    label, minv, maxv, default, step = param_info
                    settings[param_key] = st.slider(label, minv, maxv, default, step)

# ====================== КНОПКИ ======================
col_save, col_clear, col_info = st.columns([2, 1, 2])

if col_save.button("💾 СОХРАНИТЬ НАСТРОЙКИ В JSON", type="primary", use_container_width=True):
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)
    
    st.success(f"✅ Настройки успешно сохранены в **{json_path}**")
    st.balloons()
    st.info(f"Время сохранения: {datetime.now().strftime('%H:%M:%S')}")

if col_clear.button("🗑 Очистить и сбросить к значениям по умолчанию"):
    if os.path.exists(json_path):
        os.remove(json_path)
    st.success("JSON удалён. Перезагрузи страницу для сброса.")
    st.rerun()

# ====================== КОМАНДЫ ДЛЯ ЗАПУСКА ======================
st.header("3. Команды для запуска")

cmd_backtest = f"""
freqtrade backtesting \\
  --strategy SampleStrategy \\
  --config config.json \\
  --timeframe {timeframe} \\
  --timerange 20230101-20260325
"""

st.subheader("Бэктест")
st.code(cmd_backtest, language="bash")

st.subheader("Dry-run (тест в реальном времени)")
st.code(f"freqtrade trade --strategy SampleStrategy --config config.json --dry-run", language="bash")

st.caption("После сохранения JSON просто запускай команду выше — стратегия автоматически подгрузит все твои настройки.")

# Подвал
st.divider()
st.caption("Freqtrade Strategy Constructor • Работает через strategy_settings.json • Полностью динамический")