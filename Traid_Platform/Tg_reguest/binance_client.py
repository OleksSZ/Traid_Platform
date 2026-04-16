import time
import requests
import pandas as pd

class BinanceClient:
    TESTNET_BASE_URL = "https://testnet.binancefuture.com"
    REAL_BASE_URL = "https://fapi.binance.com"

    def __init__(self, api_key="", api_secret="", testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.BASE_URL = self.TESTNET_BASE_URL if testnet else self.REAL_BASE_URL

    def _to_binance_symbol(self, symbol: str) -> str:
        """Превращаем 'BTC-USDT' → 'BTCUSDT'"""
        return symbol.replace('-USDT', 'USDT').replace('-', '')

    def _public_request(self, path: str, params=None, timeout: int = 10):
        if params is None:
            params = {}
        url = f"{self.BASE_URL}{path}"
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()

    def get_klines(self, symbol, interval, limit: int = 1500) -> pd.DataFrame:
        bin_symbol = self._to_binance_symbol(symbol)
        payload = {
            "symbol": bin_symbol,
            "interval": interval,
            "limit": limit
        }
        data = self._public_request("/fapi/v1/klines", payload)
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])

        df['time'] = pd.to_datetime(pd.to_numeric(df['time']), unit='ms')
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col])

        df = df.sort_values("time").reset_index(drop=True)
        return df[["time", "open", "high", "low", "close", "volume"]]

    def get_all_tikers(self):
        """Возвращает список в формате 'BTC-USDT' (как было у тебя)"""
        data = self._public_request("/fapi/v1/exchangeInfo")
        symbols = []
        for s in data.get("symbols", []):
            if (s.get("contractType") == "PERPETUAL" and
                s.get("quoteAsset") == "USDT" and
                s.get("status") == "TRADING"):
                sym = s["symbol"]  # BTCUSDT
                symbols.append(sym.replace("USDT", "-USDT"))  # → BTC-USDT
        return symbols