import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
import pandas as pd

def generate_mt4_snapshot(df, trade_info, output_dir="trade_snapshots"):
    """
    Generates a dark-mode, MT4-style trade snapshot optimized for ultra-wide displays.
    Saves image as PNG with precise price/date labels, entry arrow, SL, and TP lines.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Base Candlestick Chart (MT4 Classic Colors)
    fig = go.Figure(data=[
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='#00FF00',  # MT4 Lime Green Bull
            increasing_fillcolor='#00FF00',
            decreasing_line_color='#FF0000',  # MT4 Red Bear
            decreasing_fillcolor='#FF0000',
            name="Price"
        )
    ])

    # 2. Add Trade Annotations (Entry Arrow, SL & TP Lines)
    entry_time = trade_info['entry_time']
    entry_price = trade_info['entry_price']
    trade_type = trade_info['type']  # 'BUY' or 'SELL'
    sl_price = trade_info['sl']
    tp_price = trade_info['tp']

    arrow_color = '#00FF00' if trade_type == 'BUY' else '#FF0000'
    arrow_symbol = 'triangle-up' if trade_type == 'BUY' else 'triangle-down'

    # Entry Marker Arrow
    fig.add_trace(go.Scatter(
        x=[entry_time],
        y=[entry_price],
        mode='markers+text',
        marker=dict(symbol=arrow_symbol, size=16, color=arrow_color),
        text=[f"  {trade_type} @ {entry_price:.3f}"],
        textposition="middle right",
        textfont=dict(color="#FFFFFF", size=12),
        name="Entry Point"
    ))

    # Dotted SL Line (Red)
    fig.add_hline(
        y=sl_price,
        line_dash="dot",
        line_color="#FF4444",
        line_width=1.5,
        annotation_text=f"SL: {sl_price:.3f}",
        annotation_position="bottom right",
        annotation_font=dict(color="#FF4444", size=11)
    )

    # Dotted TP Line (Green)
    fig.add_hline(
        y=tp_price,
        line_dash="dot",
        line_color="#00FF00",
        line_width=1.5,
        annotation_text=f"TP: {tp_price:.3f}",
        annotation_position="top right",
        annotation_font=dict(color="#00FF00", size=11)
    )

    # 3. Apply Pitch-Black MT4 Terminal Layout Styling
    symbol_name = trade_info.get('pair', 'AUDJPYmicro').replace('=X', '')
    tf_name = trade_info.get('timeframe', 'M15')
    last_close = df['Close'].iloc[-1]
    last_open = df['Open'].iloc[-1]
    last_high = df['High'].iloc[-1]
    last_low = df['Low'].iloc[-1]

    header_text = f"{symbol_name},{tf_name}  {last_open:.3f} {last_high:.3f} {last_low:.3f} {last_close:.3f}"

    fig.update_layout(
        title=dict(
            text=header_text,
            font=dict(color="#FFFFFF", size=13, family="Consolas, monospace"),
            x=0.01,
            y=0.98
        ),
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        margin=dict(l=20, r=60, t=30, b=30),
        xaxis=dict(
            showgrid=True,
            gridcolor='#1A1A1A',
            gridwidth=1,
            tickfont=dict(color='#AAAAAA', size=10),
            type='date'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#1A1A1A',
            gridwidth=1,
            tickfont=dict(color='#AAAAAA', size=10),
            side='right'
        ),
        showlegend=False,
        width=1920,
        height=824
    )

    # Save to disk
    filename = f"{output_dir}/trade_{trade_info['id']}_{symbol_name}.png"
    fig.write_image(filename)
    return filename

def auto_cleanup_old_snapshots(output_dir="trade_snapshots", max_days=30):
    """
    Deletes snapshot PNG files older than 30 days to save cloud space.
    """
    now = datetime.now()
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isfile(file_path) and filename.endswith('.png'):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if now - file_time > timedelta(days=max_days):
                    os.remove(file_path)
