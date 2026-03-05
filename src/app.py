import math
import streamlit as st
import pandas as pd
from data_parser import (
    normalize_dataframe, convert_flow_units,
    filter_operating_points, convert_pressure_ratio_to_kpa,
    compute_efficiency
)
from plotter import create_performance_curve

import json
import os

st.set_page_config(page_title="Fan Performance Dashboard", layout="wide")

st.markdown("""
<style>
    /* Industrial Theme CSS Injection */
    .stMetricValue, .stNumberInput input, .stSlider div[role="slider"] {
        font-family: 'Roboto Mono', 'Courier New', monospace !important;
    }
    /* Safety Orange for Sliders and Accents */
    .stSlider div[data-baseweb="slider"] div {
        background-color: #FF8C00 !important;
    }
    h1, h2, h3 {
        color: #E0E0E0 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎛️ 交互式风机性能曲线数据看板 (Industrial)")

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
        "show_power": True
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
st.sidebar.header("控制面板")
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

    df["display_flow"] = df["mass_flow"].apply(
        lambda x: convert_flow_units(x, "kg/s", flow_unit, density=AIR_DENSITY_20C)
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

    # ─── 过滤阈值 ─────────────────────────────────────────────────────────────
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

    # 压力单位换算（显示层）
    filtered_df = filtered_df.copy()
    filtered_df["display_pressure"] = convert_pressure_ratio_to_kpa(
        filtered_df[pressure_raw_col], pressure_mode
    )
    if not surge_line_df.empty:
        surge_line_df = surge_line_df.copy()
        surge_line_df["display_pressure"] = convert_pressure_ratio_to_kpa(
            surge_line_df[pressure_raw_col], pressure_mode
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

    # ─── 曲线平滑度（分开控制） ───────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.subheader("曲线平滑度")
    perf_smooth = st.sidebar.slider(
        "性能曲线平滑强度",
        min_value=0.0, max_value=10.0, value=3.0, step=0.5,
        help="控制压力/功率拟合曲线的平滑度（0=精确过点，10=最高平滑）"
    )
    eff_smooth = st.sidebar.slider(
        "等效率线平滑强度",
        min_value=0.0, max_value=10.0, value=5.0, step=0.5,
        help="控制等效率等值线的圆滑程度（值越大越偏离原始网格，越圆润）",
        disabled=not show_efficiency
    )

    # ─── X 轴范围 ────────────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    min_flow = float(filtered_df["display_flow"].min())
    max_flow = float(filtered_df["display_flow"].max())
    flow_range = st.sidebar.slider(
        f"X轴流量显示范围 ({flow_unit})", min_flow, max_flow, (min_flow, max_flow)
    )
    mask = (
        (filtered_df["display_flow"] >= flow_range[0]) &
        (filtered_df["display_flow"] <= flow_range[1])
    )
    final_df = filtered_df.loc[mask]
    # ─── 绘图容器 ──────────────────────────────────────────────────────────────
    plot_container = st.container(border=True)
    plot_container.subheader("📈 动态绘图主区")
    if final_df.empty:
        plot_container.warning("当前流量范围内没有数据，请调整X轴显示范围。")
    else:
        fig = create_performance_curve(
            final_df, surge_line_df,
            x_col="display_flow", y1_col="display_pressure", y2_col=power_col,
            x_label=f"流量 ({flow_unit})", y1_label=y1_label, y2_label="轴功率 (kW)",
            perf_smooth=perf_smooth,
            eff_smooth=eff_smooth,
            show_power=show_power,
            show_efficiency=show_efficiency,
            eff_contour_step=eff_contour_step,
        )
        plot_container.plotly_chart(fig, use_container_width=True)
        plot_container.info("💡 鼠标悬停在图表右上角 → 相机图标 → 下载高清 PNG")

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
else:
    st.info("👈 请从左侧导入 CSV 数据文件开始。")
