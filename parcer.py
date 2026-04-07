from binance.client import Client

import os
from dotenv import load_dotenv


load_dotenv("config.env")

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(API_KEY, API_SECRET)


def get_usdt_balance():
    balance = client.futures_account_balance()

    for asset in balance:
        if asset['asset'] == 'USDT':
            total_usdt = float(asset['balance'])
            available_usdt = float(asset['availableBalance'])
            used_usdt = total_usdt - available_usdt

            return {
                "total": total_usdt,
                "available": available_usdt,
                "used": used_usdt
            }

    return None


