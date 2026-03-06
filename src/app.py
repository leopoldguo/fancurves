import streamlit as st

# ============================================================
# 主入口：使用 st.navigation() 显式注册所有页面
# 这是 Streamlit 1.36+ 推荐的多页面方案，兼容性更好
# ============================================================

st.set_page_config(
    page_title="IBI 工程师工具箱",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

pg = st.navigation([
    st.Page("pages/home.py",         title="工具箱首页",   icon="🏠", default=True),
    st.Page("pages/1_风机性能曲线.py", title="风机性能曲线", icon="📈"),
    st.Page("pages/2_动平衡工作站.py", title="动平衡工作站", icon="⚖️"),
    st.Page("pages/3_气体计算器.py",  title="气体计算器",  icon="💨"),
])

pg.run()
