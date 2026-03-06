import streamlit as st

def main():
    st.set_page_config(
        page_title="IBI 工程师工具箱",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 隐藏顶部的 "Deploy" 菜单和页脚
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # 大厅欢迎界面
    col1, col2, col3 = st.columns([1, 8, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # 如果有 Logo，可以在这里加载 (暂时预留文本标题)
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
        
        # 模块导航卡片 — 使用 st.page_link() 实现真正的页面跳转
        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.markdown("### 📈 风机性能曲线")
            st.markdown("专业的风机性能曲线图谱工具。支持从离线计算数据进行插值，生成包含各类工程边界（如喘振线、做功效率等）的精美可导出图谱。")
            st.page_link("pages/1_📈_风机性能曲线.py", label="进入 → 风机性能曲线", icon="📈")
            
        with m2:
            st.markdown("### ⚖️ 动平衡工作站")
            st.markdown("基于 ISO 1940 标准的参数测算与判定系统。支持许用不平衡力矩评估及各类实体制品钻孔去重的深度计算指导。")
            st.page_link("pages/2_⚖️_动平衡工作站.py", label="进入 → 动平衡工作站", icon="⚖️")
            
        with m3:
            st.markdown("### 💨 气体计算器")
            st.markdown("通用热力学气体参数转换引擎。提供多工质纯气体及标准空气压缩绝热功率计算，以及状态体积、质量流量物理换算。")
            st.page_link("pages/3_💨_气体计算器.py", label="进入 → 气体计算器", icon="💨")

        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; color: #64748b; font-size: 0.9rem; margin-top: 50px;'>
                👈 也可从 <b>左侧导航栏</b> (Sidebar) 直接点击进入相应模块
                <br><br>
                &copy; 2026 IBI Motor Company. Internal Use Only.
            </div>
            """,
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
