import streamlit as st
import os
import base64
import io
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

_static = os.path.join(os.path.dirname(__file__), "..", "static")

def get_transparent_logo_b64(logo_path: str) -> str:
    """读取带有深色背景的 Logo，将其转换为带透明通道 (Alpha) 的纯白 Logo"""
    img = Image.open(logo_path).convert("RGB")
    data = img.getdata()
    
    # 假设左上角第一个像素是纯背景色
    bg_r, bg_g, bg_b = data[0]
    
    new_data = []
    for item in data:
        # 如果像素颜色接近背景色，则使其透明
        if abs(item[0] - bg_r) < 30 and abs(item[1] - bg_g) < 30 and abs(item[2] - bg_b) < 30:
            new_data.append((255, 255, 255, 0))
        else:
            # 否则将其转换为白色（原图字是白的，其他边缘也变白）
            new_data.append((255, 255, 255, 255))
            
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

    html = html.replace("mix-blend-mode: screen !important;", "")
    html = html.replace("filter: none !important;", "")
    
    if HAS_PIL:
        try:
            b64 = get_transparent_logo_b64(logo_path)
            html = html.replace('src="IBI_Logo_Dark.png"', f'src="data:image/png;base64,{b64}"')
        except Exception:
            pass
    return html

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
[data-testid="stHeaderActionElements"] {visibility: hidden;}
header {background: transparent !important;}
footer {visibility: hidden;}

[data-testid="stTooltipIcon"] {
    display: none !important;
}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0rem !important;
}
</style>
""", unsafe_allow_html=True)

st.components.v1.html(load_html("gas-calculator.html"), height=1050, scrolling=True)
