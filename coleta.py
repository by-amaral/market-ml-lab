import ccxt

corretora = ccxt.binance({"enableRateLimit": True})

candles = corretora.fetch_ohlcv(
    "BTC/USDT",
    timeframe="1h",
    limit=5,
)

print("Quantidade recebida:", len(candles))

for candle in candles:
    print(candle)