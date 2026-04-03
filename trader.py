import os
from datetime import datetime
from dotenv import load_dotenv
from binance.client import Client

# Новые импорты из database
from database import init_journal, insert_open_trade, close_trade, get_open_positions

from checks import check_rr, get_position_size

load_dotenv(dotenv_path='config.env')


class Trader:
    def __init__(self):
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        if not api_key or not api_secret:
            raise ValueError("API ключи не найдены в config.env!")
        
        self.client = Client(api_key, api_secret)

        # Инициализируем Excel-журнал при старте
        init_journal()

    def open_trade(
        self,
        pair: str,
        entry: float,
        stop: float,
        take: float,
        reason_entry: str,
        fear_greed: int,
        direction: str = 'long',
        leverage: int = None,
        risk_dollar: float = None
    ):
        ok, msg, risk, reward = check_rr(entry, stop, take, direction)
        if not ok:
            return False, msg

        if leverage is None or leverage < 1:
            return False, "Плечо не передано или некорректно"

        if risk_dollar is None or risk_dollar <= 0:
            return False, "Риск в $ не передан"

        # Расчёт размера позиции
        quantity, calc_leverage, margin_pct, real_risk_pct, msg = get_position_size(
            self.client, pair, entry, stop, direction, risk_dollar=risk_dollar
        )
        if quantity <= 0:
            return False, msg

        leverage_to_use = leverage
        rr_ratio = reward / risk if risk > 0 else 0
        potential_profit = reward * quantity
        potential_loss = risk * quantity

        try:
            # Устанавливаем плечо
            self.client.futures_change_leverage(symbol=pair, leverage=leverage_to_use)

            position_side = 'LONG' if direction == 'long' else 'SHORT'
            open_side = 'BUY' if direction == 'long' else 'SELL'
            close_side = 'SELL' if direction == 'long' else 'BUY'

            # 1. Лимитный ордер на вход (обычный)
            entry_order = self.client.futures_create_order(
                symbol=pair,
                side=open_side,
                type='LIMIT',
                price=entry,
                quantity=quantity,
                timeInForce='GTC',
                positionSide=position_side
            )

            # 2. Stop-Loss через Algo Order (используем triggerPrice!)
            self.client.futures_create_algo_order(
                algoType='CONDITIONAL',
                symbol=pair,
                side=close_side,
                type='STOP_MARKET',
                quantity=quantity,
                triggerPrice=stop,           # ← Вот главный параметр
                timeInForce='GTC',
                positionSide=position_side,
                workingType='CONTRACT_PRICE' # или 'MARK_PRICE' по желанию
            )

            # 3. Take-Profit через Algo Order
            self.client.futures_create_algo_order(
                algoType='CONDITIONAL',
                symbol=pair,
                side=close_side,
                type='TAKE_PROFIT_MARKET',
                quantity=quantity,
                triggerPrice=take,           # ← Вот главный параметр
                timeInForce='GTC',
                positionSide=position_side,
                workingType='CONTRACT_PRICE'
            )

            # Данные для Excel
            trade_data = {
                'pair': pair,
                'direction': direction,
                'entry_price': entry,
                'stop_loss': stop,
                'take_profit': take,
                'leverage': leverage_to_use,
                'rr_ratio': round(rr_ratio, 4),
                'potential_profit': round(potential_profit, 2),
                'potential_loss': round(potential_loss, 2),
                'reason_entry': reason_entry,
                'fear_greed': fear_greed,
                'profit_shans': 0,
                'tradingview_link': None,
            }

            trade_id = insert_open_trade(trade_data)

            return True, (
                f"✅ Ордер успешно отправлен ({direction.upper()}) ID:{trade_id}\n"
                f"Плечо: {leverage_to_use}x | Кол-во: {quantity:.6f}\n"
                f"Stop-Loss и Take-Profit созданы (Algo Order)"
            )

        except Exception as e:
            error_str = str(e)
            if "position side" in error_str.lower():
                error_str += "\n\nРекомендация: Переключи Position Mode → One-way Mode в настройках Binance Futures."
            return False, f"❌ Ошибка открытия позиции: {error_str}"
    def close_trade(self, pair: str, reason_close: str):
        """Закрытие позиции по рынку + обновление журнала"""
        try:
            position_info = self.client.futures_position_information(symbol=pair)[0]
            amount = float(position_info['positionAmt'])
            if amount == 0:
                return False, "Нет открытой позиции по этой паре."

            close_side = 'SELL' if amount > 0 else 'BUY'
            quantity = abs(amount)

            # Закрываем по рынку
            close_order = self.client.futures_create_order(
                symbol=pair,
                side=close_side,
                type='MARKET',
                quantity=quantity
            )

            # Получаем реализованный PnL из последней сделки
            trades = self.client.futures_account_trade_list(symbol=pair, limit=5)
            pnl = 0.0
            if trades:
                # Берём самую свежую реализованную прибыль
                pnl = float(trades[0].get('realizedPnl', 0))

            # Обновляем Excel
            success = close_trade(trade_id=None, pnl=pnl, reason_close=reason_close, pair=pair)
            # Если close_trade принимает pair вместо id — нужно будет подправить в database.py

            return True, f"✅ Позиция закрыта по рынку. PnL: {pnl:.2f} USDT | Причина: {reason_close}"

        except Exception as e:
            return False, f"❌ Ошибка закрытия позиции: {str(e)}"

    def get_open_positions(self):
        """Возвращает список открытых позиций для меню закрытия"""
        try:
            positions = self.client.futures_position_information()
            open_pos = []
            for pos in positions:
                amt = float(pos['positionAmt'])
                if amt != 0:
                    symbol = pos['symbol']
                    direction = "Long" if amt > 0 else "Short"
                    open_pos.append(f"{symbol} ({direction})")
            return open_pos
        except Exception as e:
            print(f"Ошибка получения открытых позиций: {e}")
            return []

    def monitor_trades(self):
        """Мониторинг активных позиций"""
        try:
            positions = self.client.futures_position_information()
            info = ""
            for pos in positions:
                amt = float(pos['positionAmt'])
                if amt != 0:
                    symbol = pos['symbol']
                    direction = "Long" if amt > 0 else "Short"
                    pnl = float(pos['unRealizedProfit'])
                    entry = float(pos['entryPrice'])
                    info += f"{symbol} ({direction}) | PnL: {pnl:.2f} | Вход: {entry}\n"
            return info or "Нет активных позиций."
        except Exception as e:
            return f"Ошибка мониторинга: {e}"
        
        
    def get_usdt_balance(self):
        try:
            balance_info = self.client.futures_account_balance()
            for b in balance_info:
                if b['asset'] == 'USDT':
                    return float(b['balance'])
            return 0.0
        except Exception as e:
            print(f"Ошибка баланса: {e}")
            return 0.0

    def check_closed_trades(self):
        """Проверка закрытых позиций на бирже и обновление журнала"""
        print("Проверка закрытых сделок на Binance...")
        # Можно доработать позже, если нужно автоматически находить закрытые сделки
        pass