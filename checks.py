import math

def check_rr(entry, stop, take, direction='long'):
    if direction == 'long':
        if entry <= stop or take <= entry:
            return False, "Неверные цены для long: стоп ниже входа, тейк выше.", 0, 0
        risk = entry - stop
        reward = take - entry
    else:  # short
        if entry >= stop or take >= entry:
            return False, "Неверные цены для short: стоп выше входа, тейк ниже.", 0, 0
        risk = stop - entry
        reward = entry - take

    rr = reward / risk if risk > 0 else 0
    if rr < 3:
        return False, f"RR {rr:.2f} < 3! Отмена сделки, не прошёл проверку RR.", 0, 0
    return True, f"RR {rr:.2f} OK.", risk, reward


def get_position_size(client, pair, entry, stop, direction='long', risk_dollar=100.0):
    try:
        # Расстояние до стопа в абсолюте
        if direction == 'long':
            stop_distance = entry - stop
        else:
            stop_distance = stop - entry

        if stop_distance <= 0:
            return 0, 0, 0, 0, "Неверное расстояние до стопа"

        stop_pct = stop_distance / entry

        # ТОЧНЫЙ размер позиции
        position_value_usdt = risk_dollar / stop_pct
        quantity = position_value_usdt / entry

        # Получаем реальное плечо биржи
        brackets = client.futures_leverage_bracket(symbol=pair)
        max_leverage = brackets[0]['brackets'][0]['initialLeverage']

        leverage = min(round(position_value_usdt / (risk_dollar * 2)), max_leverage)  # запас

        # Округление quantity по правилам биржи
        info = client.futures_exchange_info()
        for s in info['symbols']:
            if s['symbol'] == pair:
                qty_precision = int(s['quantityPrecision'])
                quantity = round(quantity, qty_precision)
                break

        real_risk_pct = (risk_dollar / (client.futures_account_balance()[0]['balance'] or 1)) * 100

        return quantity, leverage, 0, real_risk_pct, "OK"

    except Exception as e:
        return 0, 0, 0, 0, f"Ошибка расчёта размера: {e}"