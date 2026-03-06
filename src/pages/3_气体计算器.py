import streamlit as st
import os
import base64
import streamlit.components.v1 as components

_static = os.path.join(os.path.dirname(__file__), "..", "static")

def load_html(filename: str, logo_filter: str = "brightness(0) invert(1)") -> str:
    """读取 HTML，把 logo 转 base64 内嵌，并注入 logo 颜色滤镜 CSS"""
    html_path = os.path.join(_static, filename)
    logo_path = os.path.join(_static, "IBI_Logo_Dark.png")

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. 注入 base64 logo（绕过 iframe 沙盒无法加载相对路径的问题）
    try:
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        html = html.replace('src="IBI_Logo_Dark.png"',
                            f'src="data:image/png;base64,{b64}"')
    except FileNotFoundError:
        pass

    # 2. 用 Python 注入滤镜 CSS，让 logo 融合深色背景
    filter_css = f"""
<style>
.logo-img, img[alt="IBI Logo"], .header-logo {{
    filter: {logo_filter} !important;
}}
</style>
"""
    html = html.replace("</head>", filter_css + "</head>")
    return html


components.html(load_html("gas-calculator.html"), height=1050, scrolling=True)
