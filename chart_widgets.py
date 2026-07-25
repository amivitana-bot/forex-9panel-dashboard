import plotly.graph_objects as go
import pandas as pd

def render_panel_chart(df, pred_fast, pred_slow, title, show_crosshair=False):
    fig = go.Figure()

    # 1. Main Candlesticks
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350',
        showlegend=False
    ))

    # 2. Add Cyan & Yellow Forecast Rays
    if pred_fast is not None and pred_slow is not None:
        last_time = df.index[-1]
        last_close = float(df['Close'].iloc[-1])
        step = df.index[-1] - df.index[-2] if len(df) > 1 else pd.Timedelta(minutes=15)

        t1 = last_time + step
        t2 = last_time + (step * 3)

        # Fast Ray (Cyan)
        fig.add_trace(go.Scatter(
            x=[last_time, t1, t2],
            y=[last_close, pred_fast, pred_fast],
            mode='lines+markers',
            line=dict(color='#00E5FF', width=2, dash='dot'),
            marker=dict(size=4, color='#00E5FF'),
            showlegend=False
        ))

        # Slow Ray (Yellow)
        fig.add_trace(go.Scatter(
            x=[last_time, t1, t2],
            y=[last_close, pred_slow, pred_slow],
            mode='lines',
            line=dict(color='#FFEA00', width=2, dash='dash'),
            showlegend=False
        ))

    # Slim, Sleek Crosshairs
    spike_kwargs = dict(
        showspikes=show_crosshair,
        spikemode='across',
        spikesnap='cursor',
        spikecolor='#777777',
        spikethickness=1,
        spikedash='dot'
    )

    fig.update_layout(
        title=dict(text=title, font=dict(color='#FFFFFF', size=11), x=0.02, y=0.95),
        paper_bgcolor='#111111',
        plot_bgcolor='#111111',
        margin=dict(l=10, r=35, t=25, b=15),
        height=180,
        xaxis=dict(
            showgrid=True, gridcolor='#222222',
            tickfont=dict(color='#888888', size=9),
            **spike_kwargs
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#222222',
            tickfont=dict(color='#888888', size=9),
            side='right',
            **spike_kwargs
        ),
        showlegend=False
    )
    return fig


def render_mt4_structure_chart(df, struct_info, show_crosshair=False):
    fig = go.Figure(data=[
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='#00FF00',  # MT4 Lime
            increasing_fillcolor='#00FF00',
            decreasing_line_color='#FF0000',  # MT4 Red
            decreasing_fillcolor='#FF0000',
            showlegend=False
        )
    ])

    # Add EMAs
    if 'EMA_6' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_6'], line=dict(color='#00FFFF', width=1), name='EMA 6'))
    if 'EMA_18' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_18'], line=dict(color='#FF00FF', width=1), name='EMA 18'))
    if 'EMA_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#FFFF00', width=1.2), name='EMA 50'))

    # Slim Crosshairs for Main Chart
    spike_kwargs = dict(
        showspikes=show_crosshair,
        spikemode='across',
        spikesnap='cursor',
        spikecolor='#AAAAAA',
        spikethickness=1,
        spikedash='dot'
    )

    fig.update_layout(
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        margin=dict(l=15, r=45, t=15, b=20),
        height=400,
        xaxis=dict(
            showgrid=True, gridcolor='#1A1A1A',
            tickfont=dict(color='#888888', size=10),
            **spike_kwargs
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#1A1A1A',
            tickfont=dict(color='#888888', size=10),
            side='right',
            **spike_kwargs
        ),
        showlegend=False
    )
    return fig
