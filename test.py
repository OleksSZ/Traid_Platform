# -*- coding: utf-8 -*-
def risk_check():
    # Ввод параметров
    balance = float(input("Введите размер баланса ($): "))
    entry_percent = float(input("Введите процент входа от баланса (%): "))
    leverage = float(input("Введите плечо: "))
    entry_price = float(input("Введите точку входа: "))
    stop_price = float(input("Введите точку стопа: "))
    take_price = float(input("Введите точку тейка: "))
    risk_level = int(input("Введите уровень риска (1-10): "))

    # Сумма входа
    position_value = balance * (entry_percent / 100) * leverage
    position_size = position_value / entry_price

    # Потенциальный убыток и прибыль
    loss_per_unit = abs(entry_price - stop_price)
    total_loss = loss_per_unit * position_size
    profit_per_unit = abs(take_price - entry_price)
    total_profit = profit_per_unit * position_size

    # Риск в %
    risk_percent = (total_loss / balance) * 100
    rr_ratio = total_profit / total_loss if total_loss > 0 else float('inf')

    # Требования по шкале риска
    rr_requirement = {1:2, 2:3, 3:3, 4:3, 5:3, 6:3, 7:3, 8:4, 9:3.5, 10:5}
    risk_requirement = {1:4, 2:3, 3:2, 4:1.5, 5:1.2, 6:1, 7:1, 8:1, 9:0.5, 10:0.5}

    rr_ok = rr_ratio >= rr_requirement[risk_level]
    risk_ok = risk_percent <= (risk_requirement[risk_level] + 0.1)  # допуск 0.1%

    # Вывод результатов
    print("\n--- Результаты ---")
    print(f"Размер позиции: {position_size:.4f} единиц")
    print(f"Сумма сделки: {position_value:.2f} $")
    print(f"Риск: {total_loss:.2f} $ ({risk_percent:.2f} %)")
    print(f"Потенциальная прибыль: {total_profit:.2f} $")
    print(f"RR соотношение: {rr_ratio:.2f}")

    if rr_ok and risk_ok:
        print("✅ Сделка входит в риск по шкале")
    else:
        if not rr_ok:
            print("❌ Сделка не входит в риск через RR")
        if not risk_ok:
            print("❌ Сделка не входит в риск через процент убытка")

    # Оптимальное плечо (если риск слишком велик)
    if not risk_ok:
        optimal_leverage = leverage * (risk_requirement[risk_level] / risk_percent)
        print(f"Рекомендуемое плечо для снижения риска: {optimal_leverage:.2f}")


if __name__ == "__main__":
    risk_check()
