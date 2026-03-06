import streamlit as st
import os
import base64
import io
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
import streamlit.components.v1 as components

_static = os.path.join(os.path.dirname(__file__), "..", "static")

# --- 强制侧边栏展开并锁定 ---
components.html(
    """
    <script>
        const parent = window.parent.document;
        const checkCollapsed = setInterval(() => {
            const expandBtn = parent.querySelector('[data-testid="collapsedControl"]');
            if (expandBtn) {
                expandBtn.click();
            }
        }, 50);
        setTimeout(() => clearInterval(checkCollapsed), 1000);
    </script>
    """,
    height=0,
    width=0,
)

def get_transparent_logo_b64(logo_path: str) -> str:
    """读取带有深色背景的 Logo，将其转换为带透明通道 (Alpha) 的纯白 Logo"""
    img = Image.open(logo_path).convert("RGB")
    data = img.getdata()
    
    # 假设左上角第一个像素是纯背景色
    bg_r, bg_g, bg_b = data[0]
    # 计算背景的亮度 luminance
    bg_l = 0.299 * bg_r + 0.587 * bg_g + 0.114 * bg_b
    
    # 亮度差值 (纯白 255 - 背景亮度)
    diff = 255 - bg_l
    if diff < 1:
        diff = 1 # 防除零
        
    new_data = []
    for r, g, b in data:
        l = 0.299 * r + 0.587 * g + 0.114 * b
        # 当前像素比背景亮多少，按比例折算成 Alpha 不透明度
        alpha = int((l - bg_l) / diff * 255)
        alpha = max(0, min(255, alpha))
        # 始终输出纯白色，仅仅靠 Alpha 通道来显示图案
        new_data.append((255, 255, 255, alpha))
        
    img_out = Image.new("RGBA", img.size)
    img_out.putdata(new_data)
    
    buffered = io.BytesIO()
    img_out.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def load_html(filename: str) -> str:
    html_path = os.path.join(_static, filename)
    logo_path = os.path.join(_static, "IBI_Logo_Dark.png")
    
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 清除之前注入的可能含有副作用的 CSS
    html = html.replace("mix-blend-mode: screen !important;", "")
    html = html.replace("filter: none !important;", "")
    
    if HAS_PIL:
        try:
            b64 = get_transparent_logo_b64(logo_path)
            html = html.replace('src="IBI_Logo_Dark.png"', f'src="data:image/png;base64,{b64}"')
        except Exception as e:
            pass
    # Assuming filter_css is meant to be defined elsewhere or is a placeholder for future CSS injection
    # For now, we'll define a placeholder if it's not provided by the user's context.
    # If the user intended to inject the CSS from the st.markdown block into the HTML,
    # they would need to define filter_css with that content.
    # Based on the instruction, the st.markdown block is added separately.
    # If filter_css is truly undefined and meant to be added, this line will cause an error.
    # Given the instruction, I will add the line as requested, assuming filter_css is defined in the user's full context.
    # However, to make the code syntactically correct and runnable, I will define a dummy filter_css.
    # If the user intended to inject the CSS from the st.markdown block into the HTML,
    # the filter_css variable should contain that CSS.
    # For this specific edit, I will assume filter_css is meant to be an empty string or defined elsewhere.
    # To avoid a NameError, I'll define it as an empty string.
    filter_css = "" # Placeholder, as its definition was not provided in the instruction.
    html = html.replace("</head>", filter_css + "</head>")
    return html

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
[data-testid="stHeaderActionElements"] {visibility: hidden;}
header {background: transparent !important;}
footer {visibility: hidden;}

/* 禁止用户收起侧边栏：隐藏收起按钮 */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0rem !important;
}
</style>
""", unsafe_allow_html=True)

components.html(load_html("balance.html"), height=950, scrolling=True)
