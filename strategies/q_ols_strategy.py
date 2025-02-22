import pandas as pd
from sklearn.linear_model import LinearRegression
from .base_strategy import BaseStrategy

class Q_OLSStrategy(BaseStrategy):
    def __init__(self, df_data, config):
        super().__init__(df_data, config)
        self.threshold_pct = config.get("threshold_pct", 0.001)
        self.volume_threshold_multiplier = config.get("volume_threshold_multiplier", 1.5)
        self.regime_filter_enabled = config.get("regime_filter_enabled", True)
        self.sma_period = config.get("sma_period", 5)
        self.lma_short = config.get("lma_short", 50)
        self.lma_long = config.get("lma_long", 100)
        self.vol_ma_window = config.get("vol_ma_window", 10)
        self.sma_col_name = f"SMA_{self.sma_period}"
        self.__prepare_data()
        self.__apply_ols_model()

    def __prepare_data(self):
        # Calculate average price and SMA used for regression
        self.data['Avg'] = (self.data['Open'] + self.data['High'] +
                            self.data['Low'] + self.data['Close']) / 4
        self.data[self.sma_col_name] = self.data['Avg'].rolling(window=self.sma_period).mean()
        # Regime moving averages
        self.data['LMA_short'] = self.data['Avg'].rolling(window=self.lma_short).mean()
        self.data['LMA_long'] = self.data['Avg'].rolling(window=self.lma_long).mean()
        # Volume moving average
        self.data['Vol_MA'] = self.data['Volume'].rolling(window=self.vol_ma_window).mean()
        # Bollinger bands (20-period window)
        boll_window = 20
        boll_multiplier = 2
        self.data['SMA_boll'] = self.data['Close'].rolling(window=boll_window).mean()
        self.data['STD_boll'] = self.data['Close'].rolling(window=boll_window).std()
        self.data['Upper_boll'] = self.data['SMA_boll'] + boll_multiplier * self.data['STD_boll']
        self.data['Lower_boll'] = self.data['SMA_boll'] - boll_multiplier * self.data['STD_boll']
        self.data.dropna(inplace=True)

    def __apply_ols_model(self):
        X = self.data[[self.sma_col_name]]
        y = self.data['Avg']
        model = LinearRegression()
        model.fit(X, y)
        self.intercept = model.intercept_
        self.slope = model.coef_[0]

    def generate_signal(self):
        latest = self.data.iloc[-1].copy()
        predicted = self.intercept + self.slope * latest[self.sma_col_name]
        deviation = latest['Avg'] - predicted
        threshold = predicted * self.threshold_pct
        print("Deviation:", deviation, "Threshold:", threshold)
        if deviation > threshold:
            signal = "Short"
        elif deviation < -threshold:
            signal = "Long"
        else:
            signal = "No Signal"
        # Regime filter
        if self.regime_filter_enabled:
            if (latest['LMA_short'] > latest['LMA_long'] and signal == "Short") or \
               (latest['LMA_short'] < latest['LMA_long'] and signal == "Long"):
                signal = "No Signal"
        # Volume filter
        if latest['Volume'] > self.volume_threshold_multiplier * latest['Vol_MA']:
            signal = "No Signal"
        return signal, latest['Date']
