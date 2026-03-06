import streamlit as st
import math

# ── 工具函数 ──────────────────────────────────────────────────────────────────
PRESSURE_UNITS = {
    "kPa": 1, "MPa": 1000, "bar": 100, "psi": 6.89476,
    "atm": 101.325, "Pa": 0.001, "mmH₂O": 0.00980665, "inH₂O": 0.2490889,
}
MASS_FLOW_TO_KGS = {
    "kg/s": 1, "kg/min": 1/60, "kg/h": 1/3600, "g/s": 0.001, "lb/s": 0.453592
}
VOL_FLOW_TO_M3S = {
    "m³/s": 1, "m³/min": 1/60, "m³/h": 1/3600,
    "L/s": 0.001, "L/min": 0.001/60, "CFM": 0.000471947,
}
POWER_FROM_KW = {"kW": 1, "W": 1000, "MW": 0.001, "hp": 1/0.7457, "PS": 1/0.7355}
DENSITY_FROM_KGM3 = {"kg/m³": 1, "g/L": 1, "g/cm³": 0.001, "lb/ft³": 1/16.0185}

COMMON_GASES = {
    "空气":          (28.964, 1.40),
    "氮气 (N₂)":    (28.013, 1.40),
    "氧气 (O₂)":    (31.999, 1.40),
    "二氧化碳 (CO₂)":(44.010, 1.30),
    "氢气 (H₂)":    (2.016,  1.41),
    "氦气 (He)":    (4.003,  1.66),
    "氩气 (Ar)":    (39.948, 1.67),
    "甲烷 (CH₄)":   (16.043, 1.31),
    "自定义":        (28.964, 1.40),
}

def std_density(M, T_K):
    R = 8.314 / (M / 1000)
    return (101.325 * 1000) / (R * T_K)

def act_density(M, p_kPa, T_K):
    if T_K <= 0: return 0
    R = 8.314 / (M / 1000)
    return (p_kPa * 1000) / (R * T_K)

def fmt(v, n=4):
    if v is None or (isinstance(v, float) and math.isnan(v)): return "—"
    if abs(v) >= 1e6 or (abs(v) < 1e-3 and v != 0):
        return f"{v:.3e}"
    return f"{round(v, n)}"

