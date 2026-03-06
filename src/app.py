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
    /* 取消导致重叠的巨大负边距，恢复正常但偏小的间距 */
    margin-top: 1rem !important;
}
[data-testid="stLogo"] {
    /* 将 Logo 整体下移一点并与左侧文字对齐 */
    margin-top: 1rem !important;
    margin-left: 1.2rem !important;
    margin-bottom: 0.5rem !important;
}
[data-testid="stLogo"] img {
    /* 强制限制 Logo 的最大高度，防止其过大 */
    max-height: 40px !important;
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
