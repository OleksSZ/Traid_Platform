import aiohttp
import asyncio

BASE_URL = "https://fapi.binance.com"

async def fetch_symbols():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/fapi/v1/exchangeInfo") as resp:
            data = await resp.json()
            return [s["symbol"] for s in data["symbols"] if s["contractType"] == "PERPETUAL" and s["quoteAsset"] == "USDT"]

async def fetch_funding_rate(session, symbol):
    async with session.get(f"{BASE_URL}/fapi/v1/premiumIndex", params={"symbol": symbol}) as resp:
        data = await resp.json()
        funding_rate = float(data.get("lastFundingRate", 0))
        if funding_rate > 0.0009:  # фильтр > 1%
            print(f"{symbol}: fundingRate={funding_rate*100:.2f}% | nextFundingTime={data.get('nextFundingTime')}")

async def main():
    symbols = await fetch_symbols()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_funding_rate(session, symbol) for symbol in symbols]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
