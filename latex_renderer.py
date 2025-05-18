import matplotlib.pyplot as plt
from io import BytesIO

def render_latex_image(latex_expr: str) -> BytesIO:
    fig, ax = plt.subplots(figsize=(0.1, 0.1))
    fig.patch.set_visible(False)
    ax.axis("off")
    ax.text(0.5, 0.5, f"${latex_expr}$", fontsize=20, ha='center', va='center')
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.3, dpi=200, transparent=True)
    buf.seek(0)
    plt.close(fig)
    return buf