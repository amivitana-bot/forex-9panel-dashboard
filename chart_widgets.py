import matplotlib.pyplot as plt
import numpy as np
from config_settings import COLOR_FAST_SPIKE, COLOR_SLOW_SMOOTH, COLOR_HISTORICAL, COLOR_BG

def render_panel_chart(df, pred_fast, pred_slow, title):
    """
    Renders an individual indicator forecast panel in an ultra-compact
    layout (very wide, very short) to ensure all 3 rows fit one screen.
    """
    # ULTRA COMPACT SIZE: Ratio adjusted for 3x3 stacking
    fig, ax = plt.subplots(figsize=(4.0, 1.2), facecolor=COLOR_BG)
    ax.set_facecolor(COLOR_BG)
    
    # Historical Prices
    ax.plot(range(len(df)), df['Close'], color=COLOR_HISTORICAL, linewidth=1.0)
    
    # Complete forecast lines starting from the last historical point
    full_fast = np.insert(pred_fast, 0, df['Close'].iloc[-1])
    full_slow = np.insert(pred_slow, 0, df['Close'].iloc[-1])
    future_x = range(len(df) - 1, len(df) + len(pred_fast))
    
    # Yellow Spike Line (Thinner)
    ax.plot(future_x, full_fast, color=COLOR_FAST_SPIKE, linewidth=1.5)
    
    # Blue Smooth Line (Thinner)
    ax.plot(future_x, full_slow, color=COLOR_SLOW_SMOOTH, linewidth=1.8, linestyle="--")
    
    # ULTRA COMPACT TEXT AND GRIDS
    ax.set_title(title, fontsize=7, fontweight='bold', color='#FFFFFF', pad=2)
    ax.grid(True, linestyle=':', alpha=0.1, color='#FFFFFF')
    
    # Shrink and dim the ticks
    ax.tick_params(colors='#666666', labelsize=5, length=1, pad=1)
    
    # Hide top and right spines completely for a cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    
    # Reduce whitespace around the plot within the figure
    plt.subplots_adjust(left=0.08, bottom=0.1, right=0.98, top=0.85, wspace=0, hspace=0)
    
    return fig
