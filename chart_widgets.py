import matplotlib.pyplot as plt
import numpy as np
from config_settings import COLOR_FAST_SPIKE, COLOR_SLOW_SMOOTH, COLOR_HISTORICAL, COLOR_BG

def render_panel_chart(df, pred_fast, pred_slow, title):
    """
    Renders an individual indicator forecast panel in dark mode.
    """
    fig, ax = plt.subplots(figsize=(4.5, 3.2), facecolor=COLOR_BG)
    ax.set_facecolor(COLOR_BG)
    
    # Historical Prices
    ax.plot(range(len(df)), df['Close'], color=COLOR_HISTORICAL, linewidth=1.2, label="History")
    
    # Build complete forecast lines starting from the last historical point
    full_fast = np.insert(pred_fast, 0, df['Close'].iloc[-1])
    full_slow = np.insert(pred_slow, 0, df['Close'].iloc[-1])
    
    # Future x-coordinates matching full_fast & full_slow length
    future_x = range(len(df) - 1, len(df) + len(pred_fast))
    
    # Yellow Spike Line
    ax.plot(future_x, full_fast, color=COLOR_FAST_SPIKE, linewidth=2.2, label="Spike (Fast)")
    
    # Blue Smooth Line
    ax.plot(future_x, full_slow, color=COLOR_SLOW_SMOOTH, linewidth=2.5, linestyle="--", label="Smooth (Trend)")
    
    ax.set_title(title, fontsize=10, fontweight='bold', color='#FFFFFF', pad=8)
    ax.grid(True, linestyle=':', alpha=0.2, color='#FFFFFF')
    ax.tick_params(colors='#888888', labelsize=8)
    for spine in ax.spines.values():
        spine.set_color('#333333')
        
    plt.tight_layout()
    return fig
