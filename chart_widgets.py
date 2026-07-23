import matplotlib.pyplot as plt
import numpy as np
from config_settings import COLOR_FAST_SPIKE, COLOR_SLOW_SMOOTH, COLOR_HISTORICAL, COLOR_BG

def render_panel_chart(df, pred_fast, pred_slow, title):
    """
    Renders an individual indicator forecast panel in proper aspect ratio.
    """
   fig, ax = plt.subplots(figsize=(4.0, 1.6), facecolor=COLOR_BG)
    ax.set_facecolor(COLOR_BG)
    
    # Historical Prices
    ax.plot(range(len(df)), df['Close'], color=COLOR_HISTORICAL, linewidth=1.1)
    
    # Complete forecast lines starting from the last historical point
    full_fast = np.insert(pred_fast, 0, df['Close'].iloc[-1])
    full_slow = np.insert(pred_slow, 0, df['Close'].iloc[-1])
    future_x = range(len(df) - 1, len(df) + len(pred_fast))
    
    # Yellow Spike Line
    ax.plot(future_x, full_fast, color=COLOR_FAST_SPIKE, linewidth=1.8)
    
    # Blue Smooth Line
    ax.plot(future_x, full_slow, color=COLOR_SLOW_SMOOTH, linewidth=2.0, linestyle="--")
    
    ax.set_title(title, fontsize=9, fontweight='bold', color='#FFFFFF', pad=3)
    ax.grid(True, linestyle=':', alpha=0.15, color='#FFFFFF')
    
    ax.tick_params(colors='#777777', labelsize=7, pad=1)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    
    plt.tight_layout(pad=0.5)
    return fig
