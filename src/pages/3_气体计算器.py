import streamlit as st
import math

# ─── 单位换算字典（统一方向：把"其他单位"转换为SI基准单位）─────────────────────
# 压力：乘以系数 → kPa
P_TO_KPA  = {"kPa": 1, "MPa": 1000, "bar": 100, "psi": 6.89476,
              "atm": 101.325, "Pa": 0.001, "mmH₂O": 0.00980665, "inH₂O": 0.2490889}
# 流量：乘以系数 → kg/s
MF_TO_KGS = {"kg/s": 1, "kg/min": 1/60, "kg/h": 1/3600, "g/s": 0.001, "lb/s": 0.453592}
# 体积流量：→ m³/s
VF_TO_M3S = {"m³/s": 1, "m³/min": 1/60, "m³/h": 1/3600,
              "L/s": 1e-3, "L/min": 1e-3/60, "CFM": 4.71947e-4}
# 功率：kW → 显示单位（乘以系数）
KW_TO_PW  = {"kW": 1, "W": 1000, "MW": 1e-3, "hp": 1/0.7457, "PS": 1/0.7355}
# 密度：kg/m³ → 显示单位（乘以系数）
KGM3_TO_D = {"kg/m³": 1, "g/L": 1, "g/cm³": 0.001, "lb/ft³": 1/16.0185}

GAS_DB = {
    "空气":           (28.964, 1.40),
    "氮气 (N₂)":     (28.013, 1.40),
    "氧气 (O₂)":     (31.999, 1.40),
    "二氧化碳 (CO₂)": (44.010, 1.30),
    "氢气 (H₂)":     (2.016,  1.41),
    "氦气 (He)":     (4.003,  1.66),
    "氩气 (Ar)":     (39.948, 1.67),
    "甲烷 (CH₄)":    (16.043, 1.31),
    "自定义":         (28.964, 1.40),
}

def R(M): return 8.314 / (M / 1000)          # 比气体常数 J/(kg·K)

def rho_std(M, T_K):
    return (101.325e3) / (R(M) * T_K)         # 标准状态密度 kg/m³

def rho_act(M, p_kPa, T_K):
    if T_K <= 0 or p_kPa <= 0: return 0.0
    return (p_kPa * 1e3) / (R(M) * T_K)

def sig(v, n=4):
    """有效位数显示"""
    if v is None or (isinstance(v, float) and math.isnan(v)): return "—"
    if v == 0: return "0"
    if abs(v) >= 1e5 or (abs(v) < 1e-3 and v != 0):
        return f"{v:.4e}"
    return f"{round(v, n)}"

