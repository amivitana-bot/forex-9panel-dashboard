import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import streamlit.components.v1 as components

from core_predictor import generate_dual_forecast
from chart_widgets import render_panel_chart, render_mt4_structure_chart
from structure_scanner import analyze_market_structure

# 1. Wide Layout & Zero-Scroll CSS
st.set_page_config(page_title="Forex Confirmation Matrix & MT4 Structure", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container {
        padding-top: 0.3rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.3rem !important;
        padding-right: 0.3rem !important;
    }
    header {visibility: hidden;} footer {visibility: hidden;}
    div[data-testid="stVerticalBlock"] > div { gap: 0.1rem !important; }
    </style>
""", unsafe_allow_html=True)

# 2. Audio Alarm Component (Escalating Sound)
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
                osc.frequency.setValueAtTime(880, window.audioCtx.currentTime);
                gain.gain.setValueAtTime(vol, window.audioCtx.currentTime);
                osc.connect(gain);
                gain.connect(window.audioCtx.destination);
                osc.start();
                osc.stop(window.audioCtx.currentTime + 0.15);
                if (vol < 0.5) vol += 0.05;
            }, 800);
        }
        </script>
        """
        components.html(js_code, height=0, width=0)

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

# Main Split Screen (Left: 9 Panels, Right: MT4 Structure & Controls)
col_left, col_right = st.columns([1.3, 1])

# --- RIGHT SIDE: CONTROLS & MT4 LIVE STRUCTURE CHART ---
with col_right:
    c_title, c_pair, c_tf, c_cross, c_mute, c_btn = st.columns([1.5, 1.2, 1, 1, 1, 0.8])
    with c_title: st.markdown("<h4 style='margin:0; color:#FFFFFF;'>⚡ Forex Matrix</h4>", unsafe_allow_html=True)
    with c_pair: symbol = st.selectbox("Pair", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X"], index=0, label_visibility="collapsed")
    with c_tf: timeframe = st.selectbox("TF", ["15m", "30m", "1h", "4h"], index=0, label_visibility="collapsed")
    with c_cross: crosshair_enabled = st.toggle("🎯 Crosshair", value=False)
    with c_mute: alarm_muted = st.toggle("🔕 Mute", value=False)
    with c_btn: refresh = st.button("🔄")

    try:
        df = fetch_data(symbol, timeframe)
        struct_info = analyze_market_structure(df)

        # Status Banner
        st.markdown(f"""
            <div style="background-color: #1E1E1E; padding: 4px 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: white; font-weight: bold; font-size: 13px;">MT4 Structure: {symbol.replace('=X','')} ({timeframe})</span>
                <span style="color: {struct_info['color']}; font-weight: bold; font-size: 13px;">{struct_info['status']}</span>
            </div>
        """, unsafe_allow_html=True)

        # Trigger Escalating Alarm if Bounce detected
        if struct_info['signal_alert'] and not alarm_muted:
            st.warning(f"🚨 ALERT: Adam Koo {struct_info['status']} EMA Bounce on {symbol.replace('=X','')}!")
            trigger_escalating_alarm(True)

        # Render MT4 Live Structure Chart
        fig_mt4 = render_mt4_structure_chart(df, struct_info, show_crosshair=crosshair_enabled)
        st.plotly_chart(fig_mt4, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Data error: {e}")

# --- LEFT SIDE: UNTOUCHED 9-PANEL PREDICTION MATRIX ---
with col_left:
    st.markdown("<p style='margin:0; padding:0; color:#AAAAAA; font-size:12px;'><b>9-Panel Forecast Matrix</b></p>", unsafe_allow_html=True)
    indicators = [
        ("Moving Averages", "MA"), ("Fibonacci Retracement", "FIB"), ("RSI Momentum", "RSI"),
        ("Bollinger Bands", "BOLL"), ("MACD Oscillator", "MACD"), ("Supertrend Indicator", "SUPERTREND"),
        ("Ichimoku Cloud", "ICHIMOKU"), ("ADX Trend Strength", "ADX"), ("Parabolic SAR", "PSAR")
    ]

    row1, row2, row3 = st.columns(3), st.columns(3), st.columns(3)
    grid = [row1, row2, row3]

    try:
        for idx, (title, code) in enumerate(indicators):
            col = grid[idx // 3][idx % 3]
            pred_fast, pred_slow = generate_dual_forecast(df, code)
            fig = render_panel_chart(df, pred_fast, pred_slow, title, show_crosshair=crosshair_enabled)
            
            with col:
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except Exception as e:
        st.error(f"Matrix load error: {e}")
