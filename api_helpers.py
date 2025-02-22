# api_helpers.py
import time, hmac, hashlib, requests
from config import BYBIT_API_KEY, BYBIT_API_SECRET, BYBIT_BASE_URL

def get_signature(params, api_secret=BYBIT_API_SECRET):
    qs = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(api_secret.encode('utf-8'), qs.encode('utf-8'), hashlib.sha256).hexdigest()

def get_server_time():
    url = f"{BYBIT_BASE_URL}/v5/market/time"
    r = requests.get(url)
    return r.json()['result']['timeSecond']

def create_bybit_order(category, symbol, side, orderType, qty, timeInForce, **kwargs):
    endpoint = "/v5/order/create"
    url = BYBIT_BASE_URL + endpoint
    server_time = get_server_time()
    params = {
        "api_key": BYBIT_API_KEY,
        "category": category,
        "symbol": symbol,
        "side": side,
        "orderType": orderType,
        "qty": qty,
        "timeInForce": timeInForce,
        "recvWindow": "5000",
        "timestamp": str(int(float(server_time) * 1000))
    }
    params.update(kwargs)
    params["sign"] = get_signature(params)
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=params, headers=headers)
    return r.json()

def set_leverage(symbol, buy_leverage, sell_leverage):
    endpoint = "/v5/position/set-leverage"
    url = BYBIT_BASE_URL + endpoint
    server_time = get_server_time()
    params = {
        "api_key": BYBIT_API_KEY,
        "category": "linear",
        "symbol": symbol,
        "buyLeverage": buy_leverage,
        "sellLeverage": sell_leverage,
        "timestamp": str(int(float(server_time) * 1000)),
        "recvWindow": "5000"
    }
    params["sign"] = get_signature(params)
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=params, headers=headers)
    return r.json()

def set_trading_stop(**kwargs):
    endpoint = "/v5/position/trading-stop"
    url = BYBIT_BASE_URL + endpoint
    server_time = get_server_time()
    kwargs["api_key"] = BYBIT_API_KEY
    kwargs["timestamp"] = str(int(float(server_time) * 1000))
    kwargs["recvWindow"] = "5000"
    kwargs["sign"] = get_signature(kwargs)
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=kwargs, headers=headers)
    return r.json()

def get_price_precision(symbol: str):
    import ccxt
    exchange = ccxt.binance({'enableRateLimit': True})
    exchange.load_markets()
    if symbol in exchange.markets:
        return int(exchange.markets[symbol]['precision']['price'])
    for mkt, info in exchange.markets.items():
        if mkt.replace("/", "") == symbol:
            return int(info['precision']['price'])
    raise KeyError(f"Symbol {symbol} not found")
