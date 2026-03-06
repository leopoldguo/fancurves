import streamlit as st

# ============================================================
# 主入口：使用 st.navigation() 显式注册所有页面
# 这是 Streamlit 1.36+ 推荐的多页面方案，兼容性更好
# ============================================================

import os
import base64

st.set_page_config(
    page_title="IBI 工程师工具箱",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 读取透明 Logo 并转换为 base64
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_transparent.png")
with open(logo_path, "rb") as f:
    logo_base64 = base64.b64encode(f.read()).decode()

# 读取透明 Logo 并转换为 base64
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_transparent.png")
with open(logo_path, "rb") as f:
    logo_base64 = base64.b64encode(f.read()).decode()

# 最稳定跨浏览器方案：直接通过原生 Markdown 渲染一个绝对定位在左上角的 Logo
st.markdown(
    f"""
    <style>
        /* 强制给 Streamlit 的侧边栏顶部腾出 120px 的空间 */
        [data-testid="stSidebarHeader"] {{
            padding-bottom: 90px !important;
        }}
        
        /* 创建一个幽灵层，绝对定位悬浮在侧边栏最顶端 */
        .sidebar-logo-container {{
            position: absolute;
            top: 2rem;
            left: 2rem;
            width: 80%;
            z-index: 1000;
        }}
        .sidebar-logo {{
            width: 100%;
            height: auto;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(
    f"""
    <div class="sidebar-logo-container">
        <img class="sidebar-logo" src="data:image/png;base64,{logo_base64}">
    </div>
    """,
    unsafe_allow_html=True
)


pg = st.navigation([
    st.Page("pages/home.py",         title="工具箱首页",   icon="🏠", default=True),
    st.Page("pages/1_风机性能曲线.py", title="风机性能曲线", icon="📈"),
    st.Page("pages/2_动平衡工作站.py", title="动平衡工作站", icon="⚖️"),
    st.Page("pages/3_气体计算器.py",  title="气体计算器",  icon="💨"),
])

pg.run()
