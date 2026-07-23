import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from config_settings import FAST_LOOKBACK, SLOW_LOOKBACK, FORECAST_STEPS

def generate_dual_forecast(df, indicator_type):
    """
    Calculates both Fast (Spike/Yellow) and Slow (Smooth/Blue) 4-candle projections 
    independently for a given indicator slot.
    """
    close_prices = df['Close'].values
    n = len(close_prices)
    
    # Feature extraction based on indicator logic
    if indicator_type == "MA":
        feat = (df['Close'].ewm(span=20).mean() - df['Close'].rolling(20).mean()).fillna(0).values
    elif indicator_type == "FIB":
        high, low = df['High'].max(), df['Low'].min()
        feat = (df['Close'] - (high - 0.618 * (high - low))).values
    elif indicator_type == "RSI":
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        feat = (100 - (100 / (1 + (gain / (loss + 1e-9))))).fillna(50).values
    elif indicator_type == "BOLL":
        sma = df['Close'].rolling(20).mean()
        std = df['Close'].rolling(20).std()
        feat = ((df['Close'] - (sma - std*2)) / ((sma + std*2) - (sma - std*2) + 1e-9)).fillna(0.5).values
    elif indicator_type == "MACD":
        feat = ((df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()) - (df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()).ewm(span=9).mean()).fillna(0).values
    elif indicator_type == "SUPERTREND":
        tr = np.maximum(df['High'] - df['Low'], np.abs(df['High'] - df['Close'].shift(1)))
        feat = ((df['High'] + df['Low'])/2 - 3 * pd.Series(tr).rolling(10).mean().fillna(0)).values
    elif indicator_type == "ICHIMOKU":
        feat = (((df['High'].rolling(9).max() + df['Low'].rolling(9).min())/2) - ((df['High'].rolling(26).max() + df['Low'].rolling(26).min())/2)).fillna(0).values
    elif indicator_type == "ADX":
        feat = df['Close'].pct_change().abs().rolling(14).mean().fillna(0).values
    elif indicator_type == "PSAR":
        feat = (df['High'] - df['Low']).values
    else:
        feat = np.zeros(n)

    X = np.arange(n).reshape(-1, 1)
    
    # 1. Fast / Spike Model (Short Lookback)
    X_fast = X[-FAST_LOOKBACK:]
    y_fast = close_prices[-FAST_LOOKBACK:]
    feat_fast = feat[-FAST_LOOKBACK:]
    model_fast = LinearRegression().fit(np.column_stack((X_fast, feat_fast)), y_fast)
    
    fut_X_fast = np.arange(n, n + FORECAST_STEPS).reshape(-1, 1)
    fut_feat_fast = np.repeat(feat_fast[-1], FORECAST_STEPS).reshape(-1, 1)
    pred_fast = model_fast.predict(np.column_stack((fut_X_fast, fut_feat_fast)))

    # 2. Slow / Smooth Model (Long Lookback)
    X_slow = X[-SLOW_LOOKBACK:]
    y_slow = close_prices[-SLOW_LOOKBACK:]
    feat_slow = feat[-SLOW_LOOKBACK:]
    model_slow = LinearRegression().fit(np.column_stack((X_slow, feat_slow)), y_slow)
    
    fut_X_slow = np.arange(n, n + FORECAST_STEPS).reshape(-1, 1)
    fut_feat_slow = np.repeat(feat_slow[-1], FORECAST_STEPS).reshape(-1, 1)
    pred_slow = model_slow.predict(np.column_stack((fut_X_slow, fut_feat_slow)))

    return pred_fast, pred_slow
