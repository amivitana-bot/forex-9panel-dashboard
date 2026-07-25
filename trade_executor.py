import pandas as pd
from datetime import datetime, timedelta

def evaluate_and_place_trade(df, symbol, timeframe, active_trades, daily_counts, min_matrix_score=6, max_daily_trades=3):
    """
    Evaluates market setup for Adam Khoo setup (EMA pullback + HH/HL) and enforces risk rules.
    Returns: A trade dictionary if successful, else None.
    """
    if df.empty or len(df) < 55:  # Need data for EMA 50
        return None

    # 1. Enforce Daily Trade Cap (Max 3/Day across all pairs)
    today_date = datetime.now().strftime('%Y-%m-%d')
    if daily_counts.get(today_date, 0) >= max_daily_trades:
        # Return special message so the dashboard can display why it stopped
        return {"id": "DAILY_CAP_REACHED"}

    # 2. Check for existing active trade on this specific pair
    for trade in active_trades:
        if trade['pair'] == symbol and trade['status'] == 'OPEN':
            return None # Already in a trade on this pair

    # 3. Define Entry Criteria Signals
    last_candle = df.iloc[-1]
    last_price = last_candle['Close']
    
    # Simple EMAs for the setup (Assuming they are pre-calculated)
    ema6 = df['EMA_6'].iloc[-1]
    ema18 = df['EMA_18'].iloc[-1]
    ema50 = df['EMA_50'].iloc[-1]
    ema200 = df['EMA_200'].iloc[-1]
    
    matrix_score = last_candle.get('prediction_score', 0) # Mock score

    # Structure Check (Mock for this module)
    is_uptrend = (ema6 > ema18 > ema50 > ema200)
    is_downtrend = (ema6 < ema18 < ema50 < ema200)

    is_pullback_uptrend = last_candle['Low'] < ema18 and last_price > ema18 # Pullback and bounce off EMA18
    is_pullback_downtrend = last_candle['High'] > ema18 and last_price < ema18 # Pullback and bounce off EMA18
    
    # 4. Define Trade Type (BUY/SELL)
    trade_type = None
    if is_uptrend and is_pullback_uptrend and matrix_score >= min_matrix_score:
        trade_type = 'BUY'
    elif is_downtrend and is_pullback_downtrend and matrix_score >= min_matrix_score:
        trade_type = 'SELL'
    
    # Return None if no setup
    if trade_type is None:
        return None

    # 5. Define SL and TP using Price Structure (Mocking swing levels for simulation)
    swing_distance = df['High'].tail(15).max() - df['Low'].tail(15).min() # Mock swing distance
    risk_pips_distance = swing_distance if swing_distance > 0.05 else 0.1 # Minimum risk distance
    
    sl_price = 0.0
    tp_price = 0.0
    entry_price = last_price
    
    # Set Risk Reward Ratio (1:1.5 default)
    rr_ratio = 1.5

    if trade_type == 'BUY':
        sl_price = entry_price - risk_pips_distance
        tp_price = entry_price + (risk_pips_distance * rr_ratio)
    elif trade_type == 'SELL':
        sl_price = entry_price + risk_pips_distance
        tp_price = entry_price - (risk_pips_distance * rr_ratio)

    # 6. Increment Daily Counter and Form Trade Object
    daily_counts[today_date] = daily_counts.get(today_date, 0) + 1

    return {
        "id": f"T_{int(datetime.now().timestamp())}_{symbol.replace('=X','')}",
        "pair": symbol,
        "timeframe": timeframe,
        "type": trade_type,
        "status": "OPEN",
        "entry_time": last_candle.name,
        "entry_price": float(entry_price),
        "sl": float(sl_price),
        "tp": float(tp_price),
        "date_taken": today_date
    }
