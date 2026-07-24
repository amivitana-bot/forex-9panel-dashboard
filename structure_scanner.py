import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

def calculate_ema_stack(df):
    """Calculates Adam Koo's EMA stack: 6 EMA, 18 EMA, 50 EMA, 200 SMA."""
    df = df.copy()
    df['EMA_6'] = df['Close'].ewm(span=6, adjust=False).mean()
    df['EMA_18'] = df['Close'].ewm(span=18, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['SMA_200'] = df['Close'].rolling(window=min(200, len(df))).mean()
    return df

def analyze_market_structure(df, order=4):
    """
    Detects HH/HL or LH/LL structure and EMA bounces based on Adam Koo's rules.
    """
    df = calculate_ema_stack(df)
    
    # 1. Detect Swing Points
    high_idx = argrelextrema(df['High'].values, np.greater_equal, order=order)[0]
    low_idx = argrelextrema(df['Low'].values, np.less_equal, order=order)[0]
    
    swing_highs = df.iloc[high_idx][['High']].copy()
    swing_lows = df.iloc[low_idx][['Low']].copy()
    
    # Structure Check (At least 2 peaks and 2 troughs needed)
    is_hh_hl = False
    is_lh_ll = False
    
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        last_high, prev_high = swing_highs['High'].iloc[-1], swing_highs['High'].iloc[-2]
        last_low, prev_low = swing_lows['Low'].iloc[-1], swing_lows['Low'].iloc[-2]
        
        is_hh_hl = (last_high > prev_high) and (last_low > prev_low)
        is_lh_ll = (last_high < prev_high) and (last_low < prev_low)

    # 2. EMA Stack Alignment
    curr = df.iloc[-1]
    bull_stack = (curr['EMA_6'] > curr['EMA_18']) and (curr['EMA_18'] > curr['EMA_50'])
    bear_stack = (curr['EMA_6'] < curr['EMA_18']) and (curr['EMA_18'] < curr['EMA_50'])
    
    # 3. Pullback / Bounce Check near 18 or 50 EMA
    dist_50 = abs(curr['Close'] - curr['EMA_50']) / curr['Close']
    dist_18 = abs(curr['Close'] - curr['EMA_18']) / curr['Close']
    is_bouncing = (dist_50 < 0.0015) or (dist_18 < 0.0015)

    # Status Determination
    if is_hh_hl and bull_stack:
        status = "BULLISH HH/HL"
        color = "#00FF7F" # Spring Green
    elif is_lh_ll and bear_stack:
        status = "BEARISH LH/LL"
        color = "#FF4500" # Orange Red
    else:
        status = "CHOPPY / NO TREND"
        color = "#888888" # Grey

    signal_alert = (status in ["BULLISH HH/HL", "BEARISH LH/LL"]) and is_bouncing

    return {
        "status": status,
        "color": color,
        "is_bouncing": is_bouncing,
        "signal_alert": signal_alert,
        "high_idx": high_idx,
        "low_idx": low_idx,
        "df": df
    }
