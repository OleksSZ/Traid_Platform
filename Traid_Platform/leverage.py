from parcer import BinanceAccount


class RiskManager:
    """
    balance (B) - депозит
    percent (p) - % от баланса на сделку
    entry - цена входа
    stop - цена стопа
    desired_loss (L) - желаемый убыток ($)
    """

    def __init__(self, account: BinanceAccount):
        self._account = account
        self._balance = None

    def _load_balance(self):
        data = self._account.get_usdt_balance()
        if not data:
            raise Exception("Не удалось получить баланс")
        self._balance = float(data["available"])

    def _calculate_position_size(self, risk_percent):
        return self._balance * (risk_percent / 100.0)

    def _calculate_qty(self, position_size, risk_per_unit, entry, leverage):
        notional = position_size * leverage
        return notional / entry

    def _calculate_risk_per_unit(self, entry, stop):
        return abs(entry - stop)

    def _calculate_actual_loss(self, qty, risk_per_unit):
        return qty * risk_per_unit

    def calculate_leverage(self, entry, stop, risk_usd, risk_percent):
        """
        Возвращает целое плечо (rounded) по формуле:
        leverage = (risk_usd * entry) / (position_size * risk_per_unit)

        Гарантирует минимальное плечо 1 и проверяет деление на ноль.
        """
        self._load_balance()

        # сколько маржи выделяем
        position_size = self._calculate_position_size(risk_percent)

        if position_size <= 0:
            raise Exception("Ошибка: position_size <= 0")

        # риск на 1 монету
        risk_per_unit = self._calculate_risk_per_unit(entry, stop)
        if risk_per_unit == 0:
            raise Exception("Ошибка: entry = stop (risk_per_unit == 0)")

        if risk_usd <= 0:
            raise Exception("Ошибка: risk_usd должен быть > 0")

        # формула для плеча
        leverage = (risk_usd * entry) / (position_size * risk_per_unit)

        # нижняя граница
        if leverage < 1:
            leverage = 1.0

 
        return int(round(leverage))
