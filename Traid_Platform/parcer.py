import os
from dotenv import load_dotenv
from binance.client import Client


class BinanceAccount:
    def __init__(self, env_file: str = r"C:\Users\User\Desktop\Traid_Platform\config.env"):
        self.__load_config(env_file)
        self.__client = Client(
            api_key=self.__api_key,
            api_secret=self.__api_secret
        )

    def __load_config(self, env_file: str) -> None:
        load_dotenv(env_file)

        self.__api_key = os.getenv("BINANCE_API_KEY")
        self.__api_secret = os.getenv("BINANCE_API_SECRET")

        if not self.__api_key and not self.__api_secret:
            raise ValueError("API keys not found!")
        
        if not self.__api_key:
            raise ValueError("Key not found!")
        
        if not self.__api_secret:
            raise ValueError("Secret not found!")

    def get_usdt_balance(self) -> dict | None:
        balances = self.__client.futures_account_balance()

        for asset in balances:
            if asset["asset"] == "USDT":

                total = float(asset["balance"])
                available = float(asset["availableBalance"])
                used = total - available

                return {
                    "total": total,
                    "available": available,
                    "used": used
                }

        return None


# from binance.client import Client

# import os
# from dotenv import load_dotenv


# load_dotenv("config.env")

# API_KEY = os.getenv("BINANCE_API_KEY")
# API_SECRET = os.getenv("BINANCE_API_SECRET")

# client = Client(API_KEY, API_SECRET)


# def get_usdt_balance():
#     balance = client.futures_account_balance()

#     for asset in balance:
#         if asset['asset'] == 'USDT':
#             total_usdt = float(asset['balance'])
#             available_usdt = float(asset['availableBalance'])
#             used_usdt = total_usdt - available_usdt

#             return {
#                 "total": total_usdt,
#                 "available": available_usdt,
#                 "used": used_usdt
#             }

#     return None


# File "C:\Users\User\Desktop\Traid_Platform\cs_bridge.py", line 35, in main
#     from parcer import get_usdt_balance
# ImportError: cannot import name 'get_usdt_balance' from 'parcer' (C:\Users\User\Desktop\Traid_Platform\parcer.py)
# [09:38:05] [09:38:05] ⚠️ [py stderr] Traceback (most recent call last):
#   File "C:\Users\User\Desktop\Traid_Platform\cs_bridge.py", line 115, in <module>
#     main()
