gui.py - Основной файл с интерфейсом
trader.py - файл который отвечает за передачу инфы на сервера binance
leverage - расчет плеча ( Сделан криво ) 
checks - просмотр оптимален ли RR ( 1к3) 
database -  запись информации о сделках в Exel 


Поскольку нету файла config,json то скрипт не будет запускаться 
Пример config.json
BINANCE_API_KEY=
BINANCE_API_SECRET=
RISK_PER_TRADE_USD='0.1'
RISK_PERCENT='1.0'
