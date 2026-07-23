import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

from core_predictor import generate_dual_forecast
from chart_widgets import render_panel_chart

# 1. Page Config for Full-Screen Grid View
st.set_page_config(
    page_title="Forex Confirmation Matrix",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for compact full-screen view
st.markdown("""
    <style>
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Header & Controls
col_title, col_pair, col_tf, col_btn = st.columns([2, 1.5, 1.5, 1])

with col_title:
    st.markdown("<h3 style='margin:0; padding:0; color:#FFFFFF;'>⚡ Forex Matrix</h3>", unsafe_allow_html=True)

with col_pair:
    symbol = st.selectbox("Pair", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X"], index=0, label_visibility="collapsed")

with col_tf:
    timeframe = st.selectbox("TF", ["15m", "30m", "1h", "4h"], index=0, label_visibility="collapsed")

with col_btn:
    refresh = st.button("🔄 Refresh")

# Map timeframe choices to yfinance parameters with fallback periods
tf_config = {
    "15m": {"interval": "15m", "periods": ["1mo", "5d", "7d"]},
    "30m": {"interval": "30m", "periods": ["1mo", "5d", "7d"]},
    "1h":  {"interval": "1h",  "periods": ["1mo", "3mo"]},
    "4h":  {"interval": "1h",  "periods": ["3mo", "6mo"]}
}

# 3. Load Market Data with Robust Fallbacks
@st.cache_data(ttl=60)
def fetch_data(ticker, tf):
    cfg = tf_config[tf]
    interval = cfg["interval"]
    data = pd.DataFrame()
    
    ticker_obj = yf.Ticker(ticker)

    # Try primary history API
    for period in cfg["periods"]:
        try:
            data = ticker_obj.history(period=period, interval=interval)
            if not data.empty:
                break
        except Exception:
            continue
            
    # Fallback to yf.download if history() is empty
    if data.empty:
        for period in cfg["periods"]:
            try:
                data = yf.download(ticker, period=period, interval=interval, progress=False)
                if not data.empty:
                    break
            except Exception:
                continue

    if data.empty:
        raise ValueError(f"Yahoo Finance is temporarily not returning data for {ticker} on {tf}. Please try another pair or timeframe.")

    # Flatten MultiIndex columns if present
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Capitalize column headers
    data.columns = [str(c).capitalize() for c in data.columns]

    required_cols = ['Open', 'High', 'Low', 'Close']
    data = data[required_cols].dropna().copy()
    
    # Resample 1h to 4h if 4h requested
    if tf == "4h":
        data = data.resample('4h').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'
        }).dropna()

    return data.tail(60)

try:
    df = fetch_data(symbol, timeframe)

    indicators = [
        ("Moving Averages", "MA"),
        ("Fibonacci Retracement", "FIB"),
        ("RSI Momentum", "RSI"),
        ("Bollinger Bands", "BOLL"),
        ("MACD Oscillator", "MACD"),
        ("Supertrend Indicator", "SUPERTREND"),
        ("Ichimoku Cloud", "ICHIMOKU"),
        ("ADX Trend Strength", "ADX"),
        ("Parabolic SAR", "PSAR")
    ]

    # 4. Render 3x3 Grid Matrix
    row1 = st.columns(3)
    row2 = st.columns(3)
    row3 = st.columns(3)
    
    grid = [row1, row2, row3]

    for idx, (title, code) in enumerate(indicators):
        col = grid[idx // 3][idx % 3]
        pred_fast, pred_slow = generate_dual_forecast(df, code)
        fig = render_panel_chart(df, pred_fast, pred_slow, title)
        
        with col:
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"Error loading live market data: {e}")
