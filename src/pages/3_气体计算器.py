import streamlit as st
import math

# ── 工具函数 ──────────────────────────────────────────────────────────────────
PRESSURE_UNITS = {
    "kPa":   lambda v: v,
    "MPa":   lambda v: v * 1000,
    "bar":   lambda v: v * 100,
    "psi":   lambda v: v * 6.89476,
    "atm":   lambda v: v * 101.325,
    "Pa":    lambda v: v / 1000,
    "mmH₂O": lambda v: v * 0.00980665,
    "inH₂O": lambda v: v * 0.2490889,
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

def std_density(M, T_ref_K):
    """标准状态密度 (kg/m³), 101.325 kPa"""
    R = 8.314 / (M / 1000)
    return (101.325 * 1000) / (R * T_ref_K)

def actual_density(M, p_kPa, T_K):
    R = 8.314 / (M / 1000)
    return (p_kPa * 1000) / (R * T_K) if T_K > 0 else 0

def fmt(v, n=4):
    if v is None or math.isnan(v): return "—"
    if abs(v) >= 1e6 or (abs(v) < 1e-3 and v != 0):
        return f"{v:.4e}"
    return f"{v:.{n}f}"

# ── 页面 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
/* 收紧 selectbox 上方 label 的留白 */
div[data-testid="stSelectbox"] > label { margin-bottom: 0px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center; padding:12px 0;'>
    <h1 style='margin-bottom:4px;'>💨 通用气体计算软件</h1>
    <p style='color:#94a3b8; font-size:14px; margin:0; font-weight:bold;'>多工质气体热力学参数 / 绝热压缩功率计算</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

col_left, col_right = st.columns([11, 10], gap="large")

# ══════════════════════════════════════════════
# 左侧：参数输入
# ══════════════════════════════════════════════
with col_left:
    st.markdown("#### 气体设置")
    
    ga, gb = st.columns(2)
    with ga:
        gas_name = st.selectbox("选择气体", list(COMMON_GASES.keys()), label_visibility="visible")
    
    def_M, def_g = COMMON_GASES[gas_name]
    with gb:
        # 参考气压 (数值 + 单位并排)
        rp1, rp2 = st.columns([3, 2])
        with rp1:
            ref_p_val = st.number_input("参考气压", value=101.325, step=0.001, format="%.3f")
        with rp2:
            ref_p_unit = st.selectbox("单位##ref", list(PRESSURE_UNITS.keys()), label_visibility="collapsed")

    ma, mb = st.columns(2)
    with ma:
        molar_mass = st.number_input("分子量 (g/mol)", value=float(def_M), step=0.1, format="%.3f")
    with mb:
        gamma = st.number_input("绝热指数 γ", value=float(def_g), step=0.01, format="%.2f")

    ref_kPa = PRESSURE_UNITS[ref_p_unit](ref_p_val)

    st.markdown("#### 压力参数")
    pa1, pa2 = st.columns(2)
    with pa1:
        i1, i2 = st.columns([3, 2])
        with i1:
            inlet_p = st.number_input("入口压力 (表压)", value=0.0, step=1.0, format="%.3f")
        with i2:
            inlet_p_unit = st.selectbox("单位##inlet", list(PRESSURE_UNITS.keys()), label_visibility="collapsed")
    with pa2:
        o1, o2 = st.columns([3, 2])
        with o1:
            outlet_p = st.number_input("出口压力 (表压)", value=0.0, step=1.0, format="%.3f")
        with o2:
            outlet_p_unit = st.selectbox("单位##outlet", list(PRESSURE_UNITS.keys()), label_visibility="collapsed")

    p1_kPa = ref_kPa + PRESSURE_UNITS[inlet_p_unit](inlet_p)
    p2_kPa = ref_kPa + PRESSURE_UNITS[outlet_p_unit](outlet_p)
    st.caption(f"入口绝压 P₁ = {fmt(p1_kPa, 2)} kPa　|　出口绝压 P₂ = {fmt(p2_kPa, 2)} kPa")

    st.markdown("#### 温度与流量")
    ta, tb = st.columns(2)
    with ta:
        t1, t2 = st.columns([3, 2])
        with t1:
            inlet_t = st.number_input("入口温度", value=25.0, step=1.0, format="%.1f")
        with t2:
            t_unit = st.selectbox("单位##temp", ["°C", "K", "°F"], label_visibility="collapsed")

        if t_unit == "°C":   T1_K = inlet_t + 273.15
        elif t_unit == "°F": T1_K = (inlet_t - 32) * 5/9 + 273.15
        else:                T1_K = inlet_t

        eff_pct = st.number_input("绝热效率 (%)", value=80.0, min_value=1.0, max_value=100.0, step=1.0)
        eff = eff_pct / 100.0

    with tb:
        flow_mode = st.radio("流量类型", ["质量流量", "体积流量"], horizontal=True)
        if flow_mode == "质量流量":
            f1, f2 = st.columns([3, 2])
            with f1:
                mf_val = st.number_input("流量值", value=1.0, step=0.1, format="%.4f")
            with f2:
                mf_unit = st.selectbox("单位##mf", list(MASS_FLOW_TO_KGS.keys()), label_visibility="collapsed")
            m_kgs = mf_val * MASS_FLOW_TO_KGS[mf_unit]
        else:
            f1, f2 = st.columns([3, 2])
            with f1:
                vf_val = st.number_input("流量值", value=1.0, step=0.1, format="%.4f")
            with f2:
                vf_unit = st.selectbox("单位##vf", list(VOL_FLOW_TO_M3S.keys()), label_visibility="collapsed")
            vf_base = st.selectbox("体积基准", ["实际入口", "标方 20°C", "标方 0°C"])
            vf_m3s = vf_val * VOL_FLOW_TO_M3S[vf_unit]
            M = molar_mass
            if vf_base == "实际入口":
                rho_f = actual_density(M, p1_kPa, T1_K)
            elif vf_base == "标方 20°C":
                rho_f = std_density(M, 293.15)
            else:
                rho_f = std_density(M, 273.15)
            m_kgs = vf_m3s * rho_f

# ══════════════════════════════════════════════
# 核心计算
# ══════════════════════════════════════════════
M = molar_mass
R_gas = 8.314 / (M / 1000)

rho_std20  = std_density(M, 293.15)
rho_std0   = std_density(M, 273.15)
rho_act_in = actual_density(M, p1_kPa, T1_K)

W_ad_kW = W_sh_kW = 0.0
T2_K = T1_K

if p1_kPa > 0 and p2_kPa > 0 and gamma > 1 and p2_kPa != p1_kPa:
    pr  = p2_kPa / p1_kPa
    exp = (gamma - 1) / gamma
    W_ad_W    = (m_kgs * R_gas * T1_K / exp) * (pr**exp - 1)
    W_ad_kW   = W_ad_W / 1000
    W_sh_kW   = W_ad_kW / eff if eff > 0 else 0
    T2s       = T1_K * pr**exp
    T2_K      = T1_K + (T2s - T1_K) / eff

rho_act_out  = actual_density(M, p2_kPa, T2_K)
q_in_m3h     = (m_kgs / rho_act_in)  * 3600 if rho_act_in  > 0 else 0
q_out_m3h    = (m_kgs / rho_act_out) * 3600 if rho_act_out > 0 else 0

# 出口温度回算到用户单位
if t_unit == "°C":   T2_disp = T2_K - 273.15
elif t_unit == "°F": T2_disp = (T2_K - 273.15) * 9/5 + 32
else:                T2_disp = T2_K

# ══════════════════════════════════════════════
# 右侧：计算结果
# ══════════════════════════════════════════════
with col_right:
    st.markdown("#### 功率输出")

    pw_unit_col, pw_unit_val = st.columns([3, 2])
    with pw_unit_val:
        pw_unit = st.selectbox("功率单位", list(POWER_FROM_KW.keys()), key="pw_unit")
    
    w_ad_disp = W_ad_kW * POWER_FROM_KW[pw_unit]
    w_sh_disp = W_sh_kW * POWER_FROM_KW[pw_unit]

    st.markdown(f"""
    <div style='background:#1e293b; padding:14px 16px; border-radius:10px; border:1px solid #334155; margin-bottom:8px;'>
        <div style='display:flex; justify-content:space-between; align-items:center;'>
            <p style='color:#475569; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:2px; margin:0;'>绝热功率</p>
            <span style='font-size:24px; font-weight:800; color:#f1f5f9; font-family:Consolas,monospace;'>{fmt(w_ad_disp)} {pw_unit}</span>
        </div>
        <div style='display:flex; justify-content:space-between; align-items:center; margin-top:10px; padding-top:10px; border-top:1px solid #334155;'>
            <p style='color:#475569; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:2px; margin:0;'>轴功率</p>
            <span style='font-size:24px; font-weight:800; color:#60a5fa; font-family:Consolas,monospace;'>{fmt(w_sh_disp)} {pw_unit}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


    st.markdown("#### 气体密度")
    d1, d2 = st.columns([4, 2])
    with d2:
        d_unit = st.selectbox("密度单位", list(DENSITY_FROM_KGM3.keys()))
    dv = DENSITY_FROM_KGM3[d_unit]

    with d1:
        st.markdown(f"""
        <div style='background:#1e293b; padding:11px 14px; border-radius:10px; border:1px solid #334155;'>
            <div style='display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid #334155;'>
                <span style='color:#475569; font-size:11px; font-weight:700;'>标态 20°C</span>
                <span style='color:#94a3b8; font-size:13px; font-weight:700; font-family:Consolas,monospace;'>{fmt(rho_std20*dv)} {d_unit}</span>
            </div>
            <div style='display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid #334155;'>
                <span style='color:#475569; font-size:11px; font-weight:700;'>标态 0°C</span>
                <span style='color:#94a3b8; font-size:13px; font-weight:700; font-family:Consolas,monospace;'>{fmt(rho_std0*dv)} {d_unit}</span>
            </div>
            <div style='display:flex; justify-content:space-between; padding:4px 0;'>
                <span style='color:#475569; font-size:11px; font-weight:700;'>实际入口</span>
                <span style='color:#94a3b8; font-size:13px; font-weight:700; font-family:Consolas,monospace;'>{fmt(rho_act_in*dv)} {d_unit}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 其他参数")
    st.markdown(f"""
    <div style='background:#1e293b; padding:11px 14px; border-radius:10px; border:1px solid #334155;'>
        <div style='display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid #334155;'>
            <span style='color:#475569; font-size:12px; font-weight:600;'>出口温度</span>
            <span style='color:#cbd5e1; font-size:13px; font-weight:700; font-family:Consolas,monospace;'>{fmt(T2_disp, 2)} {t_unit}</span>
        </div>
        <div style='display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid #334155;'>
            <span style='color:#475569; font-size:12px; font-weight:600;'>折算质量流量</span>
            <span style='color:#cbd5e1; font-size:13px; font-weight:700; font-family:Consolas,monospace;'>{fmt(m_kgs, 5)} kg/s</span>
        </div>
        <div style='display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid #334155;'>
            <span style='color:#475569; font-size:12px; font-weight:600;'>实际入口体积流量</span>
            <span style='color:#cbd5e1; font-size:13px; font-weight:700; font-family:Consolas,monospace;'>{fmt(q_in_m3h, 2)} m³/h</span>
        </div>
        <div style='display:flex; justify-content:space-between; padding:5px 0;'>
            <span style='color:#475569; font-size:12px; font-weight:600;'>实际出口体积流量</span>
            <span style='color:#cbd5e1; font-size:13px; font-weight:700; font-family:Consolas,monospace;'>{fmt(q_out_m3h, 2)} m³/h</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
