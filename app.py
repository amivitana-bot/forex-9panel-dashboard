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
    initial_sidebar_state="expanded"
)

# Custom Styling to maximize screen area for 3x3 Grid
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    h1 {
        font-size: 1.6rem !important;
        margin-bottom: 0rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Header & Controls
st.title("⚡ 9-Panel Forex Confirmation Matrix")

# Controls Section: Currency Pair & Timeframe Selector
col_pair, col_tf, col_btn = st.columns([2, 2, 1])

with col_pair:
    symbol = st.selectbox("Select Currency Pair", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X"], index=0)

with col_tf:
    timeframe = st.selectbox("Select Timeframe", ["15m", "30m", "1h", "4h"], index=0)

with col_btn:
    st.write("") # Spacing
    st.write("") 
    refresh = st.button("🔄 Refresh Data")

# Map timeframe choices to yfinance interval codes
tf_map = {
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "1h" # 4h simulated via resample/1h base
}

# 3. Load Market Data
@st.cache_data(ttl=60)
def fetch_data(ticker, tf):
    interval = tf_map[tf]
    period = "1mo" if interval in ["15m", "30m"] else "6mo"
    data = yf.download(ticker, period=period, interval=interval)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data.dropna()
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

    st.markdown("---")

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
            st.pyplot(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading live market data: {e}")
