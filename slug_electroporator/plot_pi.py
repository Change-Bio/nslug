import matplotlib.pyplot as plt
import numpy as np

# Small figure + large base font = big text relative to plot
plt.rcParams.update({
    "font.size": 14,
    "font.weight": "bold",
    "axes.labelweight": "bold",
    "axes.linewidth": 1.5,
})

# Data
controls = {
    "PI\nonly":  [4622, 4620],
    "no PI":    [491, 471, 484],
    "+ PI":     [12490, 13571, 12742],
    "no PI ":   [620, 592, 607],
    "+ PI ":    [29936, 26370, 28849],
}

voltages = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5]
row_b = [14651, 13943, 14274, 14611, 14794, 14645, 11664]
row_c = [11998, 14863, 15664, 13405, 13784, 15649, 11509]

# Positions: controls with gaps for group labels
# 0=PI only, gap, 1.5="Alive", 2.5=no PI, 3.5=+PI, gap, 5="Dead", 6=no PI, 7=+PI, gap, 9=sep, 10="kV", 11-17=voltages
x_ctrl = [0, 2.5, 3.5, 6, 7]
x_group = [1.5, 5, 10]  # Alive, Dead, kV label positions
x_volt = [11, 12, 13, 14, 15, 16, 17]

fig, ax = plt.subplots(figsize=(6, 3.5))

# Controls
ctrl_colors = ["#999999", "#4daf4a", "#4daf4a", "#e41a1c", "#e41a1c"]
for i, (name, vals) in enumerate(controls.items()):
    jitter = np.random.default_rng(42 + i).uniform(-0.12, 0.12, len(vals))
    ax.scatter(x_ctrl[i] + jitter, vals, color=ctrl_colors[i], s=60, zorder=3, alpha=0.7)
    m = np.mean(vals)
    ax.hlines(m, x_ctrl[i] - 0.3, x_ctrl[i] + 0.3, color=ctrl_colors[i], linewidth=2.5, zorder=4)

# Voltage series
for i in range(len(voltages)):
    vals = [row_b[i], row_c[i]]
    jitter = np.random.default_rng(99 + i).uniform(-0.12, 0.12, len(vals))
    ax.scatter(x_volt[i] + jitter, vals, color="#377eb8", s=60, zorder=3, alpha=0.7)
    m = np.mean(vals)
    ax.hlines(m, x_volt[i] - 0.3, x_volt[i] + 0.3, color="#377eb8", linewidth=2.5, zorder=4)

# All tick positions and labels
all_x = [x_ctrl[0]] + [x_group[0]] + x_ctrl[1:3] + [x_group[1]] + x_ctrl[3:5] + [x_group[2]] + x_volt
all_labels = ["PI\nonly", "Alive", "no PI", "+ PI", "Dead", "no PI", "+ PI", "kV"] + [f"{v:.1f}" for v in voltages]

ax.set_xticks(all_x)
ax.set_xticklabels(all_labels, fontsize=12, fontweight="bold")

# Color the group labels
tick_labels = ax.get_xticklabels()
group_label_colors = {1: "#4daf4a", 4: "#e41a1c", 7: "#377eb8"}  # indices of Alive, Dead, kV
for idx, color in group_label_colors.items():
    tick_labels[idx].set_color(color)
    tick_labels[idx].set_fontsize(14)

# Separator
sep = 8.5
ax.axvline(sep, color="grey", ls=":", alpha=0.4, lw=1.5)

ax.set_ylabel("Fluorescence (AU)", fontsize=14)
ax.set_ylim(0)
ax.tick_params(axis="y", labelsize=12)

fig.tight_layout()
fig.savefig("/home/noah/src/nslug/slug_electroporator/pi_electroporation_plot.png", dpi=200)
plt.show()
print("Saved to pi_electroporation_plot.png")
