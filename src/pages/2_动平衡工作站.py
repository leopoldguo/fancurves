import streamlit as st
import os
import streamlit.components.v1 as components

# 读取静态 HTML 文件内容
_html_path = os.path.join(os.path.dirname(__file__), "..", "static", "balance.html")

try:
    with open(_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    # 全屏渲染，高度设为 900px（滚动条会自动接管）
    components.html(html_content, height=950, scrolling=True)
except FileNotFoundError:
    st.error(f"找不到文件：{_html_path}")
