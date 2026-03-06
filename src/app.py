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

# 使用标准的 markdown 注入侧边栏顶部，绝对可控的排版布局，完美适配各种屏幕并不产生重叠
st.sidebar.markdown(
    f"""
    <div style="margin-top: 15px; margin-bottom: 25px; margin-left: 10px;">
        <img src="data:image/png;base64,{logo_base64}" style="width: 85%; height: auto;">
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
