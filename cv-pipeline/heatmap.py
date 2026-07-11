import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap

COURT_W = 10.0   # metres
COURT_L = 20.0   # metres

# Purple-to-yellow heatmap (visible on white court)
CMAP = LinearSegmentedColormap.from_list(
    "padel",
    ["#ffffff00", "#7c3aed55", "#7c3aedaa", "#f59e0bdd", "#ef4444ff"],
)


def _draw_court(ax):
    court = patches.Rectangle((0, 0), COURT_W, COURT_L, linewidth=2, edgecolor="#1a1a2e", facecolor="#e8f5e9")
    ax.add_patch(court)
    # Net
    ax.plot([0, COURT_W], [10, 10], color="#1a1a2e", linewidth=2)
    # Service lines
    ax.plot([0, COURT_W], [3, 3],  color="#374151", linewidth=1)
    ax.plot([0, COURT_W], [17, 17], color="#374151", linewidth=1)
    # Centre lines
    ax.plot([COURT_W/2, COURT_W/2], [3, 10],  color="#374151", linewidth=1)
    ax.plot([COURT_W/2, COURT_W/2], [10, 17], color="#374151", linewidth=1)
    ax.set_xlim(-0.5, COURT_W + 0.5)
    ax.set_ylim(-0.5, COURT_L + 0.5)
    ax.set_aspect("equal")
    ax.axis("off")


def generate(positions: list[tuple[float, float]], player_name: str = "") -> bytes:
    """
    positions: list of (court_x, court_y) in metres.
    Returns PNG bytes.
    """
    fig, ax = plt.subplots(figsize=(4, 8), dpi=120)
    fig.patch.set_facecolor("#f8fafc")
    _draw_court(ax)

    if positions:
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        ax.hexbin(xs, ys, gridsize=20, cmap=CMAP, extent=(0, COURT_W, 0, COURT_L),
                  mincnt=1, linewidths=0.2, alpha=0.85)

    if player_name:
        ax.set_title(player_name, fontsize=11, pad=6, color="#1a1a2e", fontweight="bold")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf.read()
