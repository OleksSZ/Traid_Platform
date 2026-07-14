import os
from dotenv import load_dotenv
from binance.client import Client

from database import ExcelTradeJournal
from parcer import BinanceAccount
from checks import check_rr, get_position_size

load_dotenv(dotenv_path=r'C:\Users\User\Desktop\Traid_Platform\config.env')


class Trader:
    def __init__(self):
        # Binance клієнт через BinanceAccount (новий клас)
        self._account = BinanceAccount()

        # Журнал через ExcelTradeJournal (новий клас)
        self._journal = ExcelTradeJournal()

        # Прямий клієнт для ордерів
        api_key    = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        if not api_key or not api_secret:
            raise ValueError("API ключи не знайдено в config.env!")
        self.client = Client(api_key, api_secret)

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
        risk_dollar: float = None,
        risk_percent: float = None
    ):
        ok, msg, risk, reward = check_rr(entry, stop, take, direction)
        if not ok:
            return False, msg

        if leverage is None or leverage < 1:
            return False, "Плечо не передано"

        if risk_dollar is None or risk_dollar <= 0:
            return False, "Риск в долларах не передан"

        quantity, _, _, real_risk_pct, msg = get_position_size(
            self.client, pair, entry, stop, direction, risk_dollar=risk_dollar
        )
        if quantity <= 0:
            return False, msg

        leverage_to_use = leverage
        rr_ratio = reward / risk if risk > 0 else 0

        try:
            self.client.futures_change_leverage(
                symbol=pair, leverage=leverage_to_use)

            position_side = 'LONG' if direction == 'long' else 'SHORT'
            open_side     = 'BUY'  if direction == 'long' else 'SELL'
            close_side    = 'SELL' if direction == 'long' else 'BUY'

            # 1. Лімітний ордер на вхід
            self.client.futures_create_order(
                symbol=pair, side=open_side, type='LIMIT',
                price=entry, quantity=quantity,
                timeInForce='GTC', positionSide=position_side
            )

            # 2. Stop-Loss
            self.client.futures_create_order(
                symbol=pair, side=close_side, type='STOP_MARKET',
                stopPrice=stop, quantity=quantity,
                positionSide=position_side, workingType='CONTRACT_PRICE'
            )

            # 3. Take-Profit
            self.client.futures_create_order(
                symbol=pair, side=close_side, type='TAKE_PROFIT_MARKET',
                stopPrice=take, quantity=quantity,
                positionSide=position_side, workingType='CONTRACT_PRICE'
            )

            # 4. Зберігаємо в журнал через ExcelTradeJournal
            trade_data = {
                'pair':             pair,
                'direction':        direction.upper(),
                'entry_price':      entry,
                'stop_loss':        stop,
                'take_profit':      take,
                'leverage':         leverage_to_use,
                'rr_ratio':         round(rr_ratio, 4),
                'potential_profit': round(reward * quantity, 2),
                'potential_loss':   round(risk   * quantity, 2),
                'reason_entry':     reason_entry,
                'fear_greed':       fear_greed,
                'profit_shans':     65,
                'tradingview_link': None,
                'risk_dollar':      round(risk_dollar, 2),
                'risk_percent':     round(risk_percent, 2) if risk_percent else None,
                'real_risk_pct':    round(real_risk_pct, 4),
            }

            trade_id = self._journal.insert_open_trade(trade_data)

            return True, (
                f"✅ Позиція відкрита ({direction.upper()}) | ID: {trade_id}\n"
                f"Entry: {entry:.4f} | SL: {stop:.4f} | TP: {take:.4f}\n"
                f"Плечо: {leverage_to_use}x | Qty: {quantity:.6f}\n"
                f"Ризик: ${risk_dollar:.2f}"
            )

        except Exception as e:
            error_str = str(e)
            if "position side" in error_str.lower():
                error_str += "\n\nПереключи Position Mode → One-way Mode"
            elif "-2021" in error_str:
                error_str += "\n\nОрдер одразу тригериться. Перевір ціни SL/TP."
            return False, f"❌ Помилка відкриття:\n{error_str}"

    def close_trade(self, pair: str, reason_close: str):
        try:
            symbol_clean = pair.replace('/', '').replace('-', '').upper()

            all_positions = self.client.futures_position_information()
            position = None

            for pos in all_positions:
                if pos['symbol'] == symbol_clean:
                    if float(pos.get('positionAmt', 0)) != 0:
                        position = pos
                        break

            if not position:
                open_symbols = [
                    p['symbol'] for p in all_positions
                    if float(p.get('positionAmt', 0)) != 0
                ]
                return False, f"Позиція {pair} не знайдена.\nВідкриті: {open_symbols}"

            amt       = float(position['positionAmt'])
            symbol    = position['symbol']
            pos_side  = position.get('positionSide', 'BOTH')
            close_side = 'SELL' if amt > 0 else 'BUY'
            quantity  = abs(amt)

            self.client.futures_create_order(
                symbol=symbol, side=close_side,
                type='MARKET', quantity=quantity,
                positionSide=pos_side
            )

            return True, (
                f"✅ Позиція {symbol} закрита по ринку.\n"
                f"Кількість: {quantity} | Причина: {reason_close}"
            )

        except Exception as e:
            return False, f"❌ Помилка закриття {pair}: {str(e)}"

    def get_open_positions(self):
        try:
            positions = self.client.futures_position_information()
            return [
                f"{p['symbol']} ({'LONG' if float(p['positionAmt']) > 0 else 'SHORT'})"
                for p in positions
                if float(p.get('positionAmt', 0)) != 0
            ]
        except Exception as e:
            print(f"Помилка отримання позицій: {e}")
            return []

    def monitor_trades(self):
        try:
            positions = self.client.futures_position_information()
            lines = []
            for pos in positions:
                amt = float(pos['positionAmt'])
                if amt != 0:
                    direction = "Long" if amt > 0 else "Short"
                    pnl   = float(pos['unRealizedProfit'])
                    entry = float(pos['entryPrice'])
                    lines.append(
                        f"{pos['symbol']} ({direction}) | "
                        f"PnL: {pnl:.2f} | Вхід: {entry:.4f}"
                    )
            return "\n".join(lines) if lines else "Немає активних позицій."
        except Exception as e:
            return f"Помилка моніторингу: {e}"