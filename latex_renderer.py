import matplotlib.pyplot as plt
from io import BytesIO
import matplotlib
matplotlib.use("Agg")

def render_latex_image(latex_expr: str) -> BytesIO:
    fig, ax = plt.subplots(figsize=(6, 1.5))  # увеличенный размер
    fig.patch.set_visible(False)
    ax.axis("off")
    ax.text(0.5, 0.5, f"${latex_expr}$", fontsize=20, ha='center', va='center')
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.5, dpi=300, transparent=True)
    buf.seek(0)
    plt.close(fig)
    return buf
