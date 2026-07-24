import plotly.graph_objects as go
import numpy as np
from config_settings import COLOR_FAST_SPIKE, COLOR_SLOW_SMOOTH, COLOR_HISTORICAL, COLOR_BG

def render_panel_chart(df, pred_fast, pred_slow, title, show_crosshair=False):
    """
    Renders standard 9-panel forecast chart (UNTOUCHED).
    """
    fig = go.Figure()
    hover_mode_setting = "x" if show_crosshair else False

    # Historical Prices
    fig.add_trace(go.Scatter(
        x=list(range(len(df))), y=df['Close'], mode='lines', name='History',
        line=dict(color=COLOR_HISTORICAL, width=1.2),
        hoverinfo='all' if show_crosshair else 'skip',
        hovertemplate='Candle: %{x}<br>Price: %{y:.5f}<extra></extra>' if show_crosshair else None
    ))

    # Forecast coordinates
    full_fast = np.insert(pred_fast, 0, df['Close'].iloc[-1])
    full_slow = np.insert(pred_slow, 0, df['Close'].iloc[-1])
    future_x = list(range(len(df) - 1, len(df) + len(pred_fast)))

    # Fast & Slow Forecast Lines
    fig.add_trace(go.Scatter(x=future_x, y=full_fast, mode='lines', line=dict(color=COLOR_FAST_SPIKE, width=2), hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=future_x, y=full_slow, mode='lines', line=dict(color=COLOR_SLOW_SMOOTH, width=2, dash='dash'), hoverinfo='skip'))

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=11, color="white"), y=0.95),
        paper_bgcolor=COLOR_BG, plot_bgcolor=COLOR_BG,
        margin=dict(l=5, r=5, t=22, b=5), height=160, showlegend=False,
        hovermode=hover_mode_setting,
    )

    fig.update_xaxes(showgrid=True, gridcolor='#222222', showticklabels=False, showspikes=show_crosshair, spikemode='across', spikesnap='cursor')
    fig.update_yaxes(showgrid=True, gridcolor='#222222', tickfont=dict(color='#888888', size=8), side="right", showspikes=show_crosshair, spikemode='across', spikesnap='cursor')

    return fig

def render_mt4_structure_chart(df, struct_info, show_crosshair=False):
    """
    Renders dedicated MT4-style structure chart on the right side.
    Displays Adam Koo's EMAs (6, 18, 50, 200) + HH/HL ZigZag lines.
    """
    fig = go.Figure()
    hover_mode_setting = "x" if show_crosshair else False

    # 1. Price Candlesticks
    fig.add_trace(go.Candlestick(
        x=list(range(len(df))),
        open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='Price'
    ))

    # 2. Adam Koo EMAs Overlay
    s_df = struct_info['df']
    fig.add_trace(go.Scatter(x=list(range(len(s_df))), y=s_df['EMA_6'], mode='lines', name='6 EMA', line=dict(color='#FF3333', width=1)))
    fig.add_trace(go.Scatter(x=list(range(len(s_df))), y=s_df['EMA_18'], mode='lines', name='18 EMA', line=dict(color='#00BFFF', width=1.2)))
    fig.add_trace(go.Scatter(x=list(range(len(s_df))), y=s_df['EMA_50'], mode='lines', name='50 EMA', line=dict(color='#FFD700', width=1.5)))
    fig.add_trace(go.Scatter(x=list(range(len(s_df))), y=s_df['SMA_200'], mode='lines', name='200 SMA', line=dict(color='#FFFFFF', width=1.5, dash='dot')))

    # 3. Market Structure ZigZag overlay
    h_idx = struct_info['high_idx']
    l_idx = struct_info['low_idx']
    p_indices = sorted(list(set(np.concatenate([h_idx, l_idx]))))
    
    if p_indices:
        p_x = p_indices
        p_y = [df['Close'].iloc[i] for i in p_indices]
        fig.add_trace(go.Scatter(
            x=p_x, y=p_y, mode='lines+markers', name='Structure',
            line=dict(color=struct_info['color'], width=2),
            marker=dict(size=5, color=struct_info['color']),
        ))

    fig.update_layout(
        paper_bgcolor=COLOR_BG, plot_bgcolor=COLOR_BG,
        margin=dict(l=5, r=5, t=10, b=5), height=510,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1, font=dict(size=9, color="white")),
        xaxis_rangeslider_visible=False,
        hovermode=hover_mode_setting,
    )

    fig.update_xaxes(showgrid=True, gridcolor='#222222', showticklabels=False, showspikes=show_crosshair)
    fig.update_yaxes(showgrid=True, gridcolor='#222222', tickfont=dict(color='#888888', size=8), side="right", showspikes=show_crosshair)

    return fig
