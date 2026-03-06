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

# 读取透明 Logo 路径
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_transparent.png")
st.logo(logo_path)

# 全局侧边栏对齐样式修复（仅做轻微间距修正，不再干涉大小、DOM或背景堆叠）
st.markdown(
    f"""
    <style>
        /* 稍微拉开侧边导航菜单与 Logo 之间的间距 */
        [data-testid="stSidebarNav"] {{
            padding-top: 2rem !important;
        }}
    </style>
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
