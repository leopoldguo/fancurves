import math
import streamlit as st
import pandas as pd
from data_parser import normalize_dataframe, convert_flow_units, filter_operating_points, convert_pressure_ratio_to_kpa
from plotter import create_performance_curve

st.set_page_config(page_title="Fan Performance Dashboard", layout="wide")
st.title("交互式风机性能曲线数据看板")

# ─── 侧边栏 ───────────────────────────────────────────────────────────────────
st.sidebar.header("控制面板")
uploaded_file = st.sidebar.file_uploader("上传 CFX 结果 (CSV)", type=["csv"])

# 空气密度常量（20°C, 1 atm）
AIR_DENSITY_20C = 1.204  # kg/m³

flow_unit = st.sidebar.selectbox(
    "流量单位",
    ["kg/s", "m3/h", "m3/min", "CFM"],
    help="体积流量均以 20°C、1 标准大气压下的空气密度 1.204 kg/m³ 换算"
)

pressure_display = st.sidebar.selectbox(
    "压力单位",
    ["压比 (PR)", "差压 (ΔkPa)", "绝对出口压力 (kPa abs)"],
    help="以标准大气压 101.325 kPa 为基准换算"
)

PRESSURE_MODE_MAP = {
    "压比 (PR)": "pressure_ratio",
    "差压 (ΔkPa)": "delta_kPa",
    "绝对出口压力 (kPa abs)": "abs_kPa"
}
PRESSURE_LABEL_MAP = {
    "pressure_ratio": "压比 [-]",
    "delta_kPa": "差压 ΔP [kPa]",
    "abs_kPa": "绝对出口压力 [kPa]"
}
pressure_mode = PRESSURE_MODE_MAP[pressure_display]
y1_label = PRESSURE_LABEL_MAP[pressure_mode]

# ─── 数据上传 ─────────────────────────────────────────────────────────────────
if uploaded_file:
    try:
        try:
            raw_df = pd.read_csv(uploaded_file, encoding='gbk')
        except UnicodeDecodeError:
            raw_df = pd.read_csv(uploaded_file, encoding='utf-8')
    except Exception as e:
        st.error(f"无法读取文件，请确认为标准 CSV 格式: {e}")
        st.stop()

    df = normalize_dataframe(raw_df)

    if "mass_flow" not in df.columns:
        st.error("未能识别流量列，请确保 CSV 包含'进口流量'等关键词。")
        st.stop()

    df["display_flow"] = df["mass_flow"].apply(
        lambda x: convert_flow_units(x, "kg/s", flow_unit, density=AIR_DENSITY_20C)
    )

    pressure_raw_col = "pressure_ratio"
    power_col = "shaft_power"

    if pressure_raw_col not in df.columns:
        st.error("未能识别压力列，请确保 CSV 包含'压比'等关键词。")
        st.stop()

    # ─── 过滤阈值控件 ─────────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.subheader("数据过滤阈值")

    min_pr_val = float(df[pressure_raw_col].min())
    max_pr_val = float(df[pressure_raw_col].max())
    min_pr_threshold = st.sidebar.number_input(
        "最低压比阈值",
        min_value=1.0, max_value=float(max_pr_val),
        value=float(min_pr_val), step=0.01, format="%.4f",
        help="低于此压比的数据点（含喘振线以左）将被裁剪，曲线线段按线性插值延伸至截断位置"
    )

    max_power_threshold = None
    if power_col in df.columns:
        min_pwr = float(df[power_col].min())
        max_pwr = float(df[power_col].max())
        # 最大功率上限取整后加一，方便用户微调到数据内任意值
        power_input_max = math.ceil(max_pwr) + 1
        enable_power_filter = st.sidebar.checkbox("启用最大功率阈值", value=False)
        if enable_power_filter:
            max_power_threshold = st.sidebar.number_input(
                "最大功率阈值 (kW)",
                min_value=float(min_pwr),
                max_value=float(power_input_max),
                value=float(power_input_max),
                step=0.1, format="%.2f",
                help="超过此功率的数据点将被裁剪，曲线延伸至截断位置"
            )

    # ─── 过滤计算 ─────────────────────────────────────────────────────────────
    filtered_df, surge_line_df = filter_operating_points(
        df,
        flow_col="display_flow",
        pressure_col=pressure_raw_col,
        min_pressure=min_pr_threshold,
        max_power=max_power_threshold,
        power_col=power_col
    )

    if filtered_df.empty:
        st.warning("所有数据均被过滤条件剔除，请放宽阈值设置。")
        st.stop()

    # ─── 压力单位换算（显示层，过滤始终用压比） ───────────────────────────────
    filtered_df = filtered_df.copy()
    filtered_df["display_pressure"] = convert_pressure_ratio_to_kpa(
        filtered_df[pressure_raw_col], pressure_mode
    )
    if not surge_line_df.empty:
        surge_line_df = surge_line_df.copy()
        surge_line_df["display_pressure"] = convert_pressure_ratio_to_kpa(
            surge_line_df[pressure_raw_col], pressure_mode
        )

    # ─── 曲线平滑度 ───────────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.subheader("曲线平滑度")
    smooth_level = st.sidebar.slider(
        "平滑强度",
        min_value=0.0, max_value=10.0, value=3.0, step=0.5,
        help=(
            "0 = 精确过每一个 CFD 计算点（可能有锯齿）；"
            "3 = 推荐，自然平滑；"
            "10 = 最高平滑，接近手绘风机图谱效果"
        )
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
        st.warning("当前流量范围内没有数据，请调整 X 轴显示范围。")
    else:
        fig = create_performance_curve(
            final_df,
            surge_line_df,
            x_col="display_flow",
            y1_col="display_pressure",
            y2_col=power_col,
            x_label=f"流量 ({flow_unit})",
            y1_label=y1_label,
            y2_label="轴功率 (kW)",
            smooth_level=smooth_level,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.info("💡 将鼠标悬停在图表右上角，点击相机图标可下载高清 PNG 图片。")

        with st.expander("📋 查看当前渲染的数据表"):
            display_cols = ["speed_rpm", "display_flow", "display_pressure"]
            if power_col in final_df.columns:
                display_cols.append(power_col)
            st.dataframe(final_df[display_cols].rename(columns={
                "speed_rpm": "转速 (RPM)",
                "display_flow": f"流量 ({flow_unit})",
                "display_pressure": y1_label,
                power_col: "轴功率 (kW)"
            }))
else:
    st.info("👈 请从左侧导入 CSV 数据文件开始。")
