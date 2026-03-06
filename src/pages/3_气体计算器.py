import streamlit as st
import os
import base64
import streamlit.components.v1 as components

_static = os.path.join(os.path.dirname(__file__), "..", "static")

def load_with_logo(html_filename: str) -> str:
    html_path = os.path.join(_static, html_filename)
    logo_path = os.path.join(_static, "IBI_Logo_Dark.png")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    try:
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        html = html.replace('src="IBI_Logo_Dark.png"',
                            f'src="data:image/png;base64,{b64}"')
    except FileNotFoundError:
        pass
    return html

components.html(load_with_logo("gas-calculator.html"), height=1050, scrolling=True)
