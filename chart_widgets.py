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

# Ultra-tight padding so charts take over the screen
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

# 2. Controls Section (Single Row Layout)
col_title, col_pair, col_tf, col_btn = st.columns([2, 1.5, 1.5, 1])

with col_title:
    st.markdown("<h3 style='margin:0; padding:0; color:#FFFFFF;'>⚡ Forex Matrix</h3>", unsafe_allow_html=True)

with col_pair:
    symbol = st.selectbox("Pair", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X"], index=0, label_visibility="collapsed")

with col_tf:
    timeframe = st.selectbox("TF", ["15m", "30m", "1h", "4h"], index=0, label_visibility="collapsed")

with col_btn:
    refresh = st.button("🔄 Refresh")

# Map timeframe choices to yfinance parameters
tf_config = {
    "15m": {"interval": "15m", "period": "5d"},
    "30m": {"interval": "30m", "period": "5d"},
    "1h":  {"interval": "1h",  "period": "1mo"},
    "4h":  {"interval": "1h",  "period": "3mo"}
}

# 3. Load Market Data
@st.cache_data(ttl=60)
def fetch_data(ticker, tf):
    cfg = tf_config[tf]
    data = yf.download(ticker, period=cfg["period"], interval=cfg["interval"], progress=False)
    
    if data.empty:
        raise ValueError(f"No data returned for {ticker} on {tf} timeframe.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    required_cols = ['Open', 'High', 'Low', 'Close']
    data = data[required_cols].dropna().copy()
    
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
            st.pyplot(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading live market data: {e}")
