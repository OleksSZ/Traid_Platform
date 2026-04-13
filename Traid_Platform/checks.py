import math

def check_rr(entry, stop, take, direction='long'):
    """Проверка RR Ratio"""
    try:
        entry = float(entry)
        stop = float(stop)
        take = float(take)
    except (ValueError, TypeError):
        return False, "Ошибка преобразования цен в число", 0, 0

    if direction.lower() == 'long':
        if entry <= stop or take <= entry:
            return False, "Неверные цены для Long: стоп должен быть ниже входа, тейк — выше.", 0, 0
        risk = entry - stop
        reward = take - entry
    else:  # short
        if entry >= stop or take >= entry:
            return False, "Неверные цены для Short: стоп должен быть выше входа, тейк — ниже.", 0, 0
        risk = stop - entry
        reward = entry - take

    rr = reward / risk if risk > 0 else 0
    if rr < 3.0:
        return False, f"RR {rr:.2f} < 3! Сделка отменена.", 0, 0

    return True, f"RR {rr:.2f} OK.", risk, reward


def get_position_size(client, pair, entry, stop, direction='long', risk_dollar=100.0, risk_percent=None):
    """
    Расчёт размера позиции + плеча
    """
    try:
        # Приводим всё к float
        entry = float(entry)
        stop = float(stop)
        risk_dollar = float(risk_dollar)

        # Расстояние до стопа
        if direction.lower() == 'long':
            stop_distance = entry - stop
        else:
            stop_distance = stop - entry

        if stop_distance <= 0:
            return 0, 0, 0, 0, "Неверное расстояние до стопа (stop_distance <= 0)"

        stop_pct = stop_distance / entry

        # Основной расчёт размера позиции
        position_value_usdt = risk_dollar / stop_pct
        quantity = position_value_usdt / entry

        # === Получаем максимальное плечо с биржи ===
        brackets = client.futures_leverage_bracket(symbol=pair)
        max_leverage = int(brackets[0]['brackets'][0]['initialLeverage'])

        # Рассчитываем теоретическое плечо
        theoretical_leverage = position_value_usdt / risk_dollar

        # Округляем до целого и выбираем ближайшее валидное плечо
        leverage = round(theoretical_leverage)
        
        # Валидные значения плеча Binance (можно расширить)
        valid_leverages = [1, 2, 3, 5, 7, 10, 12, 15, 20, 25, 30, 40, 50, 60, 75, 100, 125]
        leverage = min(valid_leverages, key=lambda x: abs(x - leverage))
        
        # Не превышаем максимум биржи
        leverage = min(leverage, max_leverage)

        # Округление quantity по правилам биржи
        info = client.futures_exchange_info()
        for s in info['symbols']:
            if s['symbol'] == pair:
                qty_precision = int(s['quantityPrecision'])
                quantity = round(quantity, qty_precision)
                break
        else:
            quantity = round(quantity, 3)  # fallback

        # Реальный процент риска от баланса
        try:
            balance_info = client.futures_account_balance()
            total_balance = float(balance_info[0]['balance']) if balance_info else 1000.0
            real_risk_pct = (risk_dollar / total_balance) * 100 if total_balance > 0 else 0.0
        except:
            real_risk_pct = 0.0

        return quantity, leverage, stop_pct * 100, real_risk_pct, "OK"

    except Exception as e:
        return 0, 0, 0, 0, f"Ошибка расчёта размера: {str(e)}"