import plotly.graph_objects as go
import numpy as np

def render_panel_chart(df, pred_fast, pred_slow, title, show_crosshair=False, structure_info=None):
    """
    Renders interactive Plotly chart with Adam Koo's Market Structure & EMAs.
    """
    fig = go.Figure()

    hover_mode_setting = "x" if show_crosshair else False

    # 1. Price Candlesticks/Line
    fig.add_trace(go.Scatter(
        x=list(range(len(df))),
        y=df['Close'],
        mode='lines',
        name='Price',
        line=dict(color='#FFFFFF', width=1.2),
        hoverinfo='all' if show_crosshair else 'skip',
        hovertemplate='Candle: %{x}<br>Price: %{y:.5f}<extra></extra>' if show_crosshair else None
    ))

    # 2. Overlay EMAs (Adam Koo Stack)
    if structure_info and 'df' in structure_info:
        s_df = structure_info['df']
        fig.add_trace(go.Scatter(x=list(range(len(s_df))), y=s_df['EMA_18'], mode='lines',
                                 name='18 EMA', line=dict(color='#00BFFF', width=1), hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=list(range(len(s_df))), y=s_df['EMA_50'], mode='lines',
                                 name='50 EMA', line=dict(color='#FFD700', width=1.2), hoverinfo='skip'))

    # 3. Market Structure ZigZag overlay
    if structure_info and 'high_idx' in structure_info:
        h_idx = structure_info['high_idx']
        l_idx = structure_info['low_idx']
        
        # Combine and sort high/low points chronologically
        p_indices = sorted(list(set(np.concatenate([h_idx, l_idx]))))
        if p_indices:
            p_x = p_indices
            p_y = [df['Close'].iloc[i] for i in p_indices]
            
            fig.add_trace(go.Scatter(
                x=p_x, y=p_y,
                mode='lines+markers',
                name='Structure',
                line=dict(color=structure_info['color'], width=1.5, dash='dot'),
                marker=dict(size=4, color=structure_info['color']),
                hoverinfo='skip'
            ))

    # Forecast coordinates
    full_fast = np.insert(pred_fast, 0, df['Close'].iloc[-1])
    full_slow = np.insert(pred_slow, 0, df['Close'].iloc[-1])
    future_x = list(range(len(df) - 1, len(df) + len(pred_fast)))

    # Fast & Slow Forecast Lines
    fig.add_trace(go.Scatter(x=future_x, y=full_fast, mode='lines', line=dict(color='#FFD700', width=2), hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=future_x, y=full_slow, mode='lines', line=dict(color='#00BFFF', width=2, dash='dash'), hoverinfo='skip'))

    # Layout Config
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=12, color="white"), y=0.95),
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        margin=dict(l=5, r=5, t=25, b=5),
        height=180,
        showlegend=False,
        hovermode=hover_mode_setting,
    )

    fig.update_xaxes(showgrid=True, gridcolor='#222222', showticklabels=False, showspikes=show_crosshair, spikemode='across', spikesnap='cursor')
    fig.update_yaxes(showgrid=True, gridcolor='#222222', tickfont=dict(color='#888888', size=8), side="right", showspikes=show_crosshair, spikemode='across', spikesnap='cursor')

    return fig
