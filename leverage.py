def calculate_optimal_leverage(
    entry_price: float,
    stop_price: float,
    margin_usd: float,
    risk_dollar: float
) -> int:
    """
    НОВАЯ ЛОГИКА:
    Подбирает плечо так, чтобы при срабатывании стопа потеря была ровно risk_dollar.
    """
    if margin_usd <= 0 or risk_dollar <= 0:
        raise ValueError("Маржа и риск должны быть положительными")

    distance = abs(entry_price - stop_price)
    if distance == 0:
        raise ValueError("Цена входа и стоп не могут быть одинаковыми")

    stop_pct = distance / entry_price                     # расстояние до стопа в %

    # Основная формула
    leverage_float = risk_dollar / (margin_usd * stop_pct)

    # Округляем до целого
    leverage = round(leverage_float)

    # Защита от нереалистичных значений
    if leverage < 1:
        leverage = 1
    if leverage > 50:                                     # можно изменить на 75 или 100
        leverage = 50

    return leverage