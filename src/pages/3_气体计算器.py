import streamlit as st
import math



hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.metric-box {
    background-color: #1e293b;
    border-radius: 10px;
    padding: 15px;
    border: 1px solid #334155;
    margin-bottom: 20px;
}
.metric-box-title {
    font-size: 11px;
    font-weight: 800;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 8px;
}
.metric-big-flex {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.metric-big-value {
    font-size: 28px;
    font-weight: 800;
    color: #f1f5f9;
    font-family: 'Consolas', monospace;
}
.metric-big-unit {
    color: #94a3b8;
    font-size: 16px;
    font-weight: bold;
}
.result-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #1e293b;
}
.result-row-label {
    font-size: 13px;
    font-weight: 600;
    color: #8b9bb4;
}
.result-row-value {
    font-size: 14px;
    font-weight: 700;
    color: #cbd5e1;
    font-family: 'Consolas', monospace;
}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("💨 通用气体计算软件")
st.markdown("<p style='color:#94a3b8; margin-top:-15px;'>多工质气体热力学参数 / 绝热压缩功率计算</p>", unsafe_allow_html=True)
st.markdown("---")

# 数据字典 (内置的常见气体物性)
COMMON_GASES = {
    "空气": {"name": "空气", "molarMass": 28.964, "gamma": 1.4},
    "氮气 (N₂)": {"name": "氮气 (N₂)", "molarMass": 28.013, "gamma": 1.4},
    "氧气 (O₂)": {"name": "氧气 (O₂)", "molarMass": 31.999, "gamma": 1.4},
    "二氧化碳 (CO₂)": {"name": "二氧化碳 (CO₂)", "molarMass": 44.010, "gamma": 1.3},
    "氢气 (H₂)": {"name": "氢气 (H₂)", "molarMass": 2.016, "gamma": 1.41},
    "氦气 (He)": {"name": "氦气 (He)", "molarMass": 4.003, "gamma": 1.66},
    "氩气 (Ar)": {"name": "氩气 (Ar)", "molarMass": 39.948, "gamma": 1.67},
    "甲烷 (CH₄)": {"name": "甲烷 (CH₄)", "molarMass": 16.043, "gamma": 1.31},
    "自定义": {"name": "自定义气", "molarMass": 28.964, "gamma": 1.4}
}

col_left, col_right = st.columns([12, 10], gap="large")

