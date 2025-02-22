import ccxt
import pandas as pd

def fetch_historical_data(ticker="BTCUSDT", period_hours=300, timeframe='15m'):
    exchange = ccxt.bybit({'enableRateLimit': True})
    now = exchange.milliseconds()
    since = now - period_hours * 3600 * 1000
    candles = exchange.fetch_ohlcv('BTC/USDT', timeframe, since=since, limit=1000)
    df = pd.DataFrame(candles, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    df["Date"] = pd.to_datetime(df["Date"], unit="ms")
    return df
