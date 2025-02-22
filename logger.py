import psycopg2, json
from psycopg2.extras import Json

def log_trade(trade_time, signal, side, symbol, order_type, quantity,
              order_price, take_profit, stop_loss, response):
    try:
        conn = psycopg2.connect("postgresql://user:password@host/db?sslmode=require")
        cur = conn.cursor()
        query = """
            INSERT INTO trading_logs 
            (trade_time, signal, side, symbol, order_type, quantity, order_price, take_profit, stop_loss, response)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (trade_time, signal, side, symbol, order_type, float(quantity),
                              float(order_price) if order_price else None,
                              float(take_profit) if take_profit else None,
                              float(stop_loss) if stop_loss else None,
                              json.dumps(response)))
        conn.commit()
        cur.close()
        conn.close()
        print("Trade log inserted successfully.")
    except Exception as e:
        print("Error logging trade to database:", e)
