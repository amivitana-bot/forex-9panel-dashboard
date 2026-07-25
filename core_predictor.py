import numpy as np
import pandas as pd

def generate_dual_forecast(df, code):
    if df.empty or len(df) < 10:
        return None, None

    last_close = float(df['Close'].iloc[-1])
    recent_std = float(df['Close'].tail(20).std())
    
    if np.isnan(recent_std) or recent_std == 0:
        recent_std = last_close * 0.001

    diff = last_close - float(df['Close'].iloc[-5])
    direction = 1 if diff >= 0 else -1

    fast_pred = last_close + (direction * recent_std * 0.8)
    slow_pred = last_close + (direction * recent_std * 1.5)

    return float(fast_pred), float(slow_pred)