# ── 页面样式 ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.result-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 0; border-bottom: 1px solid #1e293b;
}
.result-row:last-child { border-bottom: none; }
.result-label { font-size: 12px; font-weight: 600; color: #475569; }
.result-value { font-size: 13px; font-weight: 700; color: #94a3b8; font-family: Consolas, monospace; }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown("""
<div style='text-align:center; padding:12px 0;'>
    <h1 style='margin-bottom:4px;'>💨 通用气体计算软件</h1>
    <p style='color:#94a3b8; font-size:14px; margin:0; font-weight:bold;'>多工质气体热力学参数 / 绝热压缩功率计算</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

col_left, col_right = st.columns([11, 9], gap="large")

# ══════════════════════════════════════════════════════════
# 左侧：参数输入  (数值 + 单位并排，比例 3:1.5)
# ══════════════════════════════════════════════════════════
with col_left:
    st.markdown("##### 气体设置")

    g1, g2 = st.columns(2)
    with g1:
        gas_name = st.selectbox("选择气体", list(COMMON_GASES.keys()))
    def_M, def_g = COMMON_GASES[gas_name]
    with g2:
        # 参考气压：数值 + 单位在同一行
        rp_a, rp_b = st.columns([3, 2])
        with rp_a:
            ref_p_val = st.number_input("参考气压", value=101.325, step=0.001, format="%.3f")
        with rp_b:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            ref_p_unit = st.selectbox("##ref_unit", list(PRESSURE_UNITS.keys()), label_visibility="collapsed")

    m1, m2 = st.columns(2)
    with m1:
        molar_mass = st.number_input("分子量 (g/mol)", value=float(def_M), step=0.1, format="%.3f")
    with m2:
        gamma = st.number_input("绝热指数 γ", value=float(def_g), step=0.01, format="%.2f")

    ref_kPa = ref_p_val * PRESSURE_UNITS[ref_p_unit]

    st.markdown("##### 压力参数")
    pa, pb = st.columns(2)
    with pa:
        i_a, i_b = st.columns([3, 2])
        with i_a:
            inlet_p = st.number_input("入口压力 (表压)", value=0.0, step=1.0, format="%.3f")
        with i_b:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            inlet_unit = st.selectbox("##in_unit", list(PRESSURE_UNITS.keys()), label_visibility="collapsed")
    with pb:
        o_a, o_b = st.columns([3, 2])
        with o_a:
            outlet_p = st.number_input("出口压力 (表压)", value=0.0, step=1.0, format="%.3f")
        with o_b:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            outlet_unit = st.selectbox("##out_unit", list(PRESSURE_UNITS.keys()), label_visibility="collapsed")

    p1_kPa = ref_kPa + inlet_p * PRESSURE_UNITS[inlet_unit]
    p2_kPa = ref_kPa + outlet_p * PRESSURE_UNITS[outlet_unit]
    st.caption(f"入口绝压 P₁ = {p1_kPa:.3f} kPa　|　出口绝压 P₂ = {p2_kPa:.3f} kPa")

    st.markdown("##### 温度与流量")
    ta, tb = st.columns(2)
    with ta:
        t_a, t_b = st.columns([3, 2])
        with t_a:
            inlet_t = st.number_input("入口温度", value=25.0, step=1.0, format="%.1f")
        with t_b:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            t_unit = st.selectbox("##t_unit", ["°C", "K", "°F"], label_visibility="collapsed")

        if t_unit == "°C":   T1_K = inlet_t + 273.15
        elif t_unit == "°F": T1_K = (inlet_t - 32) * 5/9 + 273.15
        else:                T1_K = inlet_t

        eff = st.number_input("绝热效率 (%)", value=80.0, min_value=1.0, max_value=100.0, step=1.0) / 100

    with tb:
        flow_mode = st.radio("流量类型", ["质量流量", "体积流量"], horizontal=True)
        if flow_mode == "质量流量":
            f_a, f_b = st.columns([3, 2])
            with f_a:
                mf_val = st.number_input("质量流量", value=1.0, step=0.1, format="%.4f")
            with f_b:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                mf_unit = st.selectbox("##mf_unit", list(MASS_FLOW_TO_KGS.keys()), label_visibility="collapsed")
            m_kgs = mf_val * MASS_FLOW_TO_KGS[mf_unit]
        else:
            f_a, f_b = st.columns([3, 2])
            with f_a:
                vf_val = st.number_input("体积流量", value=1.0, step=0.1, format="%.4f")
            with f_b:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                vf_unit = st.selectbox("##vf_unit", list(VOL_FLOW_TO_M3S.keys()), label_visibility="collapsed")
            vf_base = st.selectbox("体积基准", ["实际入口", "标方 20°C", "标方 0°C"])
            vf_m3s = vf_val * VOL_FLOW_TO_M3S[vf_unit]
            M = molar_mass
            rho_f = (act_density(M, p1_kPa, T1_K) if vf_base == "实际入口"
                     else std_density(M, 293.15) if vf_base == "标方 20°C"
                     else std_density(M, 273.15))
            m_kgs = vf_m3s * rho_f

# ══════════════════════════════════════════════════════════
# 核心计算
# ══════════════════════════════════════════════════════════
M = molar_mass
R_gas = 8.314 / (M / 1000)

rho20   = std_density(M, 293.15)
rho0    = std_density(M, 273.15)
rho_in  = act_density(M, p1_kPa, T1_K)

W_ad_kW = W_sh_kW = 0.0
T2_K = T1_K
if p1_kPa > 0 and p2_kPa > 0 and gamma > 1 and abs(p2_kPa - p1_kPa) > 0.001:
    pr   = p2_kPa / p1_kPa
    ex   = (gamma - 1) / gamma
    W_ad_kW = (m_kgs * R_gas * T1_K / ex) * (pr**ex - 1) / 1000
    W_sh_kW = W_ad_kW / eff if eff > 0 else 0
    T2s     = T1_K * pr**ex
    T2_K    = T1_K + (T2s - T1_K) / eff

rho_out  = act_density(M, p2_kPa, T2_K)
q_in     = (m_kgs / rho_in)  * 3600 if rho_in  > 0 else 0
q_out    = (m_kgs / rho_out) * 3600 if rho_out > 0 else 0

if t_unit == "°C":   T2_disp = T2_K - 273.15
elif t_unit == "°F": T2_disp = (T2_K - 273.15) * 9/5 + 32
else:                T2_disp = T2_K

# ══════════════════════════════════════════════════════════
# 右侧：计算结果
# ══════════════════════════════════════════════════════════
with col_right:

    # ── 气体密度（每行独立单位选择器）──────────────────────
    st.markdown("##### 气体密度")
    
    d_vals = [rho20, rho0, rho_in]
    d_labels = ["标态 20°C", "标态 0°C", "实际入口"]
    d_keys   = ["du20", "du0", "du_act"]
    
    for label, val, key in zip(d_labels, d_vals, d_keys):
        dc1, dc2, dc3 = st.columns([3, 2, 2])
        with dc1:
            st.markdown(f"<p style='color:#475569; font-size:12px; font-weight:700; margin:6px 0 0 0;'>{label}</p>", unsafe_allow_html=True)
        with dc2:
            d_unit = st.selectbox("##" + key, list(DENSITY_FROM_KGM3.keys()), label_visibility="collapsed", key=key)
        with dc3:
            display_val = val * DENSITY_FROM_KGM3[d_unit]
            st.markdown(f"<p style='color:#94a3b8; font-size:13px; font-weight:700; font-family:Consolas,monospace; margin:6px 0 0 0; text-align:right;'>{fmt(display_val)}</p>", unsafe_allow_html=True)

    st.markdown("---")

    # ── 绝热功率（大数字 + 单位并排）──────────────────────
    st.markdown("##### 绝热功率")
    pw1, pw2 = st.columns([3, 2])
    with pw2:
        pw_ad_unit = st.selectbox("##pw_ad", list(POWER_FROM_KW.keys()), label_visibility="collapsed", key="pw_ad")
    with pw1:
        w_ad_disp = W_ad_kW * POWER_FROM_KW[pw_ad_unit]
        st.markdown(f"<p style='font-size:32px; font-weight:900; color:#f1f5f9; font-family:Consolas,monospace; margin:0; text-align:left;'>{fmt(w_ad_disp, 2)}</p>", unsafe_allow_html=True)

    # ── 轴功率 ──────────────────────────────────────────
    st.markdown("##### 轴功率")
    sh1, sh2 = st.columns([3, 2])
    with sh2:
        pw_sh_unit = st.selectbox("##pw_sh", list(POWER_FROM_KW.keys()), label_visibility="collapsed", key="pw_sh")
    with sh1:
        w_sh_disp = W_sh_kW * POWER_FROM_KW[pw_sh_unit]
        st.markdown(f"<p style='font-size:32px; font-weight:900; color:#60a5fa; font-family:Consolas,monospace; margin:0;'>{fmt(w_sh_disp, 2)}</p>", unsafe_allow_html=True)

    st.markdown("---")

    # ── 其他物理量 ──────────────────────────────────────
    st.markdown("##### 其他物理量")
    rows = [
        ("出口温度",          f"{fmt(T2_disp, 2)} {t_unit}"),
        ("实际入口流量",       f"{fmt(q_in, 2)} m³/h"),
        ("实际出口流量",       f"{fmt(q_out, 2)} m³/h"),
        ("折算质量流量",       f"{fmt(m_kgs, 5)} kg/s"),
    ]
    html_rows = "".join(
        f"<div class='result-row'>"
        f"<span class='result-label'>{lb}</span>"
        f"<span class='result-value'>{val}</span>"
        f"</div>"
        for lb, val in rows
    )
    st.markdown(f"<div style='background:#1e293b; padding:10px 14px; border-radius:10px; border:1px solid #334155;'>{html_rows}</div>", unsafe_allow_html=True)
