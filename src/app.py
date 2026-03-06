import streamlit as st

# ============================================================
# 主入口：使用 st.navigation() 显式注册所有页面
# 这是 Streamlit 1.36+ 推荐的多页面方案，兼容性更好
# ============================================================

import os

st.set_page_config(
    page_title="IBI 工程师工具箱",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 使用绝对路径定位刚刚抠图好的透明 Logo，避免部署云端时因执行目录变化引起的路径报错
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_transparent.png")
st.logo(logo_path)

# 全局侧边栏对齐样式修复
st.markdown("""
<style>
/* 修复侧边栏带有 logo 时的超大间隔和不对齐问题 */
[data-testid="stSidebarNav"] {
    /* 调整导航上下边距，使其与上方 Logo 保持舒适距离 */
    padding-top: 1.5rem !important;
}
[data-testid="stLogo"] {
    /* Logo 原始容器下移，与导航的左侧留白看齐 */
    margin-top: 2rem !important;
    margin-left: 1.5rem !important;
    margin-bottom: 0rem !important;
}
[data-testid="stLogo"] img {
    /* 把 Logo 放大！Streamlit 默认卡得非常死，我们强行放大它的最大高度范围 */
    max-height: 55px !important;
    height: auto !important;
    width: auto !important;
}
</style>
""", unsafe_allow_html=True)

pg = st.navigation([
    st.Page("pages/home.py",         title="工具箱首页",   icon="🏠", default=True),
    st.Page("pages/1_风机性能曲线.py", title="风机性能曲线", icon="📈"),
    st.Page("pages/2_动平衡工作站.py", title="动平衡工作站", icon="⚖️"),
    st.Page("pages/3_气体计算器.py",  title="气体计算器",  icon="💨"),
])

pg.run()