with col_left:
    st.markdown("### 参数设置 Parameter Settings")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # === Group: 气体属性 ===
    st.markdown("**1. 气体设置 (Gas Settings)**")
    c1, c2 = st.columns(2)
    with c1:
        gas_choice = st.selectbox("选择气体", list(COMMON_GASES.keys()))
        ref_p_val = st.number_input("参考气压 (当地大气压)", value=101.325, step=0.001)
        ref_p_unit = st.selectbox("参考气压单位", ["kPa", "MPa", "bar", "atm", "psi", "Pa", "mmH₂O", "inH₂O"])
    with c2:
        m_mass_default = COMMON_GASES[gas_choice]["molarMass"]
        g_default = COMMON_GASES[gas_choice]["gamma"]
        molar_mass = st.number_input("分子量 (g/mol)", value=float(m_mass_default), step=0.1)
        gamma = st.number_input("绝热指数 γ", value=float(g_default), step=0.01)

    # 简单基准转换全部统一到 kPa
    def to_kPa(val, unit):
        if unit == "kPa": return val
        if unit == "MPa": return val * 1000
        if unit == "bar": return val * 100
        if unit == "psi": return val * 6.89476
        if unit == "atm": return val * 101.325
        if unit == "Pa":  return val / 1000
        if unit == "mmH₂O": return val * 0.00980665
        if unit == "inH₂O": return val * 0.2490889
        return val

    ref_kPa = to_kPa(ref_p_val, ref_p_unit)

    st.markdown("<hr style='margin:10px 0; border-color:#334155;'>", unsafe_allow_html=True)

    # === Group: 压力 ===
    st.markdown("**2. 压力参数 (Pressure)**")
    c3, c4 = st.columns(2)
    with c3:
        inlet_p = st.number_input("入口压力 (表压)", value=0.0, step=1.0)
        inlet_p_unit = st.selectbox("入口压力单位", ["kPa", "MPa", "bar", "atm", "psi", "Pa", "mmH₂O", "inH₂O"])
    with c4:
        outlet_p = st.number_input("出口压力 (表压)", value=0.0, step=1.0)
        outlet_p_unit = st.selectbox("出口压力单位", ["kPa", "MPa", "bar", "atm", "psi", "Pa", "mmH₂O", "inH₂O"])
    
    p1_abs_kPa = ref_kPa + to_kPa(inlet_p, inlet_p_unit)
    p2_abs_kPa = ref_kPa + to_kPa(outlet_p, outlet_p_unit)
    
    st.markdown(f"<p style='font-size:12px; color:#64748b;'>入口绝压（P1）: {p1_abs_kPa:.2f} kPa &nbsp; | &nbsp; 出口绝压（P2）: {p2_abs_kPa:.2f} kPa</p>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin:10px 0; border-color:#334155;'>", unsafe_allow_html=True)

    # === Group: 温度与流量 ===
    st.markdown("**3. 温度和流量 (Temp & Flow)**")
    c5, c6 = st.columns(2)
    with c5:
        inlet_t = st.number_input("入口温度", value=25.0, step=1.0)
        t_unit = st.selectbox("温度单位", ["°C", "K", "°F"])
        
        # 统一转开尔文
        T1_K = inlet_t
        if t_unit == "°C": T1_K = inlet_t + 273.15
        elif t_unit == "°F": T1_K = (inlet_t - 32) * 5/9 + 273.15

        eff = st.number_input("绝热效率 (%)", value=80.0, step=1.0) / 100.0

    with c6:
        flow_mode = st.radio("流量输入类型", ["质量流量", "体积流量"], horizontal=True)
        if flow_mode == "质量流量":
            m_flow_val = st.number_input("质量流量数值", value=1.0, step=0.1)
            m_flow_unit = st.selectbox("质量单位", ["kg/s", "kg/min", "kg/h", "g/s", "lb/s"])
            
            # 统一转 kg/s
            if m_flow_unit == "kg/s": m_flow_kgs = m_flow_val
            elif m_flow_unit == "kg/min": m_flow_kgs = m_flow_val / 60
            elif m_flow_unit == "kg/h": m_flow_kgs = m_flow_val / 3600
            elif m_flow_unit == "g/s": m_flow_kgs = m_flow_val / 1000
            elif m_flow_unit == "lb/s": m_flow_kgs = m_flow_val * 0.453592
            
            v_flow_base = "实际入口" # 不重要
        else:
            v_flow_val = st.number_input("体积流量数值", value=1.0, step=0.1)
            v_flow_unit = st.selectbox("体积单位", ["m³/s", "m³/min", "m³/h", "L/s", "L/min", "CFM"])
            v_flow_base = st.selectbox("体积标态基准", ["实际入口", "标方 20°C", "标方 0°C"])

            # 统一转 m3/s
            if v_flow_unit == "m³/s": v_flow_m3s = v_flow_val
            elif v_flow_unit == "m³/min": v_flow_m3s = v_flow_val / 60
            elif v_flow_unit == "m³/h": v_flow_m3s = v_flow_val / 3600
            elif v_flow_unit == "L/s": v_flow_m3s = v_flow_val / 1000
            elif v_flow_unit == "L/min": v_flow_m3s = v_flow_val / 60000
            elif v_flow_unit == "CFM": v_flow_m3s = v_flow_val * 0.000471947
            
            # 内部算密度推算 kg/s
            R_gas = 8.314 / (molar_mass / 1000.0)
            if v_flow_base == "实际入口":
                rho_flow = (p1_abs_kPa * 1000) / (R_gas * T1_K)
            elif v_flow_base == "标方 20°C":
                rho_flow = (101.325 * 1000) / (R_gas * 293.15)
            elif v_flow_base == "标方 0°C":
                rho_flow = (101.325 * 1000) / (R_gas * 273.15)
                
            m_flow_kgs = v_flow_m3s * rho_flow


