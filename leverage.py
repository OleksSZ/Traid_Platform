from parcer import get_usdt_balance


def calculate_optimal_leverage(entry, stop, risk_usd, risk_percent):
    """
    balance (B) - депозит
    percent (p) - % от баланса на сделку
    entry - цена входа
    stop - цена стопа
    desired_loss (L) - желаемый убыток ($)
    """
    balance_data = get_usdt_balance()

    if not balance_data:
        raise Exception("Не удалось получить баланс")

    balance = balance_data["available"]

    positionSize = balance * (risk_percent / 100)
    qty = positionSize / entry
    riskPerUnit = abs(entry - stop)
    actualLoss = qty * riskPerUnit

    leverage = risk_usd / actualLoss

    return  round(leverage)
