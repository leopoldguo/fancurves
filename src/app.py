import streamlit as st
import os
import base64

# ============================================================
# 预先导入所有重量级且带有 C 扩展的依赖库，防止 Streamlit Cloud 
# 环境在 Python 3.13 下，由于通过 st.navigation 触发 exec(code) 
# 加载多页面时产生 importlib 锁并发冲突 (KeyError: frozen importlib._bootstrap)
# ============================================================
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="IBI 工程师工具箱",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 读取透明 Logo 路径并转换
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_transparent.png")
with open(logo_path, "rb") as f:
    logo_base64 = base64.b64encode(f.read()).decode()

# 使用 CSS ::before 伪元素在导航栏的最上方作为独立区块渲染完整的自适应 Logo
st.markdown(
    f"""
    <style>
        /* 隐藏掉带有天生尺寸锁死包袱的原生 st.logo */
        [data-testid="stLogo"] {{
            display: none !important;
        }}
        
        /* 在侧边菜单栏内直接插入一个虚拟元素当 Logo */
        [data-testid="stSidebarNav"]::before {{
            content: "";
            display: block;
            width: 85%;
            height: 65px; /* 按照 4.3 的宽高比计算出合理且较大的高度 */
            margin-left: 1.5rem;
            margin-top: 1rem;
            margin-bottom: 2rem;
            background-image: url("data:image/png;base64,{logo_base64}");
            background-size: contain;
            background-repeat: no-repeat;
            background-position: left center;
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
