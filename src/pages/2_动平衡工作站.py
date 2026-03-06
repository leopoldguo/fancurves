import streamlit as st
import math



# 隐藏默认菜单
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.metric-container {
    background-color: #1a202c;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #2d3748;
    text-align: center;
}
.metric-big-text {
    font-size: 3.5rem;
    font-weight: 900;
    color: #34d399; /* emerald-400 */
    line-height: 1;
}
.metric-unit {
    font-size: 1.25rem;
    color: #059669; /* emerald-600 */
    font-weight: bold;
}
.stage-card {
    background-color: #1e293b; 
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid #334155;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 标题区
col1, col2 = st.columns([1, 10])
with col2:
    st.markdown("<h1 style='margin-bottom:0;'>⚖️ 动平衡去重工作站</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; font-size:14px; margin-top:-10px; font-weight:bold;'>ISO 1940 标准计算 / 实体去重指导系统</p>", unsafe_allow_html=True)
st.markdown("---")

# 主体分为左右两部分：阶段 1 (测算) / 阶段 2 (去重)
left_col, right_col = st.columns(2, gap="large")

with left_col:
    st.markdown("<div class='stage-card'>", unsafe_allow_html=True)
    st.subheader("阶段 1：平衡品质边界计算 (ISO 1940)")
    
    # 建立表单参数
    c1, c2 = st.columns(2)
    with c1:
        grade_str = st.selectbox("平衡品质 (G)", ["G0.4", "G1.0", "G2.5", "G6.3", "G16"], index=2)
        weight = st.number_input("工件合计重量 (kg)", min_value=0.1, value=10.0, step=0.1)
    with c2:
        speed = st.number_input("最高工作转速 (rpm)", min_value=10, value=20000, step=100)
        plane_mode = st.selectbox("校正平面", ["单面 (100%)", "双面 (各分配 50%)"])

    G_val = float(grade_str.replace("G", ""))
    planes = 1 if "单面" in plane_mode else 2

    st.markdown("<hr style='margin:10px 0; border-color:#334155;'>", unsafe_allow_html=True)
    
    rc1, rc2 = st.columns(2)
    with rc1:
        radius_A = st.number_input("实际去重操作半径 (面A) [mm]", min_value=1.0, value=50.0, step=1.0)
    with rc2:
        if planes == 2:
            radius_B = st.number_input("实际去重操作半径 (面B) [mm]", min_value=1.0, value=50.0, step=1.0)
        else:
            radius_B = 0.0

    # ================= 计算许用不平衡力矩 =================
    if weight > 0 and speed > 0 and radius_A > 0:
        # U_per = 9549 * G * M / N (g·mm)
        u_per_total = (9549.0 * G_val * weight) / speed
        u_per_plane = u_per_total / planes

        # 折算为当前半径下的质量 (mg)
        permissible_mass_a = (u_per_plane / radius_A) * 1000.0
        permissible_mass_b = (u_per_plane / max(radius_B, 1.0)) * 1000.0 if planes == 2 else 0

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#94a3b8; font-size:12px; font-weight:bold; letter-spacing:1px;'>输入至平衡机的判定基准上限</p>", unsafe_allow_html=True)

        res_cols = st.columns(planes)
        with res_cols[0]:
            st.markdown(f"""
            <div class='metric-container'>
                <p style='color:#64748b; font-size:14px; font-weight:bold; margin-bottom:5px;'>{'面 A' if planes==2 else '单面 (100%)'}</p>
                <span class='metric-big-text'>{permissible_mass_a:.1f}</span>
                <span class='metric-unit'>mg</span>
            </div>
            """, unsafe_allow_html=True)
        if planes == 2:
            with res_cols[1]:
                st.markdown(f"""
                <div class='metric-container'>
                    <p style='color:#64748b; font-size:14px; font-weight:bold; margin-bottom:5px;'>面 B</p>
                    <span class='metric-big-text'>{permissible_mass_b:.1f}</span>
                    <span class='metric-unit'>mg</span>
                </div>
                """, unsafe_allow_html=True)
        
        # 底部小字补充说明力矩
        st.markdown(f"<p style='text-align:center; color:#64748b; font-size:12px; margin-top:15px;'>总许可用力矩: {u_per_total:.2f} g·mm &nbsp;&nbsp;|&nbsp;&nbsp; 单面许用力矩({int(100/planes)}%): {u_per_plane:.2f} g·mm</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    st.markdown("<div class='stage-card'>", unsafe_allow_html=True)
    st.subheader("阶段 2：去重执行策略 (实体打孔深算)")
    
    amount_mg = st.number_input("平衡机显示的待去重质量 (超差值) [mg]", min_value=0.0, value=100.0, step=1.0)
    
    c3, c4 = st.columns(2)
    with c3:
        material_options = {
            "钢 (7.85 g/cm³)": 7.85,
            "铝合金 (2.70 g/cm³)": 2.70,
            "铸铁 (7.30 g/cm³)": 7.30,
            "紫铜 (8.90 g/cm³)": 8.90,
            "钛合金 (4.50 g/cm³)": 4.50,
            "英克奈尔合金 (8.40 g/cm³)": 8.40,
            "自定义...": -1
        }
        selected_mat = st.selectbox("去重材质", list(material_options.keys()))
        if selected_mat == "自定义...":
            density = st.number_input("自定义密度 (g/cm³)", min_value=0.01, value=7.85, step=0.1)
        else:
            density = material_options[selected_mat]

    with c4:
        drill_choices = [4.0, 5.0, 6.0, 8.0, 10.0]
        selected_drill = st.selectbox("选用钻头 (Ø mm)", drill_choices, index=1)
        
    st.markdown("<hr style='margin:10px 0; border-color:#334155;'>", unsafe_allow_html=True)

    if amount_mg > 0 and density > 0 and selected_drill > 0:
        amount_g = amount_mg / 1000.0
        # g/cm3 to g/mm3
        density_mm3 = density / 1000.0
        
        volume_mm3 = amount_g / density_mm3
        drill_radius = selected_drill / 2.0
        area_mm2 = math.pi * (drill_radius ** 2)
        depth_mm = volume_mm3 / area_mm2

        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:flex-end;">
            <p style='color:#cbd5e1; font-weight:bold; margin-bottom:5px;'>目标钻孔深度 (平底基准)</p>
            <p style='color:#64748b; font-size:12px;'>理论排量: {round(volume_mm3)} mm³</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #1e3a8a 0%, #0f172a 100%); padding: 2rem; border-radius: 12px; border: 1px solid #1e3a8a; text-align: center; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);'>
            <span style='font-size: 5rem; font-weight: 900; color: #ffffff; font-family: monospace; text-shadow: 0 4px 15px rgba(59,130,246,0.5);'>{depth_mm:.2f}</span>
            <span style='font-size: 1.5rem; font-weight: bold; color: #60a5fa; margin-left: 10px;'>mm</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("请输入合法的待去重质量与密度。")
        
    st.markdown("</div>", unsafe_allow_html=True)
