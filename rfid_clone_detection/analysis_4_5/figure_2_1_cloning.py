"""Figure 1 (section 2.1): UID-only identification accepts both the genuine and the cloned tag."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

INK, INK2, BOX = "#0b0b0b", "#52514e", "#f1f0ec"
GOOD, CRIT = "#0ca30c", "#d03b3b"
plt.rcParams["font.family"] = "DejaVu Sans"

fig, ax = plt.subplots(figsize=(8.0, 3.3))
ax.set_xlim(0, 11.9); ax.set_ylim(0, 4.4); ax.axis("off")


def box(x, y, w, h, text, edge=INK2, face=BOX, ls="-", color=INK, weight="normal", size=8.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                linewidth=1.2, edgecolor=edge, facecolor=face, linestyle=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=color,
            fontsize=size, fontweight=weight, linespacing=1.35)


def arrow(p, q, color=INK2, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12, linewidth=1.3,
                                 color=color, linestyle=ls, shrinkA=2, shrinkB=2))


box(0.1, 3.2, 2.6, 0.95, "Thẻ hợp lệ\nUID = X", weight="bold")
box(0.1, 1.75, 2.6, 0.95, "Kẻ tấn công đọc lén\nUID, ghi lên thẻ trắng\nhoặc thiết bị giả lập", ls="--", face="white", color=INK2, size=7.8)
box(0.1, 0.3, 2.6, 0.95, "Thẻ nhân bản\nUID = X (sao chép)", weight="bold")
arrow((1.4, 3.2), (1.4, 2.7), ls="--"); arrow((1.4, 1.75), (1.4, 1.25), ls="--")

box(3.5, 0.85, 2.7, 2.75, "Reader tại\nđiểm kiểm soát\n(ESP32-MFRC522)\n\nChỉ kiểm tra UID\ncó trong CSDL?", size=8.5)
arrow((2.7, 3.67), (3.5, 3.2)); arrow((2.7, 0.77), (3.5, 1.25))

box(7.0, 3.2, 2.0, 0.95, "✓ Chấp nhận\nhàng thật", edge=GOOD, face="white", size=8.5)
box(7.0, 0.3, 2.0, 0.95, "✓ Chấp nhận thẻ\nnhân bản như\nhàng thật", edge=GOOD, face="white", size=8)
arrow((6.2, 3.2), (7.0, 3.67)); arrow((6.2, 1.25), (7.0, 0.77))

box(9.4, 0.12, 2.4, 1.31, "⚠ Vi phạm an ninh\nmạo danh định danh\nsai lệch tồn kho\ntruy vết mâu thuẫn",
    edge=CRIT, face="white", size=7.8)
arrow((9.0, 0.77), (9.4, 0.77), color=CRIT)

out = sys.argv[1] if len(sys.argv) > 1 else "figure1_cloning"
fig.savefig(out + ".png", dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(out + ".pdf", bbox_inches="tight", facecolor="white")
print("saved", out + ".png/.pdf")
