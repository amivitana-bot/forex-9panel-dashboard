import os
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import streamlit.components.v1 as components

from core_predictor import generate_dual_forecast
from chart_widgets import render_panel_chart, render_mt4_structure_chart
from structure_scanner import analyze_market_structure
from snapshot_generator import generate_mt4_snapshot, auto_cleanup_old_snapshots

st.set_page_config(page_title="Forex Confirmation Matrix & MT4 Structure", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container {
        padding-top: 0.2rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.3rem !important;
        padding-right: 0.3rem !important;
    }
    header {visibility: hidden;} footer {visibility: hidden;}
    div[data-testid="stVerticalBlock"] > div { gap: 0.1rem !important; }
    </style>
""", unsafe_allow_html=True)

# 1. Initialize Active Pair State
pair_list = ["USDJPY=X", "EURJPY=X", "GBPJPY=X", "AUDJPY=X", "EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDCAD=X"]

if "selected_pair" not in st.session_state:
    st.session_state["selected_pair"] = "USDJPY=X"

# Web Audio API Escalating Alarm Component
def trigger_escalating_alarm(active, test_mode=False):
    if active:
        max_beeps = 5 if test_mode else 999
        js_code = f"""
        <script>
        if (!window.audioCtx) {{
            window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }}
        let vol = 0.05;
        let count = 0;
        let alarmInterval = setInterval(() => {{
            let osc = window.audioCtx.createOscillator();
            let gain = window.audioCtx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, window.audioCtx.currentTime);
            gain.gain.setValueAtTime(vol, window.audioCtx.currentTime);
            osc.connect(gain);
            gain.connect(window.audioCtx.destination);
            osc.start();
            osc.stop(window.audioCtx.currentTime + 0.15);
            if (vol < 0.4) vol += 0.05;
            count++;
            if (count >= {max_beeps}) {{
                clearInterval(alarmInterval);
            }}
        }}, 600);
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

# Create Main Tabs to support trade gallery without breaking main view
tab_live, tab_gallery = st.tabs(["⚡ Live Trading Matrix", "📸 Trade Snapshot Gallery"])

with tab_live:
    col_left, col_right = st.columns([1.3, 1])

    # --- RIGHT SIDE: CONTROLS, MT4 STRUCTURE CHART & SNAPSHOT TEST ---
    with col_right:
        c_title, c_pair, c_tf, c_cross, c_snap, c_btn = st.columns([1.4, 1.2, 0.8, 0.8, 0.9, 0.6])
        
        with c_title: 
            st.markdown("<h4 style='margin:0; color:#FFFFFF;'>⚡ Forex Matrix</h4>", unsafe_allow_html=True)
        
        with c_pair:
            curr_idx = pair_list.index(st.session_state["selected_pair"]) if st.session_state["selected_pair"] in pair_list else 0
            symbol = st.selectbox("Pair", pair_list, index=curr_idx, key="pair_select", label_visibility="collapsed")
            st.session_state["selected_pair"] = symbol

        with c_tf: timeframe = st.selectbox("TF", ["15m", "30m", "1h", "4h"], index=0, label_visibility="collapsed")
        with c_cross: crosshair_enabled = st.toggle("🎯 Cross", value=False)
        with c_snap: test_snapshot_btn = st.button("📸 Snap")
        with c_btn: refresh = st.button("🔄")

        try:
            df = fetch_data(st.session_state["selected_pair"], timeframe)
            struct_info = analyze_market_structure(df)

            st.markdown(f"""
                <div style="background-color: #1E1E1E; padding: 4px 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: white; font-weight: bold; font-size: 13px;">MT4 Structure: {st.session_state['selected_pair'].replace('=X','')} ({timeframe})</span>
                    <span style="color: {struct_info['color']}; font-weight: bold; font-size: 13px;">{struct_info['status']}</span>
                </div>
            """, unsafe_allow_html=True)

            # Generate Snapshot Test
            if test_snapshot_btn:
                sample_trade = {
                    "id": "101",
                    "pair": st.session_state["selected_pair"],
                    "timeframe": timeframe,
                    "type": "BUY",
                    "entry_time": df.index[-5],
                    "entry_price": float(df['Close'].iloc[-5]),
                    "sl": float(df['Low'].iloc[-10]),
                    "tp": float(df['High'].iloc[-1] * 1.002)
                }
                saved_file = generate_mt4_snapshot(df, sample_trade)
                st.success(f"Generated test MT4 snapshot! Check 'Trade Snapshot Gallery' tab.")

            fig_mt4 = render_mt4_structure_chart(df, struct_info, show_crosshair=crosshair_enabled)
            st.plotly_chart(fig_mt4, use_container_width=True, config={'displayModeBar': False})

            # --- ONE-CLICK WATCHLIST SWITCH BUTTONS ---
            st.markdown("<p style='margin:0; padding:2px 0 0 0; color:#AAAAAA; font-size:11px;'><b>Active Patterns (Click button to switch view):</b></p>", unsafe_allow_html=True)
            
            active_found = False
            feed_cols = st.columns(len(pair_list) - 1)
            col_i = 0

            for p in pair_list:
                if p != st.session_state["selected_pair"]:
                    try:
                        p_df = fetch_data(p, timeframe)
                        p_info = analyze_market_structure(p_df)
                        if p_info['status'] != "CHOPPY / NO TREND":
                            active_found = True
                            clean_p = p.replace("=X", "")
                            with feed_cols[col_i]:
                                if st.button(f"{clean_p}", key=f"btn_{p}"):
                                    st.session_state["selected_pair"] = p
                                    st.rerun()
                            col_i += 1
                    except Exception:
                        continue
            
            if not active_found:
                st.markdown("<div style='background-color:#111111; padding:4px; border-radius:4px; font-size:11px; color:#666666;'>No active trend patterns detected in other watchlist pairs right now.</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Data error: {e}")

    # --- LEFT SIDE: 9-PANEL PREDICTION MATRIX ---
    with col_left:
        st.markdown(f"<p style='margin:0; padding:0; color:#AAAAAA; font-size:12px;'><b>9-Panel Forecast Matrix: {st.session_state['selected_pair'].replace('=X','')}</b></p>", unsafe_allow_html=True)
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

# --- TAB 2: TRADE GALLERY & AUTO-CLEANUP REVIEW ---
with tab_gallery:
    st.markdown("### 📸 Generated MT4 Trade Snapshots")
    auto_cleanup_old_snapshots(max_days=30)
    
    snapshot_dir = "trade_snapshots"
    if os.path.exists(snapshot_dir):
        files = [f for f in os.listdir(snapshot_dir) if f.endswith('.png')]
        if files:
            for fname in reversed(files):
                img_path = os.path.join(snapshot_dir, fname)
                st.image(img_path, caption=fname, use_container_width=True)
        else:
            st.info("No snapshots generated yet. Click the '📸 Snap' button on the Live Trading tab to generate a test snapshot.")
    else:
        st.info("No snapshots directory found.")
