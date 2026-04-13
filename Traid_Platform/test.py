import asyncio
from binance import AsyncClient, BinanceSocketManager

async def main():
    api_key = "5fRzEbXkRe5aAVoHhOQRuDwJTmwSAjJJLyJHNZQpPAbVBfmaaGDiding9se5bsf3"
    api_secret = "hh3UWGoKhQ7yjorMu9H2snJnZlic13JXNSs65PawHEukQT0dKMMx8ps2aXsSrj8Q"

    client = await AsyncClient.create(api_key, api_secret)
    bm = BinanceSocketManager(client)

    ts = bm.depth_socket('BTCUSDT', depth=100)
    async with ts as stream:
        while True:
            res = await stream.recv()
            print(res)

    await client.close_connection()

asyncio.run(main())
