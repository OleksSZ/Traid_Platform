def calculate_optimal_leverage(entry_price, stop_price, loss_amount, capital):
    """
    entry_price: цена входа
    stop_price: цена выхода (стоп)
    loss_amount: желаемый убыток при достижении стопа
    capital: сумма денег на сделку без плеча
    """

    # риск на единицу актива
    risk_per_unit = abs(entry_price - stop_price)

    if risk_per_unit == 0:
        raise ValueError("Цена входа и стоп не могут совпадать.")

    # количество контрактов без плеча
    contracts_no_leverage = capital / entry_price

    # убыток без плеча
    loss_no_leverage = contracts_no_leverage * risk_per_unit

    if loss_no_leverage == 0:
        raise ValueError("Убыток без плеча равен нулю, проверь параметры.")

    # оптимальное плечо
    optimal_leverage = loss_amount / loss_no_leverage

    return optimal_leverage


if __name__ == "__main__":
    entry = float(input("Введите цену входа: "))
    stop = float(input("Введите цену выхода (стоп): "))
    desired_loss = float(input("Введите желаемый убыток: "))
    capital = float(input("Введите сумму денег на сделку (без плеча): "))

    leverage = calculate_optimal_leverage(entry, stop, desired_loss, capital)
    print(f"\nОптимальное плечо: {leverage:.2f}x")