with col_right:
    st.markdown("### 计算结果 Calculation")
    st.markdown("<br>", unsafe_allow_html=True)
    
    R_gas = 8.314 / (molar_mass / 1000)
    density_act_in = (p1_abs_kPa * 1000) / (R_gas * T1_K) if T1_K > 0 else 0
    density_std_20 = (101.325 * 1000) / (R_gas * 293.15)
    density_std_0 = (101.325 * 1000) / (R_gas * 273.15)

    # 计算压比和功率
    W_ad_kW = 0.0
    W_sh_kW = 0.0
    T2_K = T1_K
    
    if p1_abs_kPa > 0 and p2_abs_kPa > 0 and gamma > 1:
        pr = p2_abs_kPa / p1_abs_kPa
        exp_factor = (gamma - 1) / gamma
        
        # 绝热做功 W = (m * R * T1 / ( (gamma-1)/gamma ) ) * (pr^((gamma-1)/gamma) - 1)
        W_ad_W = (m_flow_kgs * R_gas * T1_K / exp_factor) * (math.pow(pr, exp_factor) - 1)
        W_ad_kW = W_ad_W / 1000.0
        
        if eff > 0:
            W_sh_kW = W_ad_kW / eff
            
        T2s = T1_K * math.pow(pr, exp_factor)
        T2_K = T1_K + (T2s - T1_K) / eff

    density_act_out = (p2_abs_kPa * 1000) / (R_gas * T2_K) if T2_K > 0 else 0
    act_v_flow_in_m3h = (m_flow_kgs / density_act_in) * 3600 if density_act_in > 0 else 0
    act_v_flow_out_m3h = (m_flow_kgs / density_act_out) * 3600 if density_act_out > 0 else 0
    
    # ======= 输出渲染区 =======
    
    st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-box-title'>绝热功率 ADIABATIC POWER</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='metric-big-flex'>
        <span class='metric-big-value'>{W_ad_kW:.2f}</span>
        <span class='metric-big-unit'>kW</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-box-title'>轴功率 SHAFT POWER</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='metric-big-flex'>
        <span class='metric-big-value' style='color:#60a5fa;'>{W_sh_kW:.2f}</span>
        <span class='metric-big-unit' style='color:#3b82f6;'>kW</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 气体密度
    st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-box-title'>气体密度 GAS DENSITY (kg/m³)</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='result-row'><span class='result-row-label'>标态 20°C</span><span class='result-row-value'>{density_std_20:.4f}</span></div>
    <div class='result-row'><span class='result-row-label'>标态 0°C</span><span class='result-row-value'>{density_std_0:.4f}</span></div>
    <div class='result-row' style='border:none;'><span class='result-row-label'>实际入口工况</span><span class='result-row-value'>{density_act_in:.4f}</span></div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 出口温度和其他流量
    st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-box-title'>其他状态参数 OTHER PARAMS</div>", unsafe_allow_html=True)
    
    # 按照输入单位回推出口温度显示
    if t_unit == "°C": T2_disp = T2_K - 273.15
    elif t_unit == "°F": T2_disp = (T2_K - 273.15) * 9/5 + 32
    else: T2_disp = T2_K

    st.markdown(f"""
    <div class='result-row'><span class='result-row-label'>出口温度</span><span class='result-row-value'>{T2_disp:.2f} {t_unit}</span></div>
    <div class='result-row'><span class='result-row-label'>折算系统质量流量</span><span class='result-row-value'>{m_flow_kgs:.4f} kg/s</span></div>
    <div class='result-row'><span class='result-row-label'>实际入口容积流量</span><span class='result-row-value'>{act_v_flow_in_m3h:.2f} m³/h</span></div>
    <div class='result-row' style='border:none;'><span class='result-row-label'>实际出口容积流量</span><span class='result-row-value'>{act_v_flow_out_m3h:.2f} m³/h</span></div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
