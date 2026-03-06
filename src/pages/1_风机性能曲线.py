import math
import streamlit as st
import pandas as pd
from data_parser import (
    normalize_dataframe, convert_flow_units,
    filter_operating_points, convert_pressure_ratio_to_kpa,
    compute_efficiency
)
from plotter import create_performance_curve, create_performance_curve_export

import json
import os


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

/* ── Root Variables ── */
:root {
    --blue-brand:   #3B5FA0;
    --blue-dark:    #2A4580;
    --blue-light:   #5A80C8;
    --blue-accent:  #7EAAEE;
    --white:        #F5F7FA;
    --white-dim:    rgba(245,247,250,0.75);
    --bg-main:      #131B2E;
    --bg-card:      rgba(255,255,255,0.04);
    --border:       rgba(255,255,255,0.12);
}

/* 隐藏 Streamlit 默认组件 */
#MainMenu {visibility: hidden;}
[data-testid="stHeaderActionElements"] {visibility: hidden;}
header {background: transparent !important;}
footer {visibility: hidden;}

/* 减小顶部留白 */
.block-container {
    padding-top: 1rem !important;
}

    --mono:         'IBM Plex Mono', monospace;
    --sans:         'IBM Plex Sans', sans-serif;
}

/* ── Global ── */
html, body {
    font-family: var(--sans);
    background-color: var(--bg-main) !important;
}
/* 主内容区域背景 + 页眉 */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stHeader"],
.main .block-container {
    background-color: var(--bg-main) !important;
}
[data-testid="stHeader"] {
    border-bottom: 1px solid rgba(94,128,200,0.25) !important;
}

/* ── Sidebar: IBI Brand Blue ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--blue-brand) 0%, var(--blue-dark) 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.10) !important;
}
section[data-testid="stSidebar"] * {
    color: var(--white) !important;
}

/* ── Sidebar: Input Controls ── */
section[data-testid="stSidebar"] input {
    background-color: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.30) !important;
    border-radius: 4px !important;
    color: var(--white) !important;
    font-family: var(--mono) !important;
}
section[data-testid="stSidebar"] div[data-baseweb="input"],
section[data-testid="stSidebar"] div[data-baseweb="base-input"] {
    background-color: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.30) !important;
    border-radius: 4px !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.30) !important;
    border-radius: 4px !important;
    color: var(--white) !important;
}
section[data-testid="stSidebar"] input:focus {
    border-color: var(--blue-accent) !important;
    box-shadow: 0 0 0 2px rgba(126,170,238,0.25) !important;
}

/* ── Sidebar: Divider & Expander ── */
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.20) !important;
    margin: 8px 0 !important;
}
section[data-testid="stSidebar"] details {
    background: rgba(0,0,0,0.15) !important;
    border-radius: 6px !important;
}
/* 隐藏所有 Streamlit 悬停/缩放/键盘快捷键浮层 */
[data-testid="stImage"] button,
[data-testid="StyledFullScreenButton"],
section[data-testid="stSidebar"] [data-testid="stTooltipHoverTarget"],
[data-testid="stTooltipIcon"],
div[class*="keyboardShortcut"] {
    display: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: transparent !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: rgba(59,95,160,0.25) !important;
    border: 1.5px dashed rgba(126,170,238,0.70) !important;
    border-radius: 8px !important;
    backdrop-filter: blur(4px) !important;
}
[data-testid="stFileUploaderDropzone"] * {
    color: var(--white) !important;
    background: transparent !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: var(--blue-brand) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    color: white !important;
    border-radius: 4px !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    background: var(--blue-light) !important;
}
[data-testid="stFileUploaderDropzone"] svg {
    fill: rgba(255,255,255,0.6) !important;
}

/* ── Headings ── */
h1, h2, h3 {
    font-family: var(--sans) !important;
    color: var(--white) !important;
    letter-spacing: -0.01em !important;
}
h2, h3 {
    border-bottom: 1px solid var(--border) !important;
    padding-bottom: 4px !important;
}

