import math
import streamlit as st
import pandas as pd
from data_parser import (
    normalize_dataframe, convert_flow_units,
    filter_operating_points, convert_pressure_ratio_to_kpa,
    compute_efficiency
)
from plotter import create_performance_curve

st.set_page_config(page_title="Fan Performance Dashboard", layout="wide")
st.title("交互式风机性能曲线数据看板")

AIR_DENSITY_20C = 1.204

# ─── 侧边栏 ───────────────────────────────────────────────────────────────────
st.sidebar.header("控制面板")
uploaded_file = st.sidebar.file_uploader("上传 CFX 结果 (CSV)", type=["csv"])

flow_unit = st.sidebar.selectbox(
    "流量单位", ["kg/s", "m3/h", "m3/min", "CFM"],
    help="体积流量均以 20°C、1 标准大气压（1.204 kg/m³）换算"
)
pressure_display = st.sidebar.selectbox(
    "压力单位", ["压比 (PR)", "差压 (ΔkPa)", "绝对出口压力 (kPa abs)"],
    help="以标准大气压 101.325 kPa 为基准"
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
    min_pr_threshold = st.sidebar.number_input(
        "最低压比阈值", min_value=1.0, max_value=float(max_pr_val),
        value=float(min_pr_val), step=0.01, format="%.4f"
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
    filtered_df, surge_line_df = filter_operating_points(
        df, flow_col="display_flow", pressure_col=pressure_raw_col,
        min_pressure=min_pr_threshold, max_power=max_power_threshold, power_col=power_col
    )
    if filtered_df.empty:
        st.warning("所有数据均被过滤条件剔除，请放宽阈值。"); st.stop()

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
    show_power = st.sidebar.checkbox("显示功率曲线", value=True)

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

    # ─── 绘图 ─────────────────────────────────────────────────────────────────
    st.subheader("性能曲线图")
    if final_df.empty:
        st.warning("当前流量范围内没有数据，请调整X轴显示范围。")
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
        st.plotly_chart(fig, use_container_width=True)

        if show_efficiency and has_efficiency and "efficiency" in final_df.columns:
            bep_row = final_df.loc[final_df["efficiency"].idxmax()]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🏆 BEP 效率", f"{bep_row['efficiency']*100:.1f}%")
            col2.metric(f"流量 (BEP)", f"{bep_row['display_flow']:.3f} {flow_unit}")
            col3.metric("压力 (BEP)", f"{bep_row['display_pressure']:.4f}")
            col4.metric("转速 (BEP)", f"{int(bep_row['speed_rpm'])} RPM")
            st.caption(f"效率数据来源：{eff_source}")

        st.info("💡 鼠标悬停在图表右上角 → 相机图标 → 下载高清 PNG")

        with st.expander("📋 查看当前渲染的数据表"):
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
