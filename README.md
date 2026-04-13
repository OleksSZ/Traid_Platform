gui.py - Основной файл с интерфейсом
trader.py - файл который отвечает за передачу инфы на сервера binance
leverage - расчет плеча ( Сделан криво ) 
checks - просмотр оптимален ли RR ( 1к3) 
database -  запись информации о сделках в Exel 


Поскольку нету файла config.json то скрипт не будет запускаться 
Пример config.json
BINANCE_API_KEY=
BINANCE_API_SECRET=
RISK_PER_TRADE_USD='0.1'
RISK_PERCENT='1.0'



Interface - создает  Web-интерфейс на streamlit  в котором можно взаимодействовать с freqtrade и бектестить стратегии 
strategies/CombinedConstructorStrategy - сами стратегии для бектестов
strategies/strategy_settings - json с данными стратегий (передаеться в CombinedConstructorStrategy)
strategies/strategy_constructor_gui - ОТвечает за данные в json файле и  запоминание и редактирование данных стратегий 
data/ - Исторические данные для Бектестов (Можно скачать во второй вкладе web интерфейса )