# ─── 样式 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
div[data-testid="stSelectbox"] { margin-top: 0 !important; }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown("""
<div style='text-align:center;padding:10px 0 4px;'>
  <h1 style='margin-bottom:2px;'>💨 通用气体计算软件</h1>
  <p style='color:#94a3b8;font-size:14px;margin:0;font-weight:bold;'>多工质气体热力学参数 / 绝热压缩功率计算</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

L, R_col = st.columns([11, 9], gap="large")

# ═══════════════════════════════════════════════
#  左栏：参数输入（数值 + 单位并排）
# ═══════════════════════════════════════════════
with L:
    # —— 气体设置 ——
    st.markdown("**气体设置**")
    c1, c2 = st.columns(2)
    with c1:
        gas = st.selectbox("选择气体", list(GAS_DB.keys()))
    def_M, def_g = GAS_DB[gas]
    with c2:
        rp_v_col, rp_u_col = st.columns([3, 2])
        ref_pv = rp_v_col.number_input("参考气压", value=101.325, step=0.001, format="%.3f")
        ref_pu = rp_u_col.selectbox("_", list(P_TO_KPA.keys()), label_visibility="collapsed", key="ref_pu")

    c3, c4 = st.columns(2)
    M = c3.number_input("分子量 (g/mol)", value=float(def_M), step=0.1, format="%.3f")
    γ = c4.number_input("绝热指数 γ", value=float(def_g), step=0.01, format="%.2f")
    ref_kPa = ref_pv * P_TO_KPA[ref_pu]

    # —— 压力 ——
    st.markdown("**压力参数**")
    pa, pb = st.columns(2)
    with pa:
        iv, iu = st.columns([3, 2])
        inlet_p  = iv.number_input("入口压力 (表压)", value=0.0, step=1.0, format="%.3f")
        inlet_pu = iu.selectbox("_", list(P_TO_KPA.keys()), label_visibility="collapsed", key="in_pu")
    with pb:
        ov, ou = st.columns([3, 2])
        outlet_p  = ov.number_input("出口压力 (表压)", value=0.0, step=1.0, format="%.3f")
        outlet_pu = ou.selectbox("_", list(P_TO_KPA.keys()), label_visibility="collapsed", key="out_pu")

    p1 = ref_kPa + inlet_p  * P_TO_KPA[inlet_pu]   # 绝对入口压力 kPa
    p2 = ref_kPa + outlet_p * P_TO_KPA[outlet_pu]   # 绝对出口压力 kPa
    st.caption(f"入口绝压 P₁ = {p1:.3f} kPa　|　出口绝压 P₂ = {p2:.3f} kPa")

    # —— 温度 & 流量 ——
    st.markdown("**温度与流量**")
    ta, tb = st.columns(2)
    with ta:
        tv, tu = st.columns([3, 2])
        T_in   = tv.number_input("入口温度", value=25.0, step=1.0, format="%.1f")
        t_unit = tu.selectbox("_", ["°C", "K", "°F"], label_visibility="collapsed", key="t_u")
        eff_pct = st.number_input("绝热效率 (%)", value=80.0, min_value=1.0, max_value=100.0, step=1.0)
        eff = eff_pct / 100

    if   t_unit == "°C": T1K = T_in + 273.15
    elif t_unit == "°F": T1K = (T_in - 32) * 5/9 + 273.15
    else:                T1K = T_in

    with tb:
        flow_type = st.radio("流量类型", ["质量流量", "体积流量"], horizontal=True)
        if flow_type == "质量流量":
            fv, fu = st.columns([3, 2])
            mf_val  = fv.number_input("流量", value=1.0, step=0.1, format="%.4f", key="mf_v")
            mf_unit = fu.selectbox("_", list(MF_TO_KGS.keys()), label_visibility="collapsed", key="mf_u")
            m_kgs = mf_val * MF_TO_KGS[mf_unit]
        else:
            fv, fu = st.columns([3, 2])
            vf_val  = fv.number_input("流量", value=1.0, step=0.1, format="%.4f", key="vf_v")
            vf_unit = fu.selectbox("_", list(VF_TO_M3S.keys()), label_visibility="collapsed", key="vf_u")
            vf_base = st.selectbox("体积基准", ["实际入口", "标方 20°C", "标方 0°C"])
            vf_m3s  = vf_val * VF_TO_M3S[vf_unit]
            if   vf_base == "实际入口":  ρ_ref = rho_act(M, p1, T1K)
            elif vf_base == "标方 20°C": ρ_ref = rho_std(M, 293.15)
            else:                         ρ_ref = rho_std(M, 273.15)
            m_kgs = vf_m3s * ρ_ref

# ═══════════════════════════════════════════════
#  核心计算
# ═══════════════════════════════════════════════
ρ20    = rho_std(M, 293.15)
ρ0     = rho_std(M, 273.15)
ρ_in   = rho_act(M, p1, T1K)

W_ad = W_sh = 0.0
T2K = T1K
if p1 > 0 and p2 > 0 and γ > 1 and abs(p2 - p1) > 0.001:
    pr   = p2 / p1
    ex   = (γ - 1) / γ
    W_ad = (m_kgs * R(M) * T1K / ex) * (pr**ex - 1) / 1000   # kW
    W_sh = W_ad / eff if eff > 0 else 0
    T2s  = T1K * pr**ex
    T2K  = T1K + (T2s - T1K) / eff

ρ_out  = rho_act(M, p2, T2K)
q_in   = m_kgs / ρ_in  * 3600 if ρ_in  > 0 else 0   # m³/h
q_out  = m_kgs / ρ_out * 3600 if ρ_out > 0 else 0

if   t_unit == "°C": T2_disp = T2K - 273.15
elif t_unit == "°F": T2_disp = (T2K - 273.15) * 9/5 + 32
else:                T2_disp = T2K

# ═══════════════════════════════════════════════
#  右栏：计算结果
# ═══════════════════════════════════════════════
with R_col:

    # —— 气体密度（每行右侧独立单位选择器，和数值同行）——
    st.markdown("**气体密度**")
    for label, rho_val, key in [
        ("标态 20°C", ρ20,  "du20"),
        ("标态 0°C",  ρ0,   "du0"),
        ("实际入口",  ρ_in, "du_act"),
    ]:
        lc, vc, uc = st.columns([3, 3, 2])
        lc.markdown(f"<p style='color:#64748b;font-size:12px;font-weight:700;margin:8px 0 0 0;'>{label}</p>", unsafe_allow_html=True)
        # 先读单位，再算显示值（Streamlit 整页重跑，selectbox 返回当前值）
        d_unit = uc.selectbox("_", list(KGM3_TO_D.keys()), label_visibility="collapsed", key=key)
        disp   = rho_val * KGM3_TO_D[d_unit]
        vc.markdown(f"<p style='color:#94a3b8;font-size:13px;font-weight:700;font-family:Consolas,monospace;text-align:right;margin:8px 0 0 0;'>{sig(disp)}</p>", unsafe_allow_html=True)

    st.markdown("---")

    # —— 绝热功率（大数字 + 单位选择器同行）——
    st.markdown("**绝热功率**")
    ad_v, ad_u = st.columns([3, 2])
    # 先在右列读单位 → 再在左列渲染值（同一 st.columns 行内）
    pw_ad_unit = ad_u.selectbox("_", list(KW_TO_PW.keys()), label_visibility="collapsed", key="pw_ad")
    w_ad_disp  = W_ad * KW_TO_PW[pw_ad_unit]
    ad_v.markdown(f"<p style='font-size:30px;font-weight:900;color:#f1f5f9;font-family:Consolas,monospace;margin:0;'>{sig(w_ad_disp, 2)} <span style='font-size:14px;color:#64748b;'>{pw_ad_unit}</span></p>", unsafe_allow_html=True)

    # —— 轴功率 ——
    st.markdown("**轴功率**")
    sh_v, sh_u = st.columns([3, 2])
    pw_sh_unit = sh_u.selectbox("_", list(KW_TO_PW.keys()), label_visibility="collapsed", key="pw_sh")
    w_sh_disp  = W_sh * KW_TO_PW[pw_sh_unit]
    sh_v.markdown(f"<p style='font-size:30px;font-weight:900;color:#60a5fa;font-family:Consolas,monospace;margin:0;'>{sig(w_sh_disp, 2)} <span style='font-size:14px;color:#3b82f6;'>{pw_sh_unit}</span></p>", unsafe_allow_html=True)

    st.markdown("---")

    # —— 其他物理量 ——
    st.markdown("**其他物理量**")
    for lb, val in [
        ("出口温度",     f"{sig(T2_disp, 2)} {t_unit}"),
        ("实际入口流量", f"{sig(q_in,  2)} m³/h"),
        ("实际出口流量", f"{sig(q_out, 2)} m³/h"),
        ("质量流量",     f"{sig(m_kgs, 5)} kg/s"),
    ]:
        c_l, c_r = st.columns([3, 3])
        c_l.markdown(f"<p style='color:#475569;font-size:12px;font-weight:600;margin:4px 0;'>{lb}</p>", unsafe_allow_html=True)
        c_r.markdown(f"<p style='color:#94a3b8;font-size:13px;font-weight:700;font-family:Consolas,monospace;text-align:right;margin:4px 0;'>{val}</p>", unsafe_allow_html=True)
