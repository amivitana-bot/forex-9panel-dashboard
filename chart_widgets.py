import plotly.graph_objects as go
import numpy as np
from config_settings import COLOR_FAST_SPIKE, COLOR_SLOW_SMOOTH, COLOR_HISTORICAL, COLOR_BG

def render_panel_chart(df, pred_fast, pred_slow, title):
    """
    Renders an interactive Plotly chart with crosshairs and exact hover numbers.
    """
    fig = go.Figure()

    # 1. Historical Prices
    fig.add_trace(go.Scatter(
        x=list(range(len(df))),
        y=df['Close'],
        mode='lines',
        name='History',
        line=dict(color=COLOR_HISTORICAL, width=1.2),
        hovertemplate='Index: %{x}<br>Price: %{y:.5f}<extra></extra>'
    ))

    # Forecast coordinates
    full_fast = np.insert(pred_fast, 0, df['Close'].iloc[-1])
    full_slow = np.insert(pred_slow, 0, df['Close'].iloc[-1])
    future_x = list(range(len(df) - 1, len(df) + len(pred_fast)))

    # 2. Fast Yellow Spike Line
    fig.add_trace(go.Scatter(
        x=future_x,
        y=full_fast,
        mode='lines',
        name='Fast Spike',
        line=dict(color=COLOR_FAST_SPIKE, width=2),
        hovertemplate='Fast Pred: %{y:.5f}<extra></extra>'
    ))

    # 3. Slow Blue Smooth Line
    fig.add_trace(go.Scatter(
        x=future_x,
        y=full_slow,
        mode='lines',
        name='Slow Trend',
        line=dict(color=COLOR_SLOW_SMOOTH, width=2, dash='dash'),
        hovertemplate='Slow Pred: %{y:.5f}<extra></extra>'
    ))

    # 4. Interactive Layout Settings with Crosshair Cursor
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=12, color="white"), y=0.95),
        paper_bgcolor=COLOR_BG,
        plot_bgcolor=COLOR_BG,
        margin=dict(l=5, r=5, t=25, b=5),
        height=180,
        showlegend=False,
        hovermode="x unified",  # Displays exact prices across lines on hover
        xaxis=dict(
            showgrid=True, gridcolor='#222222',
            showticklabels=False,
            spikethickness=1, spikedash='dot', spikecolor='#888888', spikemode='across' # Vertical crosshair line
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#222222',
            tickfont=dict(color='#888888', size=8),
            side="right",
            spikethickness=1, spikedash='dot', spikecolor='#888888', spikemode='across' # Horizontal crosshair line
        )
    )

    return fig
