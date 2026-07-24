import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import streamlit.components.v1 as components

from core_predictor import generate_dual_forecast
from chart_widgets import render_panel_chart
from structure_scanner import analyze_market_structure

st.set_page_config(page_title="Forex Confirmation Matrix", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    div[data-testid="stVerticalBlock"] > div { gap: 0.2rem !important; }
    </style>
""", unsafe_allow_html=True)

# Audio Alarm System (JavaScript Web Audio API)
def trigger_escalating_alarm(active):
    if active:
        js_code = """
        <script>
        if (!window.audioCtx) {
            window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (!window.alarmInterval) {
            let vol = 0.05;
            window.alarmInterval = setInterval(() => {
                let osc = window.audioCtx.createOscillator();
                let gain = window.audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(880, window.audioCtx.currentTime); // A5 pitch
                gain.gain.setValueAtTime(vol, window.audioCtx.currentTime);
                osc.connect(gain);
                gain.connect(window.audioCtx.destination);
                osc.start();
                osc.stop(window.audioCtx.currentTime + 0.15);
                if (vol < 0.5) vol += 0.05; // Escalating volume
            }, 800);
        }
        </script>
        """
        components.html(js_code, height=0, width=0)

# Header Controls
col_title, col_pair, col_tf, col_cross, col_mute, col_btn = st.columns([1.8, 1.2, 1, 1, 1, 0.8])

with col_title:
    st.markdown("<h3 style='margin:0; padding:0; color:#FFFFFF;'>⚡ Forex Matrix</h3>", unsafe_allow_html=True)

with col_pair:
    symbol = st.selectbox("Pair", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X"], index=0, label_visibility="collapsed")

with col_tf:
    timeframe = st.selectbox("TF", ["15m", "30m", "1h", "4h"], index=0, label_visibility="collapsed")

with col_cross:
    crosshair_enabled = st.toggle("🎯 Crosshair", value=False)

with col_mute:
    alarm_muted = st.toggle("🔕 Mute Alarm", value=False)

with col_btn:
    refresh = st.button("🔄 Refresh")

tf_config = {
    "15m": {"interval": "15m", "periods": ["1mo", "5d", "7d"]},
    "30m": {"interval": "30m", "periods": ["1mo", "5d", "7d"]},
    "1h":  {"interval": "1h",  "periods": ["1mo", "3mo"]},
    "4h":  {"interval": "1h",  "periods": ["3mo", "6mo"]}
}

@st.cache_data(ttl=60)
def fetch_data(ticker, tf):
    cfg = tf_config[tf]
    data = pd.DataFrame()
    ticker_obj = yf.Ticker(ticker)

    for period in cfg["periods"]:
        try:
            data = ticker_obj.history(period=period, interval=cfg["interval"])
            if not data.empty: break
        except Exception: continue

    if data.empty:
        raise ValueError(f"No market data returned for {ticker} on {tf}.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data.columns = [str(c).capitalize() for c in data.columns]
    data = data[['Open', 'High', 'Low', 'Close']].dropna().copy()

    if tf == "4h":
        data = data.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()

    return data.tail(60)

try:
    df = fetch_data(symbol, timeframe)

    # Perform Adam Koo Market Structure Analysis
    struct_info = analyze_market_structure(df)

    # Display Structure Status Badge Top Header
    st.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 6px 12px; border-radius: 5px; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">
            <span style="color: white; font-weight: bold;">Pair: {symbol.replace('=X','')} | TF: {timeframe}</span>
            <span style="color: {struct_info['color']}; font-weight: bold; font-size: 14px;">Structure: {struct_info['status']}</span>
        </div>
    """, unsafe_allow_html=True)

    # Trigger Alarm if Signal Alert is active and Alarm is NOT muted
    if struct_info['signal_alert'] and not alarm_muted:
        st.warning(f"🚨 ALERT: Clean {struct_info['status']} EMA Bounce detected on {symbol.replace('=X','')} ({timeframe})!")
        trigger_escalating_alarm(True)

    indicators = [
        ("Moving Averages", "MA"), ("Fibonacci Retracement", "FIB"), ("RSI Momentum", "RSI"),
        ("Bollinger Bands", "BOLL"), ("MACD Oscillator", "MACD"), ("Supertrend Indicator", "SUPERTREND"),
        ("Ichimoku Cloud", "ICHIMOKU"), ("ADX Trend Strength", "ADX"), ("Parabolic SAR", "PSAR")
    ]

    row1, row2, row3 = st.columns(3), st.columns(3), st.columns(3)
    grid = [row1, row2, row3]

    for idx, (title, code) in enumerate(indicators):
        col = grid[idx // 3][idx % 3]
        pred_fast, pred_slow = generate_dual_forecast(df, code)
        fig = render_panel_chart(df, pred_fast, pred_slow, title, show_crosshair=crosshair_enabled, structure_info=struct_info)
        
        with col:
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"Error loading market data: {e}")
