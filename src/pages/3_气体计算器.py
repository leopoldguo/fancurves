import streamlit as st
import math

# ─── 单位换算字典（全部统一到 SI 基准）──────────────────────────────────────────
P_TO_KPA  = {"kPa": 1, "MPa": 1000, "bar": 100, "psi": 6.89476,
              "atm": 101.325, "Pa": 0.001, "mmH₂O": 0.00980665, "inH₂O": 0.2490889}
MF_TO_KGS = {"kg/s": 1, "kg/min": 1/60, "kg/h": 1/3600, "g/s": 0.001, "lb/s": 0.453592}
VF_TO_M3S = {"m³/s": 1, "m³/min": 1/60, "m³/h": 1/3600,
              "L/s": 1e-3, "L/min": 1e-3/60, "CFM": 4.71947e-4}
KW_TO_PW  = {"kW": 1, "W": 1000, "MW": 1e-3, "hp": 1/0.7457, "PS": 1/0.7355}
KGM3_TO_D = {"kg/m³": 1, "g/L": 1, "g/cm³": 0.001, "lb/ft³": 1/16.0185}

GAS_DB = {
    "空气":           (28.964, 1.40), "氮气 (N₂)": (28.013, 1.40),
    "氧气 (O₂)":     (31.999, 1.40), "二氧化碳 (CO₂)": (44.010, 1.30),
    "氢气 (H₂)":     (2.016,  1.41), "氦气 (He)": (4.003, 1.66),
    "氩气 (Ar)":     (39.948, 1.67), "甲烷 (CH₄)": (16.043, 1.31),
    "自定义":         (28.964, 1.40),
}

def R(M): return 8.314 / (M / 1000)
def rho_std(M, T_K): return 101325 / (R(M) * T_K)
def rho_act(M, p_kPa, T_K):
    if T_K <= 0 or p_kPa <= 0: return 0.0
    return (p_kPa * 1000) / (R(M) * T_K)
def sig(v, n=4):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))): return "—"
    if v == 0: return "0"
    if abs(v) >= 1e5 or (0 < abs(v) < 1e-3): return f"{v:.4e}"
    return f"{round(v, n)}"