/* ── Metric Values (Monospace for Data) ── */
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"],
.stNumberInput input {
    font-family: var(--mono) !important;
    letter-spacing: 0.02em !important;
}



/* ── Radio Buttons in Sidebar ── */
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: rgba(0,0,0,0.15) !important;
    border-radius: 4px !important;
    padding: 2px 8px !important;
    margin: 2px 0 !important;
}
/* ── Number Input +/- Buttons ── */
section[data-testid="stSidebar"] button[aria-label="增加"],
section[data-testid="stSidebar"] button[aria-label="减少"],
section[data-testid="stSidebar"] [data-testid="stNumberInput"] button,
section[data-testid="stSidebar"] [data-testid="stNumberInputStepUp"],
section[data-testid="stSidebar"] [data-testid="stNumberInputStepDown"] {
    background: rgba(255,255,255,0.15) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 3px !important;
    color: var(--white) !important;
}
section[data-testid="stSidebar"] [data-testid="stNumberInput"] button:hover {
    background: rgba(255,255,255,0.28) !important;
}
section[data-testid="stSidebar"] [data-testid="stNumberInput"] button svg,
section[data-testid="stSidebar"] [data-testid="stNumberInput"] button span {
    color: var(--white) !important;
    fill: var(--white) !important;
}
</style>
""", unsafe_allow_html=True)

# ─── 头部标题与 Logo (纯 HTML，无 Streamlit 组件层) ───────────────────────────
_header_logo_filename = "IBI Logo.png"
_header_logo_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", _header_logo_filename),
    os.path.join(os.getcwd(), _header_logo_filename),
    # fallback to old jpeg
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "IBI Logo.jpeg"),
    os.path.join(os.getcwd(), "IBI Logo.jpeg"),
]
_header_logo_b64 = ""
_header_mime = "png"
import base64 as _b64h
for _p in _header_logo_paths:
    if os.path.exists(_p):
        with open(_p, "rb") as _hf:
            _header_logo_b64 = _b64h.b64encode(_hf.read()).decode()
        _header_mime = "png" if _p.lower().endswith(".png") else "jpeg"
        break

# Logo + 标题居中（一行 flexbox，logo 在左，标题紧随其后）
if _header_logo_b64:
    _logo_tag = (
        f'<img src="data:image/{_header_mime};base64,{_header_logo_b64}" '
        f'style="height:42px;width:42px;object-fit:contain;margin-right:12px;">'
    )
else:
    _logo_tag = ""

st.markdown(
    f'<div style="display:flex;align-items:center;justify-content:center;padding:16px 0 8px 0;">'
    f'{_logo_tag}'
    f'<h1 style="margin:0;font-size:2.2rem;color:#F5F7FA;font-family:IBM Plex Sans,sans-serif;'
    f'font-weight:700;letter-spacing:-0.02em;line-height:1.15;">风机性能曲线数据看板</h1>'
    f'</div>',
    unsafe_allow_html=True
)

PREFS_FILE = "user_prefs.json"

def load_prefs():
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_pref(key):
    prefs = load_prefs()
    prefs[key] = st.session_state[key]
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f)

if "prefs_loaded" not in st.session_state:
    prefs = load_prefs()
    defaults = {
        "flow_unit": "kg/s",
        "pressure_display": "压比 (PR)",
        "show_power": True,
        "page_mode": "性能曲线看板",
        "has_seal": False,
        "has_impeller_holes": False,
        "has_backplate_holes": False,
        "d_imp_mm": 500.0,
        "d_shaft_mm": 100.0,
        "d_seal_mm": 120.0,
        "bp_gap_mm": 1.0,
        "p_ambient_pa": 101325.0
    }
    for k, v in defaults.items():
        if k not in prefs:
            prefs[k] = v
            
    for k, v in prefs.items():
        st.session_state[k] = v
    st.session_state["prefs_loaded"] = True

AIR_DENSITY_20C = 1.204

def calc_specific_speed(rpm, flow_val, flow_unit, pr):
    """中国压缩机常用比转速公式: n_s = n * sqrt(Q_v) / (h_ad)^0.75
    Q_v (m³/min), h_ad (m，绝热头)
    """
    if flow_unit == "kg/s":
        q = (flow_val / AIR_DENSITY_20C) * 60.0
    elif flow_unit == "m3/h":
        q = flow_val / 60.0
    elif flow_unit == "CFM":
        q = flow_val * 0.0283168
    else:
        q = flow_val
    if pr <= 1.0 or q <= 0: return 0.0
    # h_ad (J/kg) = k/(k-1) * R * T1 * (PR^((k-1)/k) - 1) 
    # Air: k=1.4, R=287, T1=293.15K -> 294469.175
    h_ad_j_kg = 294469.175 * (pr**0.2857 - 1)
    h_ad_m = h_ad_j_kg / 9.80665
    return rpm * math.sqrt(q) / (h_ad_m**0.75)

# ─── 侧边栏 ───────────────────────────────────────────────────────────────────
_logo_sidebar = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_compressor.png")
if os.path.exists(_logo_sidebar):
    import base64 as _b64
    with open(_logo_sidebar, "rb") as _f:
        _logo_b64 = _b64.b64encode(_f.read()).decode()
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{_logo_b64}" style="width:100%;display:block;margin-bottom:8px;">',
        unsafe_allow_html=True
    )
st.sidebar.header("控制面板")

page_mode = st.sidebar.radio(
    "导航菜单", ["性能曲线看板", "轴向力深度分析"],
    key="page_mode", on_change=save_pref, args=("page_mode",)
)
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("上传 CFX 结果 (CSV)", type=["csv"])

unit_card = st.sidebar.container(border=True)
unit_card.subheader("单位设置")
flow_unit = unit_card.selectbox(
    "流量单位", ["kg/s", "m3/h", "m3/min", "CFM"],
    help="体积流量均以 20°C、1 标准大气压（1.204 kg/m³）换算",
    key="flow_unit", on_change=save_pref, args=("flow_unit",)
)
pressure_display = unit_card.selectbox(
    "压力单位", ["压比 (PR)", "差压 (ΔkPa)", "绝对出口压力 (kPa abs)"],
    help="以标准大气压 101.325 kPa 为基准",
    key="pressure_display", on_change=save_pref, args=("pressure_display",)
)

PRESSURE_MODE_MAP  = {"压比 (PR)": "pressure_ratio", "差压 (ΔkPa)": "delta_kPa", "绝对出口压力 (kPa abs)": "abs_kPa"}
PRESSURE_LABEL_MAP = {"pressure_ratio": "压比 [-]", "delta_kPa": "差压 ΔP [kPa]", "abs_kPa": "绝对出口压力 [kPa]"}
pressure_mode = PRESSURE_MODE_MAP[pressure_display]
y1_label      = PRESSURE_LABEL_MAP[pressure_mode]

# ─── 数据上传 ─────────────────────────────────────────────────────────────────
if uploaded_file:
    try:
        try:
            raw_df = pd.read_csv(uploaded_file, encoding='gbk')
        except UnicodeDecodeError:
            raw_df = pd.read_csv(uploaded_file, encoding='utf-8')
    except Exception as e:
        st.error(f"无法读取文件: {e}"); st.stop()

    df = normalize_dataframe(raw_df)
    if "mass_flow" not in df.columns:
        st.error("未识别流量列"); st.stop()

    # 流量单位换算：使用每行动态密度 rho（真空工况支持）
    df["display_flow"] = df.apply(
        lambda row: convert_flow_units(row["mass_flow"], "kg/s", flow_unit, density=row["rho"]),
        axis=1
    )

    pressure_raw_col = "pressure_ratio"
    power_col        = "shaft_power"

    if pressure_raw_col not in df.columns:
        st.error("未识别压力列"); st.stop()

    # 效率：优先 CSV 直接值，否则等熵公式
    can_use_csv_eff = "efficiency_pct" in df.columns
    can_compute_eff = ("mass_flow" in df.columns and
                       pressure_raw_col in df.columns and
                       power_col in df.columns)
    has_efficiency  = can_use_csv_eff or can_compute_eff
    if has_efficiency:
        df = compute_efficiency(df)
        eff_source = "CSV 等熵效率列（直接值）" if can_use_csv_eff else "等熵公式计算值"

    # ─── 真空模式检测 ──────────────────────────────────────────────────────────────
    has_real_p_in = "p_in_pa" in df.columns and df["p_in_pa"].notna().any()
    is_vacuum     = has_real_p_in and (df["p_in_pa"].median() < 100000.0)
    avg_p_in_kpa  = df["p_in_pa"].mean() / 1000.0 if has_real_p_in else 101.325

    # 在真空+差压模式下，动态覆盖 Y 轴标签
    if is_vacuum and pressure_mode == "delta_kPa":
        y1_label = "进口表压 [kPa]（真空模式，负值）"

    # ─── 过滤阈值 ─────────────────────────────────────────────────────────────
    if page_mode == "性能曲线看板":
        if is_vacuum:
            st.info(f"🌌 **真空模式已激活**：检测到 CSV 入口压力中位数为 **{avg_p_in_kpa:.1f} kPa**，低于 1 atm。Y 轴「差压」已自动切换为进口表压（负 kPa）。")
        st.sidebar.markdown("---")
        st.sidebar.subheader("数据过滤阈值")
        min_pr_val = float(df[pressure_raw_col].min())
        max_pr_val = float(df[pressure_raw_col].max())

        if "min_pr_threshold" not in st.session_state or not (1.0 <= st.session_state.min_pr_threshold <= max_pr_val):
            st.session_state.min_pr_threshold = float(min_pr_val)

        min_pr_threshold = st.sidebar.number_input(
            "最低压比阈值", min_value=1.0, max_value=float(max_pr_val),
            step=0.01, format="%.4f", key="min_pr_threshold", on_change=save_pref, args=("min_pr_threshold",)
        )
        max_power_threshold = None
        if power_col in df.columns:
            min_pwr = float(df[power_col].min())
            max_pwr = float(df[power_col].max())
            power_input_max = math.ceil(max_pwr) + 1
            if st.sidebar.checkbox("启用最大功率阈值", value=False):
                max_power_threshold = st.sidebar.number_input(
                    "最大功率阈值 (kW)",
                    min_value=float(min_pwr), max_value=float(power_input_max),
                    value=float(power_input_max), step=0.1, format="%.2f"
                )

        # ─── 过滤计算 ─────────────────────────────────────────────────────────────
        filtered_df, surge_line_df, peak_info = filter_operating_points(
            df, flow_col="display_flow", pressure_col=pressure_raw_col,
            min_pressure=min_pr_threshold, max_power=max_power_threshold, power_col=power_col
        )
        if filtered_df.empty:
            st.warning("所有数据均被过滤条件剔除，请放宽阈值。"); st.stop()

        with st.sidebar.expander("自动边界截断与喘振点诊断", expanded=False):
            st.markdown("**检测到的真实数据最高压力点 (截断基准):**")
            for spd, info in peak_info.items():
                st.text(f"{spd} RPM: 取最大值 PR={info['pressure']:.4f} @ Flow={info['flow']:.4f}")
            st.markdown("*注：系统自动舍去了流量小于最高压力点的所有「压降」散点数据。图表中曲线在最高压力点左侧的下垂，通常是由于插值算法(Spline)在平滑连接时的视觉过冲导致，并非真实残留数据。*")

        # 压力单位换算（显示层）——基于每行入口绝对压力
        filtered_df = filtered_df.copy()
        
        def row_pressure_display(row, mode, vacuum_mode=False):
            pr = row[pressure_raw_col]
            p_in = row.get("p_in_pa", 101325.0)
            if mode == "delta_kPa":
                if vacuum_mode:
                    # 真空模式：显示进口表压（负小数 = 真空度）
                    return (p_in - 101325.0) / 1000.0  # Pa → kPa ，得到负小数
                else:
                    return (pr - 1.0) * (p_in / 1000.0)
            elif mode == "abs_kPa":
                return pr * (p_in / 1000.0)
            else:
                return pr

        filtered_df["display_pressure"] = filtered_df.apply(
            lambda row: row_pressure_display(row, pressure_mode, is_vacuum), axis=1
        )
        if not surge_line_df.empty:
            surge_line_df = surge_line_df.copy()
            surge_line_df["display_pressure"] = surge_line_df.apply(
                lambda row: row_pressure_display(row, pressure_mode, is_vacuum), axis=1
            )

        # ─── 显示选项 ─────────────────────────────────────────────────────────────
        st.sidebar.markdown("---")
        st.sidebar.subheader("显示选项")
        show_power = st.sidebar.checkbox("显示功率曲线", key="show_power", on_change=save_pref, args=("show_power",))

        show_efficiency  = False
        eff_contour_step = 2.0
        if has_efficiency:
            show_efficiency = st.sidebar.checkbox(
                "显示等效率曲线 & BEP", value=False,
                help="叠加等效率等值线并标注 BEP"
            )
            if show_efficiency:
                step_label = st.sidebar.radio("等效率线间距", ["2%", "5%"], horizontal=True)
                eff_contour_step = 2.0 if step_label == "2%" else 5.0
        else:
            st.sidebar.info("CSV 缺少效率相关列，无法显示等效率线。")

        # ─── 曲线平滑度与 X 轴范围 (已精简) ──────────────────────────────────────────────
        perf_smooth = 3.0
        eff_smooth = 5.0
        final_df = filtered_df.copy()
        # ─── 绘图容器 ──────────────────────────────────────────────────────────────
        plot_container = st.container(border=True)
        if final_df.empty:
            plot_container.warning("当前流量范围内没有数据，请调整X轴显示范围。")
        else:
            _chart_title = getattr(uploaded_file, "name", "") if uploaded_file else ""
            fig = create_performance_curve(
                final_df, surge_line_df,
                x_col="display_flow", y1_col="display_pressure", y2_col=power_col,
                x_label=f"流量 ({flow_unit})", y1_label=y1_label, y2_label="轴功率 (kW)",
                perf_smooth=perf_smooth,
                eff_smooth=eff_smooth,
                show_power=show_power,
                show_efficiency=show_efficiency,
                eff_contour_step=eff_contour_step,
                chart_title=_chart_title,
            )
            plot_container.plotly_chart(fig, use_container_width=True)
            
            # 白底导出下载按鈕（国标顺时针：白底、图例在下）
            try:
                import plotly.io as pio
                _fig_export = create_performance_curve_export(fig)
                _png_bytes = pio.to_image(_fig_export, format="png", width=1200, height=750, scale=2)
                _fname_stem = _chart_title.rsplit(".", 1)[0] if "." in _chart_title else _chart_title
                _dl_name = f"{_fname_stem}_风机性能曲线图.png" if _fname_stem else "风机性能曲线图.png"
                plot_container.download_button(
                    label="⬇️ 下载白底高清 PNG（国标截图版：图例在下）",
                    data=_png_bytes,
                    file_name=_dl_name,
                    mime="image/png"
                )
            except Exception as e:
                plot_container.warning(f"⚠️ 生成白底高清图失败: {str(e)}。请确保已安装 kaleido==0.2.1")
                plot_container.info("💡 鼠标悬停在图表右上角 → 相机图标 → 下载普通版 PNG")

        # ─── 统计容器 ──────────────────────────────────────────────────────────────
            stat_container = st.container(border=True)
            stat_container.subheader("📊 统计概览区")

            if has_efficiency and "efficiency" in final_df.columns:
                # 全局 BEP
                bep_row = final_df.loc[final_df["efficiency"].idxmax()]
                ns_global = calc_specific_speed(bep_row['speed_rpm'], bep_row['display_flow'], flow_unit, bep_row[pressure_raw_col])

                stat_container.markdown("**🌍 全局最高效率点 (Global BEP)**")
                c1, c2, c3, c4, c5 = stat_container.columns(5)
                c1.metric("🏆 最高效率", f"{bep_row['efficiency']*100:.1f}%")
                c2.metric("标准流量", f"{bep_row['display_flow']:.3f}")
                c3.metric(y1_label, f"{bep_row['display_pressure']:.4f}")
                c4.metric("所属转速", f"{int(bep_row['speed_rpm'])} RPM")
                c5.metric("比转速 (Ns)", f"{ns_global:.1f}")

                # 最高转速 BEP
                max_rpm = final_df["speed_rpm"].max()
                max_rpm_df = final_df[final_df["speed_rpm"] == max_rpm]
                if not max_rpm_df.empty:
                    max_bep_row = max_rpm_df.loc[max_rpm_df["efficiency"].idxmax()]
                    ns_max = calc_specific_speed(max_bep_row['speed_rpm'], max_bep_row['display_flow'], flow_unit, max_bep_row[pressure_raw_col])

                    stat_container.markdown(f"**🚀 最高转速工况 ({int(max_rpm)} RPM)**")
                    rc1, rc2, rc3, rc4, rc5 = stat_container.columns(5)
                    rc1.metric("🏆 最高效率", f"{max_bep_row['efficiency']*100:.1f}%")
                    rc2.metric("标准流量", f"{max_bep_row['display_flow']:.3f}")
                    rc3.metric(y1_label, f"{max_bep_row['display_pressure']:.4f}")
                    rc4.metric("所属转速", f"{int(max_bep_row['speed_rpm'])} RPM")
                    rc5.metric("比转速 (Ns)", f"{ns_max:.1f}")

                stat_container.caption(f"效率数据来源：{eff_source} | 比转速 Ns 公式采用国内压缩机标准绝热头算法")

            with stat_container.expander("📋 查看当前渲染的数据表"):
                display_cols = ["speed_rpm", "display_flow", "display_pressure"]
                if power_col in final_df.columns: display_cols.append(power_col)
                if "efficiency" in final_df.columns: display_cols.append("efficiency")
                show_df = final_df[display_cols].copy()
                if "efficiency" in show_df.columns:
                    show_df["efficiency"] = (show_df["efficiency"] * 100).round(2)
                st.dataframe(show_df.rename(columns={
                    "speed_rpm": "转速 (RPM)", "display_flow": f"流量 ({flow_unit})",
                    "display_pressure": y1_label, power_col: "轴功率 (kW)", "efficiency": "等熵效率 [%]"
                }))
    elif page_mode == "轴向力深度分析":
        from force_calculator import calculate_backplate_force, calculate_total_axial_force
        
        st.subheader("⚙️ 轴向力深度分析")
        
        # --- 真空度展示 ---
        if not df.empty and "p_in_pa" in df.columns:
            avg_p_in = df["p_in_pa"].mean()
            if avg_p_in < 101000.0:
                st.error(f"🌌 **真空/负压模式激活**：检测到数据集入口压力低于海平面。当前基准入口绝对压力约为 {avg_p_in:.0f} Pa")
            else:
                st.info(f"🌍 **标准环境模式**：当前基准入口绝对压力约为 {avg_p_in:.0f} Pa")
        
        # 侧边栏参数表单
        st.sidebar.markdown("---")
        st.sidebar.subheader("几何与构型参数")
        
        p_ambient = st.sidebar.number_input(
            "环境大气压 P_amb (Pa) (Absolute Pressure)", value=st.session_state.get("p_ambient_pa", 101325.0), 
            key="p_ambient_pa", on_change=save_pref, args=("p_ambient_pa",),
            help="针对真空泵应用，进口压力是决定轴向力绝对值的核心基准。若 CSV 未提供，系统将按标准海平面工况模拟。"
        )
        d_impeller = st.sidebar.number_input(
            "叶轮外径 D_imp (mm)", value=st.session_state.get("d_imp_mm", 500.0), 
            key="d_imp_mm", on_change=save_pref, args=("d_imp_mm",)
        )
        d_shaft = st.sidebar.number_input(
            "主轴直径 D_in (mm)", value=st.session_state.get("d_shaft_mm", 100.0), 
            key="d_shaft_mm", on_change=save_pref, args=("d_shaft_mm",),
            help="默认的内侧轴封位置边界。"
        )
        
        bp_hole_options = ["无平衡孔", "叶轮盲孔 (内连通入口)", "机壳穿孔 (外连通大气)"]
        hole_type = st.sidebar.selectbox(
            "平衡孔类型与位置", bp_hole_options, 
            index=bp_hole_options.index(st.session_state.get("hole_type", "无平衡孔")) if st.session_state.get("hole_type", "无平衡孔") in bp_hole_options else 0,
            key="hole_type", on_change=save_pref, args=("hole_type",)
        )
        has_bp_holes = hole_type != "无平衡孔"
        
        # 若有平衡孔，强制自动联动第2道密封
        target_seal2_val = True if has_bp_holes else st.session_state.get("has_seal2", False)
        
        has_seal2 = st.sidebar.checkbox(
            "启用第2道密封 (背板外侧)", value=target_seal2_val, 
            key="has_seal2", on_change=save_pref, args=("has_seal2",),
            disabled=has_bp_holes,
            help="若开启平衡孔，必须拥有第2道密封来维系独立的压力腔室。" if has_bp_holes else "位于背板外侧的辅助密封，切断高压区，显著改变压力积分区间。"
        )
        if has_bp_holes: has_seal2 = True
        
        d_seal2 = 0.0
        if has_seal2:
            d_seal2 = st.sidebar.number_input(
                "第2道密封直径 D_s2 (mm)", value=st.session_state.get("d_seal2_mm", 300.0), 
                key="d_seal2_mm", on_change=save_pref, args=("d_seal2_mm",),
                help="位于背板外侧的辅助密封，切断高压区，显著改变压力积分区间。"
            )
        
        d_hole = 0.0
        a_hole = 0.0
        alpha_hole = 0.3
        k_factor = 0.15
        
        if has_bp_holes:
            d_hole = st.sidebar.number_input(
                "平衡孔分布直径 D_hole (mm)", value=st.session_state.get("d_hole_mm", 200.0), 
                key="d_hole_mm", on_change=save_pref, args=("d_hole_mm",),
                help="平衡孔所在圆周的直径。该处的压力会被泄压拉低，进而影响整个内腔的压力梯级基准。"
            )
            a_hole = st.sidebar.number_input(
                "平衡孔总面积 A_hole (mm²)", value=st.session_state.get("a_hole_mm2", 1500.0), 
                key="a_hole_mm2", on_change=save_pref, args=("a_hole_mm2",),
                help="影响泄压效果的关键几何参数，面积越大内腔压力越趋近于泄压孔所连通的区域气压。"
            )
            alpha_hole = st.sidebar.number_input(
                "泄压系数 α", min_value=0.0, max_value=1.0, value=st.session_state.get("alpha_hole", 0.3), step=0.05,
                key="alpha_hole", on_change=save_pref, args=("alpha_hole",),
                help="反映平衡孔流动阻力与压力平衡能力的工程修正值。"
            )
            
        k_factor = st.sidebar.number_input(
            "流体旋转因子 k", min_value=0.0, max_value=1.0, value=st.session_state.get("k_factor", 0.15), step=0.05,
            key="k_factor", on_change=save_pref, args=("k_factor",),
            help="背板腔体流体角速度与叶轮角速度之比，决定径向压力下降梯度。"
        )
        
        if "axial_force" not in df.columns:
            st.warning("⚠️ 你的 CSV 数据中未提供 '轴向力(N)' 列，无法计算总轴向力。")
        else:
            def row_calc(row):
                rpm = row['speed_rpm']
                # 真空工况：直接从提取的真实物理数据获取绝对入口压力与温度
                p_in_abs = row["p_in_pa"]
                rho = row["rho"]
                
                # 基于气动压比真正推算出口绝对压力
                p_out_abs = p_in_abs * row[pressure_raw_col]
                
                # 确定目标泄压
                if hole_type == "叶轮盲孔 (内连通入口)":
                    p_target = p_in_abs
                elif hole_type == "机壳穿孔 (外连通大气)":
                    p_target = p_ambient
                else:
                    p_target = p_in_abs
                
                f_bp = calculate_backplate_force(
                    rpm=rpm, 
                    p_out_abs_pa=p_out_abs, 
                    p_in_abs_pa=p_in_abs, 
                    rho=rho,
                    d_impeller_mm=d_impeller, 
                    d_shaft_mm=d_shaft,
                    has_seal2=has_seal2, 
                    d_seal2_mm=d_seal2,
                    has_balance_holes=has_bp_holes,
                    d_hole_mm=d_hole,
                    a_hole_mm2=a_hole,
                    alpha=alpha_hole,
                    p_hole_target_pa=p_target,
                    p_ambient_pa=p_ambient, 
                    k_factor=k_factor
                )
                
                f_blade = row["axial_force"]
                f_tot = calculate_total_axial_force(f_blade, f_bp)
                return pd.Series([f_bp, f_tot])
                
            df[["f_backplate", "f_total"]] = df.apply(row_calc, axis=1)
            
            # 绘图容器
            plot_c = st.container(border=True)
            from plotter import create_axial_force_curve
            fig = create_axial_force_curve(df, "display_flow", "f_total", flow_unit)
            plot_c.plotly_chart(fig, use_container_width=True)
            
            # 统计概览区
            stat_container = st.container(border=True)
            stat_container.subheader("📊 轴向力极值诊断")
            
            # 寻找最大轴向力绝对值
            max_abs_idx = df["f_total"].abs().idxmax()
            max_row = df.loc[max_abs_idx]
            max_force_val = max_row["f_total"]
            dir_str = "指向入口 (即电机 -> 叶轮方向)" if max_force_val > 0 else "推向电机 (即叶轮 -> 电机方向)"
            
            stat_container.markdown(f"**🔥 核心关注点：最大合力工况发生于 {int(max_row['speed_rpm'])} RPM**")
            c1, c2, c3, c4 = stat_container.columns(4)
            c1.metric("最大净合力", f"{abs(max_force_val):.2f} N")
            c2.metric("力系方向", dir_str)
            c3.metric(f"对应流量 ({flow_unit})", f"{max_row['display_flow']:.3f}")
            if "efficiency" in max_row:
                c4.metric("该点效率", f"{max_row['efficiency']*100:.1f}%")
            
            # 动态数据表展示
            with st.expander("📋 查看轴向力计算核心数据", expanded=False):
                show_cols = ["speed_rpm", "display_flow", "axial_force", "f_backplate", "f_total"]
                out_df = df[show_cols].copy()
                st.dataframe(out_df.rename(columns={
                    "speed_rpm": "转速 (RPM)", "display_flow": f"流量 ({flow_unit})",
                    "axial_force": "前板推力 [N] (Motor->Inlet)", 
                    "f_backplate": "背板推力 [N]", 
                    "f_total": "净合力 [N]"
                }))

else:
    st.info("👈 请从左侧导入 CSV 数据文件开始。")
