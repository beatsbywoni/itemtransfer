"""Figure 1: schematic of leave-one-family-out transfer validation."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
fig, ax = plt.subplots(figsize=(7.4, 3.9))
ax.set_xlim(0, 100); ax.set_ylim(0, 54); ax.axis("off")

def box(x, y, w, h, text, fc="white", fs=7.5, bold=False, ec="k"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=fc, ec=ec, lw=0.9))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")

def arrow(x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=9, lw=0.9, color="k"))

ax.text(11, 51.5, "Item families", ha="center", fontsize=8.5, fontweight="bold")
box(1, 38.5, 20, 9.5, "Family A\nitems, responses,\nvalues of the measure", fc="0.90")
box(1, 27, 20, 9.5, "Family B\nitems, responses,\nvalues of the measure", fc="0.90")
box(1, 10, 20, 8.5, "Family C\n(held out)", fc="white")
ax.text(11, 23.5, "training families", ha="center", fontsize=7, style="italic")
ax.text(11, 7.3, "each family is held out in turn", ha="center", fontsize=6.5, style="italic")

box(29, 31, 22, 12, "Fit on training families\nlogit P(correct) =\n$a_{sample}$ + $b$ × measure", fs=7.5)
arrow(21.6, 43, 28.6, 39.5); arrow(21.6, 32, 28.6, 35)
box(29, 8, 22, 11, "Transferred predictor\n$b$ × measure\nfor each held-out item", fs=7.5)
arrow(40, 30.6, 40, 19.6); arrow(21.6, 14, 28.6, 14)

ax.text(69, 51.5, "Three criteria on the held-out family", ha="center", fontsize=8.5, fontweight="bold")
box(58, 38, 22, 9.5, "Ordering\nAre the items ranked\ncorrectly?", fc="0.96")
box(58, 25.5, 22, 9.5, "Scale\nIs the effect as large\nas trained?", fc="0.96")
box(58, 13, 22, 9.5, "Prediction\nAre single responses\npredicted better?", fc="0.96")
for y in (42.7, 30.2, 17.7):
    arrow(51.6, 13.5 if y < 20 else 15.5, 57.6, y)
ax.text(90.5, 42.7, "rank correlation\nwith item accuracy", ha="center", va="center", fontsize=6.8)
ax.text(90.5, 30.2, "calibration slope\n(1 = same size)", ha="center", va="center", fontsize=6.8)
ax.text(90.5, 17.7, "reduction in log loss\n(intercept re-estimated)", ha="center", va="center", fontsize=6.8)

box(1, 0.3, 98, 4.2, "Read against:  reliability ceiling (step 2)   ·   design diagnostics (step 4)   ·   bootstrap intervals and simulation check (step 5)", fs=6.8, fc="white", ec="0.5")
for ext in ("png", "pdf"):
    fig.savefig(HERE / f"figure_schematic.{ext}", dpi=300, bbox_inches="tight")
