import streamlit as st

# 注意：st.set_page_config() 已在 app.py 中调用，这里不要重复调用

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 大厅欢迎界面
_, col2, _ = st.columns([1, 8, 1])

with col2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='text-align: center;'>
            <h1 style='font-size: 3rem; font-weight: 800; background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                IBI 工程师工具箱
            </h1>
            <p style='color: #94a3b8; font-size: 1.2rem; margin-top: 10px; margin-bottom: 40px;'>
                集成通用流体计算与力学分析，为内部工程师提供高效、精准的在线支持平台。
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # 三个模块卡片
    m1, m2, m3 = st.columns(3)

    with m1:
        st.markdown("### 📈 风机性能曲线")
        st.markdown("专业的风机性能曲线图谱工具。支持从离线计算数据进行插值，生成包含各类工程边界的精美可导出图谱。")
        if st.button("进入 → 风机性能曲线", use_container_width=True, key="btn_curve"):
            st.switch_page("pages/1_风机性能曲线.py")

    with m2:
        st.markdown("### ⚖️ 动平衡工作站")
        st.markdown("基于 ISO 1940 标准的参数测算与判定系统。许用不平衡力矩评估及钻孔去重深度计算指导。")
        if st.button("进入 → 动平衡工作站", use_container_width=True, key="btn_balance"):
            st.switch_page("pages/2_动平衡工作站.py")

    with m3:
        st.markdown("### 💨 气体计算器")
        st.markdown("通用热力学气体参数转换引擎。绝热压缩功率计算及状态体积、质量流量物理换算。")
        if st.button("进入 → 气体计算器", use_container_width=True, key="btn_gas"):
            st.switch_page("pages/3_气体计算器.py")

    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #64748b; font-size: 0.9rem; margin-top: 30px;'>
            👈 也可从 <b>左侧导航栏</b> 直接点击进入相应模块
            <br><br>
            &copy; 2026 IBI Motor Company. Internal Use Only.
        </div>
        """,
        unsafe_allow_html=True
    )
