import sys
import os
import subprocess
import streamlit as st
import pandas as pd
import json
import psutil
from datetime import datetime

# ====================== TELEGRAM НАСТРОЙКИ ======================
TELEGRAM_TOKEN = "8736878634:AAFsQyL8z7hu0gq3n6Yrq43d_fsKHFMcfac"
TELEGRAM_CHAT_ID = "1420484889"

def send_telegram(message: str):
    """Простая отправка сообщения в Telegram"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)
        print(f"[TG] Отправлено: {message[:100]}...")
    except Exception as e:
        print(f"[TG ERROR] {e}")

# ====================== ИНИЦИАЛИЗАЦИЯ ======================
st.set_page_config(page_title="Freqtrade Interface", layout="wide")
st.title("🚀 Freqtrade Interface — Главное управление")
st.markdown("---")

if 'freqtrade_running' not in st.session_state:
    st.session_state.freqtrade_running = False

VENV_PYTHON = r"D:\Trading\freqtrade\.venv\Scripts\python.exe"

# ====================== ВКЛАДКИ ======================
tab_strategy, tab_data, tab_backtest, tab_live_signals = st.tabs([
    "📊 Настройка Стратегий",
    "📥 Данные Binance",
    "▶️ Запуск Бэктеста",
    "📡 Реальная торговля (сигналы в TG)"
])

# ====================== ВКЛАДКА 1: НАСТРОЙКА СТРАТЕГИЙ ======================
with tab_strategy:
    st.header("Настройка комбинированной стратегии")
    st.info("Все изменения сохраняются автоматически в `user_data/strategies/strategy_settings.json`")

    json_path = "user_data/strategies/strategy_settings.json"

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            current = json.load(f)
    else:
        current = {}

    st.subheader("Общие настройки голосования")
    col1, col2 = st.columns(2)
    with col1:
        min_buy_votes = st.slider("Минимум голосов для входа (Buy)", 1, 6, current.get("min_buy_votes", 3))
    with col2:
        min_sell_votes = st.slider("Минимум голосов для выхода (Sell)", 1, 6, current.get("min_sell_votes", 3))

    st.subheader("Стратегии и их параметры")

    strategies = {
        "RSI": {"use": "use_rsi", "buy": "rsi_buy", "sell": "rsi_sell"},
        "MACD": {"use": "use_macd", "fast": "macd_fast", "slow": "macd_slow", "signal": "macd_signal"},
        "EMA Crossover": {"use": "use_ema", "fast": "ema_fast", "slow": "ema_slow"},
        "Bollinger Bands": {"use": "use_bb", "period": "bb_period", "std": "bb_std"},
        "ADX + DI": {"use": "use_adx", "period": "adx_period", "threshold": "adx_threshold"},
        "Stochastic": {"use": "use_stoch", "k": "stoch_k", "d": "stoch_d", "buy": "stoch_buy"},
    }

    settings = {"min_buy_votes": min_buy_votes, "min_sell_votes": min_sell_votes}

    for name, keys in strategies.items():
        with st.expander(f"🔹 {name}", expanded=True):
            use = st.checkbox(f"Включить {name}", value=current.get(keys["use"], True))
            settings[keys["use"]] = use

            if use:
                if name == "RSI":
                    settings[keys["buy"]] = st.slider(f"{name} Buy уровень", 10, 50, current.get(keys["buy"], 30))
                    settings[keys["sell"]] = st.slider(f"{name} Sell уровень", 50, 90, current.get(keys["sell"], 70))
                elif name == "MACD":
                    settings[keys["fast"]] = st.slider("MACD Fast", 8, 20, current.get(keys["fast"], 12))
                    settings[keys["slow"]] = st.slider("MACD Slow", 21, 35, current.get(keys["slow"], 26))
                    settings[keys["signal"]] = st.slider("MACD Signal", 5, 15, current.get(keys["signal"], 9))
                elif name == "EMA Crossover":
                    settings[keys["fast"]] = st.slider("EMA Fast", 5, 20, current.get(keys["fast"], 8))
                    settings[keys["slow"]] = st.slider("EMA Slow", 15, 40, current.get(keys["slow"], 21))
                elif name == "Bollinger Bands":
                    settings[keys["period"]] = st.slider("BB Период", 10, 40, current.get(keys["period"], 20))
                    settings[keys["std"]] = st.slider("BB StdDev", 1.0, 3.0, current.get(keys["std"], 2.0), 0.1)
                elif name == "ADX + DI":
                    settings[keys["period"]] = st.slider("ADX Период", 10, 30, current.get(keys["period"], 14))
                    settings[keys["threshold"]] = st.slider("ADX Порог", 15, 40, current.get(keys["threshold"], 25))
                elif name == "Stochastic":
                    settings[keys["k"]] = st.slider("Stoch %K", 5, 21, current.get(keys["k"], 14))
                    settings[keys["d"]] = st.slider("Stoch %D", 3, 10, current.get(keys["d"], 3))
                    settings[keys["buy"]] = st.slider("Stoch Buy уровень", 5, 35, current.get(keys["buy"], 20))

    if st.button("💾 Сохранить настройки стратегии", type="primary"):
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        st.success("✅ Настройки успешно сохранены!")
        st.balloons()

# ====================== ВКЛАДКА 2: ДАННЫЕ BINANCE ======================
with tab_data:
    st.header("📥 Управление данными Binance")

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Скачивание свечей")
        pairs_input = st.text_input("Пары (через запятую)", "BTC/USDT")
        timeframe_input = st.selectbox("Таймфрейм", ["1m", "5m", "15m", "30m", "1h", "4h", "1d"], index=4)
        days_input = st.slider("Сколько последних дней скачать", 30, 730, 365)

        if st.button("📥 Скачать данные с Binance", type="primary"):
            with st.spinner("Скачивание..."):
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"

                cmd = [
                    VENV_PYTHON,
                    "-m", "freqtrade",
                    "download-data",
                    "--pairs", pairs_input,
                    "--timeframe", timeframe_input,
                    "--days", str(days_input),
                    "--trading-mode", "spot",
                    "--exchange", "binance",
                    "--datadir", "user_data/data"
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd(), env=env)

                if result.returncode == 0:
                    st.success("✅ Данные скачаны!")
                    st.code(result.stdout[-1500:])
                else:
                    st.error("❌ Ошибка скачивания")
                    st.code(result.stderr[-2000:] or result.stdout)

# ====================== ВКЛАДКА 3: ЗАПУСК БЭКТЕСТА ======================
with tab_backtest:
    st.header("▶️ Запуск бэктеста")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        test_pair = st.text_input("Пара для тестирования", "BTC/USDT")
    with col_b:
        test_tf = st.selectbox("Таймфрейм", ["1h", "4h", "1d", "15m"], index=0)

    if st.button("🚀 ЗАПУСТИТЬ БЭКТЕСТ СЕЙЧАС", type="primary", use_container_width=True):
        
        with st.spinner("Запуск бэктеста..."):
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            cmd = [
                VENV_PYTHON,
                "-m", "freqtrade",
                "backtesting",
                "--strategy", "CombinedConstructorStrategy",
                "--config", "user_data/config.json",
                "--timeframe", test_tf,
                "--pairs", test_pair,
                "--datadir", "user_data/data",
                "--export", "trades",
                "--cache", "none"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd(), env=env)

            if result.returncode == 0:
                st.success("✅ Бэктест успешно завершён!")

                results_dir = os.path.join(os.getcwd(), "user_data", "backtest_results")
                
                if os.path.exists(results_dir):
                    zip_files = [f for f in os.listdir(results_dir) if f.endswith('.zip')]
                    
                    if zip_files:
                        latest_zip = max([os.path.join(results_dir, f) for f in zip_files], key=os.path.getctime)
                        
                        try:
                            import zipfile
                            
                            with zipfile.ZipFile(latest_zip, 'r') as z:
                                json_name = next((name for name in z.namelist() if name.endswith('.json')), None)
                                
                                if json_name:
                                    with z.open(json_name) as f:
                                        data = json.load(f)
                                    
                                    strategy_data = data.get("strategy", {}).get("CombinedConstructorStrategy", {})

                                    trades = strategy_data.get("trades", [])
                                    if trades:
                                        df = pd.DataFrame(trades)
                                        excel_name = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                                        excel_path = os.path.join(results_dir, excel_name)
                                        df.to_excel(excel_path, index=False)
                                        
                                        st.subheader("📊 Детальная таблица сделок")
                                        st.dataframe(df.head(20))
                                        
                                        st.download_button(
                                            "📥 Скачать Excel со всеми сделками",
                                            data=open(excel_path, "rb").read(),
                                            file_name=excel_name,
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                        )
                                    else:
                                        st.warning("Сделок не найдено")

                                    st.subheader("📈 Общая статистика бэктеста")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("Всего сделок", len(trades))
                                        st.metric("Прибыль всего (USDT)", f"{strategy_data.get('profit_total_abs', 0):.2f}")
                                        st.metric("Прибыль %", f"{strategy_data.get('profit_total_pct', 0):.2f}%")
                                        st.metric("Win Rate", f"{strategy_data.get('winrate', 0):.1f}%")
                                    with col2:
                                        st.metric("Макс. просадка (USDT)", f"{strategy_data.get('max_drawdown_abs', 0):.2f}")
                                        st.metric("Макс. просадка %", f"{strategy_data.get('max_relative_drawdown', 0):.2f}%")
                                        st.metric("Средняя длительность сделки", strategy_data.get('holding_avg', '0:00:00'))
                                        st.metric("Лучшая сделка %", f"{max([t.get('profit_ratio', 0) for t in trades] or [0]) * 100:.2f}%")

                        except Exception as e:
                            st.error(f"Ошибка обработки файла: {e}")
                    else:
                        st.warning("ZIP-файл не найден")
                else:
                    st.error("Папка backtest_results не найдена")
            else:
                st.error("❌ Ошибка при запуске бэктеста")
                st.code(result.stderr or result.stdout)

# ====================== ВКЛАДКА 4: РЕАЛЬНАЯ ТОРГОВЛЯ ======================
with tab_live_signals:
    st.header("📡 Реальная торговля — ТОЛЬКО СИГНАЛЫ В TELEGRAM")
    st.success("**Dry-run режим**: сделки НЕ открываются автоматически")

    col1, col2 = st.columns([3, 2])
    with col1:
        pairs_input = st.text_input(
            "Пары для мониторинга",
            "BTC/USDT ETH/USDT SOL/USDT XRP/USDT ADA/USDT"
        )
        pairs = [p.strip().replace(" ", "/") for p in pairs_input.replace(",", " ").split() if p.strip()]

    with col2:
        tf = st.selectbox("Таймфрейм", ["1m", "5m", "15m", "30m", "1h", "4h"], index=2)

    col_start, col_stop = st.columns(2)

    with col_start:
        if st.button("🚀 Запустить сигнальный бот", type="primary", use_container_width=True):
            if not pairs:
                st.error("Укажите хотя бы одну пару!")
            else:
                pair_str = " ".join(pairs)
                cmd = [
                    VENV_PYTHON, "-m", "freqtrade", "trade",
                    "--strategy", "CombinedConstructorStrategy",
                    "--config", "user_data/config.json",
                    "--dry-run",
                    "--pairs", pair_str,
                    "--timeframe", tf,
                    "--logfile", "user_data/logs/signals.log",
                    "--verbosity", "info"
                ]
                try:
                    process = subprocess.Popen(cmd, cwd=os.getcwd(), creationflags=subprocess.CREATE_NEW_CONSOLE)
                    st.session_state.freqtrade_running = True
                    
                    send_telegram(f"🚀 <b>Сигнальный бот запущен</b>\nПары: {len(pairs)}\nТФ: {tf}")
                    
                    st.success(f"✅ Бот запущен! | Пар: {len(pairs)} | TF: {tf}")
                except Exception as e:
                    st.error(f"Ошибка запуска: {e}")

    with col_stop:
        if st.button("⛔ Остановить сигнальный бот", type="secondary", use_container_width=True):
            stopped = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and 'freqtrade' in ' '.join(cmdline).lower() and 'trade' in ' '.join(cmdline).lower():
                        proc.kill()
                        stopped = True
                except:
                    pass
            if stopped:
                st.session_state.freqtrade_running = False
                send_telegram("⛔ <b>Сигнальный бот остановлен</b>")
                st.success("✅ Бот остановлен")
            else:
                st.warning("Активных процессов Freqtrade не найдено")

    if st.session_state.freqtrade_running:
        st.success("🟢 **Сигнальный бот работает** — проверяет рынок")
    else:
        st.info("🔴 Сигнальный бот остановлен")

    st.caption("💡 Бот работает в dry-run режиме. Деньги не тратятся.")

# ====================== БОКОВАЯ ПАНЕЛЬ ======================
st.sidebar.markdown("---")
st.sidebar.header("📲 Telegram")
st.sidebar.info("Сигналы от Freqtrade приходят в Telegram (если настроено в config.json)")

st.sidebar.caption("Freqtrade + Streamlit")