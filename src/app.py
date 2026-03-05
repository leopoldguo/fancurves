import streamlit as st
import pandas as pd
from data_parser import normalize_dataframe, convert_flow_units, filter_operating_points
from plotter import create_performance_curve

st.set_page_config(page_title="Fan Performance Dashboard", layout="wide")

st.title("交互式风机性能曲线数据看板")

# 侧边栏
st.sidebar.header("控制面板")
uploaded_file = st.sidebar.file_uploader("上传 CFX 结果 (CSV)", type=["csv"])

flow_unit = st.sidebar.selectbox("流量单位", ["kg/s", "m3/min", "CFM"])
pressure_unit = st.sidebar.selectbox("压力单位", ["kPa", "压比"])

if uploaded_file:
    # 1. 解析数据
    # 使用 gbk 或 utf-8 读取，包含一定容错性（跳过坏行等）
    try:
        raw_df = pd.read_csv(uploaded_file, encoding='gbk')
    except UnicodeDecodeError:
        try:
            raw_df = pd.read_csv(uploaded_file, encoding='utf-8')
        except Exception as e:
            st.error(f"无法读取文件，请确认为标准 CSV 格式: {e}")
            st.stop()
            
    df = normalize_dataframe(raw_df)
    
    if "mass_flow" in df.columns:
        # 为了演示上下文，应用单位转换
        df["display_flow"] = df["mass_flow"].apply(lambda x: convert_flow_units(x, "kg/s", flow_unit))
    else:
        st.error("未能识别流量列，请确保 CSV 包含'进口流量'等关键词。")
        st.stop()
        
    # 允许用户设置最低压力（压比或绝对压力），默认为找到的数据最小值
    left_y_col = "pressure_ratio" if "pressure_ratio" in df.columns else df.columns[1]
    right_y_col = "shaft_power" if "shaft_power" in df.columns else df.columns[2]
            
    min_pressure_val = float(df[left_y_col].min())
    max_pressure_val = float(df[left_y_col].max())
    min_pressure_threshold = st.sidebar.number_input("最低压力/压比阈值", min_value=0.0, max_value=max_pressure_val, value=min_pressure_val)
    
    # 1. 喘振与压力过滤
    filtered_df, surge_line_df = filter_operating_points(
        df, 
        flow_col="display_flow", 
        pressure_col=left_y_col, 
        min_pressure=min_pressure_threshold
    )
    
    # 防止由于直接删除所有行导致的出错
    if filtered_df.empty:
        st.warning("所有数据均被过滤条件剔除。请降低您的最低压力阈值。")
        st.stop()
        
    # 坐标轴滑块
    min_flow, max_flow = float(filtered_df["display_flow"].min()), float(filtered_df["display_flow"].max())
    flow_range = st.sidebar.slider("X轴显示范围", min_flow, max_flow, (min_flow, max_flow))
    
    mask = (filtered_df["display_flow"] >= flow_range[0]) & (filtered_df["display_flow"] <= flow_range[1])
    final_df = filtered_df.loc[mask]
    
    # 2. 绘图
    st.subheader("性能曲线图")
    
    if final_df.empty:
        st.warning("请调整 X 轴显示范围，当前范围内没有数据可以绘制。")
    else:
        fig = create_performance_curve(
            final_df, 
            surge_line_df,
            x_col="display_flow", 
            y1_col=left_y_col, 
            y2_col=right_y_col,
            x_label=f"流量 ({flow_unit})",
            y1_label=f"压力 ({pressure_unit})",
            y2_label="轴功率 (kW)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. 导出信息
        st.info("提示：将鼠标悬停在上方图表的右上角即可直接使用相机图标下载 PNG 格式的高清图片。")
        
        # 数据集预览功能
        with st.expander("查看当前正在渲染的数据表片段"):
            st.dataframe(final_df)
else:
    st.info("👈 请从左侧导入 CSV 数据文件开始。")
