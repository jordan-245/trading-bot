import datetime
from data_retrieval import fetch_historical_data
from api_helpers import get_price_precision, set_leverage, create_bybit_order, set_trading_stop
from logger import log_trade

# Import the desired strategy (switch out this import to swap strategies)
from strategies.q_ols_strategy import Q_OLSStrategy

strategy_config = {
    "threshold_pct": 0.001,
    "volume_threshold_multiplier": 1.5,
    "regime_filter_enabled": True,
    "sma_period": 5,
    "lma_short": 50,
    "lma_long": 100,
    "vol_ma_window": 10
}

def execute_trade(signal, symbol="BTCUSDT", base_quantity=0.001, order_price=None):
    quantity = base_quantity * 10  # Example scaling
    price_precision = get_price_precision(symbol)
    qty_str = str(quantity)
    if signal == "Long":
        side = "Buy"
        posIdx = 1
    elif signal == "Short":
        side = "Sell"
        posIdx = 2
    else:
        print("No trade executed. Signal:", signal)
        return 0

    order_type = "Market"
    time_in_force = "IOC"
    response = create_bybit_order("linear", symbol, side, order_type, qty_str, time_in_force, isLeverage=1, positionIdx=posIdx)
    print(f"Placed entry {side} Market Order:")
    print(response)
    trade_time = datetime.datetime.now()
    log_trade(trade_time, signal, side, symbol, "Market", quantity, order_price, None, None, response)
    return quantity

def place_conditional_exit_orders(signal, symbol, entry_price, sma_value, boll_value, full_quantity, price_precision):
    half_qty = full_quantity / 2
    half_qty_str = str(half_qty)
    tp_precision = price_precision

    # Determine exit side
    exit_side = "Sell" if signal == "Long" else "Buy"

    # Conditional limit order for 50% exit at SMA
    cond_response = create_bybit_order(
        category="linear",
        symbol=symbol,
        side=exit_side,
        orderType="Limit",
        qty=half_qty_str,
        timeInForce="GTC",
        price=str(round(sma_value, tp_precision)),
        triggerPrice=str(round(sma_value, tp_precision)),
        triggerDirection=2 if signal == "Long" else 1,  # Added triggerDirection
        reduceOnly="true",        
        orderFilter="StopOrder",
        isLeverage=1,
        positionIdx=1 if signal=="Long" else 2
    )

    print("Placed conditional exit order at SMA:")
    print(cond_response)

    # Trailing stop for remaining 50%
    if signal == "Long":
        trailing_distance = round(sma_value - entry_price, tp_precision)
        take_profit_price = round(boll_value, tp_precision)
        stop_loss_price = round(entry_price, tp_precision)
        positionIdx = 1
    else:
        trailing_distance = round(entry_price - sma_value, tp_precision)
        take_profit_price = round(boll_value, tp_precision)
        stop_loss_price = round(entry_price, tp_precision)
        print(f"Trailing distance: {trailing_distance}, Take profit price: {take_profit_price}, Stop loss price: {stop_loss_price}")
        positionIdx = 2

    trail_response = set_trading_stop(
        category="linear",
        symbol=symbol,
        takeProfit=str(take_profit_price),
        stopLoss=str(stop_loss_price),
        trailingStop=str(trailing_distance),
        activePrice=str(round(sma_value, tp_precision)),
        tpslMode="Partial",
        tpOrderType="Limit",
        slOrderType="Limit",
        tpSize=half_qty_str,
        slSize=half_qty_str,
        positionIdx=positionIdx,
        tpLimitPrice=str(take_profit_price),
        slLimitPrice=str(stop_loss_price)
    )
    print("Set trading stop for remaining half:")
    print(trail_response)

def main():
    # Fetch historical data
    df_data = fetch_historical_data(ticker="BTCUSDT", period_hours=300, timeframe='15m')
    if df_data.empty:
        print("No data retrieved.")
        return

    # Instantiate our chosen trading strategy
    strategy = Q_OLSStrategy(df_data, strategy_config)
    signal, timestamp = strategy.generate_signal()
    print(f"Latest signal at {timestamp} is: {signal}")

    if signal not in ["Long", "Short"]:
        print("No actionable signal generated; no order executed.")
        return

    # Use latest data for pricing and indicators
    latest = strategy.data.iloc[-1]
    order_price = latest["Close"]
    sma_value = latest[strategy.sma_col_name]
    boll_value = latest["Upper_boll"] if signal=="Long" else latest["Lower_boll"]
    price_precision = get_price_precision("BTCUSDT")

    # Set leverage (example)
    leverage_response = set_leverage("BTCUSDT", "15", "15")
    print("Set leverage response:", leverage_response)

    # Execute the entry trade
    full_quantity = execute_trade(signal, symbol="BTCUSDT", base_quantity=0.001, order_price=order_price)

    # Place exit orders
    place_conditional_exit_orders(signal, symbol="BTCUSDT", entry_price=order_price,
                                  sma_value=sma_value, boll_value=boll_value,
                                  full_quantity=full_quantity, price_precision=price_precision)

if __name__ == "__main__":
    main()