# ─── 全局样式 ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility:hidden;} footer {visibility:hidden;}
/* 隐藏所有数字输入框的 +/- 步进按钮 */
button[data-testid="stNumberInputStepDown"],
button[data-testid="stNumberInputStepUp"] { display:none !important; }
/* 微调 selectbox 顶部对齐 */
div[data-testid="stSelectbox"] { margin-top:0 !important; }
div[data-testid="stSelectbox"] label { display:none !important; }
</style>
""", unsafe_allow_html=True)

# ─── 标题 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:10px 0 4px;'>
  <h1 style='margin-bottom:2px;'>💨 通用气体计算软件</h1>
  <p style='color:#94a3b8;font-size:14px;margin:0;font-weight:bold;'>多工质气体热力学参数 / 绝热压缩功率计算</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ─── 全局单位设置（顶部一行，统一控制所有同类单位）─────────────────────────────
st.markdown("**单位设置**")
u1, u2, u3, u4, u5 = st.columns(5)
with u1: p_unit  = st.selectbox("压力单位",   list(P_TO_KPA.keys()),  key="g_punit")
with u2: t_unit  = st.selectbox("温度单位",   ["°C", "K", "°F"],      key="g_tunit")
with u3: flow_type = st.selectbox("流量类型", ["质量流量", "体积流量"], key="g_ftype")
with u4:
    if flow_type == "质量流量":
        f_unit = st.selectbox("流量单位", list(MF_TO_KGS.keys()), key="g_mfunit")
    else:
        f_unit = st.selectbox("流量单位", list(VF_TO_M3S.keys()), key="g_vfunit")
with u5: d_unit  = st.selectbox("密度单位",   list(KGM3_TO_D.keys()), key="g_dunit")

st.markdown("---")
L, R_col = st.columns([11, 9], gap="large")

# ═══════════════════════════════════════════════
#  左栏：参数输入（全部用全局单位）
# ═══════════════════════════════════════════════
with L:
    # 气体设置
    st.markdown("**气体设置**")
    g1, g2, g3, g4 = st.columns(4)
    gas = g1.selectbox("选择气体", list(GAS_DB.keys()), key="gas")
    def_M, def_g = GAS_DB[gas]
    ref_pv = g2.number_input(f"参考气压 ({p_unit})", value=101.325 / P_TO_KPA[p_unit], step=0.001, format="%.3f")
    M      = g3.number_input("分子量 (g/mol)", value=float(def_M), step=0.1, format="%.3f")
    γ      = g4.number_input("绝热指数 γ",    value=float(def_g), step=0.01, format="%.2f")
    ref_kPa = ref_pv * P_TO_KPA[p_unit]

    # 压力参数（用同一个全局压力单位）
    st.markdown(f"**压力参数 ({p_unit})**")
    pa, pb = st.columns(2)
    inlet_p  = pa.number_input(f"入口压力 (表压, {p_unit})", value=0.0, step=1.0, format="%.3f")
    outlet_p = pb.number_input(f"出口压力 (表压, {p_unit})", value=0.0, step=1.0, format="%.3f")
    p1 = ref_kPa + inlet_p  * P_TO_KPA[p_unit]
    p2 = ref_kPa + outlet_p * P_TO_KPA[p_unit]
    st.caption(f"入口绝压 P₁ = {p1:.3f} kPa　|　出口绝压 P₂ = {p2:.3f} kPa")

    # 温度与流量
    st.markdown(f"**温度与流量**")
    ta, tb, tc, td = st.columns(4)
    T_in = ta.number_input(f"入口温度 ({t_unit})", value=25.0, step=1.0, format="%.1f")
    eff_pct = tb.number_input("绝热效率 (%)", value=80.0, min_value=1.0, max_value=100.0, step=1.0)
    
    if flow_type == "质量流量":
        flow_val = tc.number_input(f"流量 ({f_unit})", value=1.0, step=0.1, format="%.4f")
        td.markdown("")  # 占位
        m_kgs = flow_val * MF_TO_KGS[f_unit]
    else:
        flow_val = tc.number_input(f"流量 ({f_unit})", value=1.0, step=0.1, format="%.4f")
        vf_base  = td.selectbox("体积基准", ["实际入口", "标方 20°C", "标方 0°C"])
        vf_m3s   = flow_val * VF_TO_M3S[f_unit]
        if   vf_base == "实际入口":  ρ_ref = rho_act(M, p1, 300)   # 入口温度若还没算，先用300K近似
        elif vf_base == "标方 20°C": ρ_ref = rho_std(M, 293.15)
        else:                         ρ_ref = rho_std(M, 273.15)
        m_kgs = vf_m3s * ρ_ref

    eff = eff_pct / 100
    if   t_unit == "°C": T1K = T_in + 273.15
    elif t_unit == "°F": T1K = (T_in - 32) * 5/9 + 273.15
    else:                T1K = T_in

    # 如果是体积流量且基准是实际入口，用真实T1K重算
    if flow_type == "体积流量" and vf_base == "实际入口":
        ρ_ref = rho_act(M, p1, T1K)
        m_kgs = vf_m3s * ρ_ref

# ═══════════════════════════════════════════════
#  核心计算
# ═══════════════════════════════════════════════
ρ20  = rho_std(M, 293.15)
ρ0   = rho_std(M, 273.15)
ρ_in = rho_act(M, p1, T1K)

W_ad = W_sh = 0.0
T2K  = T1K
if p1 > 0 and p2 > 0 and γ > 1 and abs(p2 - p1) > 0.001:
    pr   = p2 / p1
    ex   = (γ - 1) / γ
    W_ad = (m_kgs * R(M) * T1K / ex) * (pr**ex - 1) / 1000
    W_sh = W_ad / eff if eff > 0 else 0
    T2s  = T1K * pr**ex
    T2K  = T1K + (T2s - T1K) / eff

ρ_out  = rho_act(M, p2, T2K)
q_in   = m_kgs / ρ_in  * 3600 if ρ_in  > 0 else 0
q_out  = m_kgs / ρ_out * 3600 if ρ_out > 0 else 0

if   t_unit == "°C": T2_disp = T2K - 273.15
elif t_unit == "°F": T2_disp = (T2K - 273.15) * 9/5 + 32
else:                T2_disp = T2K

# ═══════════════════════════════════════════════
#  右栏：计算结果（单位已从全局选择器获取）
# ═══════════════════════════════════════════════
with R_col:
    # 气体密度（全局密度单位，三行对齐）
    st.markdown("**气体密度**")
    dv = KGM3_TO_D[d_unit]
    for lbl, rho_v in [("标态 20°C", ρ20), ("标态 0°C", ρ0), ("实际入口", ρ_in)]:
        lc, vc = st.columns([3, 3])
        lc.markdown(f"<p style='color:#64748b;font-size:12px;font-weight:700;margin:8px 0 0 0;'>{lbl}</p>", unsafe_allow_html=True)
        vc.markdown(f"<p style='color:#94a3b8;font-size:13px;font-weight:700;font-family:Consolas,monospace;text-align:right;margin:8px 0 0 0;'>{sig(rho_v * dv)} {d_unit}</p>", unsafe_allow_html=True)

    st.markdown("---")

    # 功率（单行，大数字 + 单位选择器并列）
    st.markdown("**绝热功率**")
    ad_v, ad_u = st.columns([3, 2])
    pw_ad = ad_u.selectbox("功率单位", list(KW_TO_PW.keys()), key="pw_ad")
    ad_v.markdown(f"<p style='font-size:30px;font-weight:900;color:#f1f5f9;font-family:Consolas,monospace;margin:0;'>{sig(W_ad * KW_TO_PW[pw_ad], 2)} <span style='font-size:14px;color:#475569;'>{pw_ad}</span></p>", unsafe_allow_html=True)

    st.markdown("**轴功率**")
    sh_v, sh_u = st.columns([3, 2])
    pw_sh = sh_u.selectbox("功率单位", list(KW_TO_PW.keys()), key="pw_sh")
    sh_v.markdown(f"<p style='font-size:30px;font-weight:900;color:#60a5fa;font-family:Consolas,monospace;margin:0;'>{sig(W_sh * KW_TO_PW[pw_sh], 2)} <span style='font-size:14px;color:#3b82f6;'>{pw_sh}</span></p>", unsafe_allow_html=True)

    st.markdown("---")

    # 其他物理量
    st.markdown("**其他物理量**")
    for lb, val in [
        ("出口温度",     f"{sig(T2_disp, 2)} {t_unit}"),
        ("实际入口流量", f"{sig(q_in,  2)} m³/h"),
        ("实际出口流量", f"{sig(q_out, 2)} m³/h"),
        ("质量流量",     f"{sig(m_kgs, 5)} kg/s"),
    ]:
        lc, vc = st.columns([3, 3])
        lc.markdown(f"<p style='color:#475569;font-size:12px;font-weight:600;margin:4px 0;'>{lb}</p>", unsafe_allow_html=True)
        vc.markdown(f"<p style='color:#94a3b8;font-size:13px;font-weight:700;font-family:Consolas,monospace;text-align:right;margin:4px 0;'>{val}</p>", unsafe_allow_html=True)
