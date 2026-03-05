import pandas as pd

HEADER_MAP = {
    "进口流量": "mass_flow",
    "压比": "pressure_ratio",
    "轴功率": "shaft_power",
    "设定转速": "speed_rpm"
}

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """将 CFX CSV 的中文表头标准化为内部统一的英文键。"""
    df_clean = df.copy()
    # 去除列名的前后空格，以防万一
    df_clean.columns = df_clean.columns.str.strip()
    
    # 重命名匹配的列
    rename_dict = {}
    for col in df_clean.columns:
        for ch_key, en_key in HEADER_MAP.items():
            if ch_key in col:  # 允许部分匹配 (例如: "质量流量 (kg/s)")
                rename_dict[col] = en_key
                break
                
    return df_clean.rename(columns=rename_dict)

def convert_flow_units(value: float, from_unit: str, to_unit: str, density: float = 1.225) -> float:
    """在 kg/s, m3/min 和 CFM 之间转换流量单位。"""
    if from_unit == to_unit:
        return value
        
    # 首先将所有单位转换为 m3/min 作为基准
    m3_min = value
    if from_unit == "kg/s":
        m3_min = (value / density) * 60.0
    elif from_unit == "CFM":
        m3_min = value / 35.3146667
        
    # 从基准单位转换到目标单位
    if to_unit == "m3/min":
        return m3_min
    elif to_unit == "kg/s":
        return (m3_min / 60.0) * density
    elif to_unit == "CFM":
        return m3_min * 35.3146667
        
    raise ValueError(f"不支持的单位转换: {from_unit} 到 {to_unit}")

def filter_operating_points(df: pd.DataFrame, flow_col: str, pressure_col: str, min_pressure: float):
    # 1. 找到各个转速下的喘振点 (假设为质量流量最小的点)
    surge_points = []
    
    # 确保转速列存在，否则直接返回
    if "speed_rpm" not in df.columns:
        return df, pd.DataFrame()
        
    for speed in df["speed_rpm"].unique():
        speed_df = df[df["speed_rpm"] == speed]
        # 找到该转速下流量最小的行
        surge_row = speed_df.loc[speed_df[flow_col].idxmin()]
        surge_points.append(surge_row)
        
    surge_df = pd.DataFrame(surge_points).sort_values(by="speed_rpm")
    
    # 提取最低转速和最高转速的喘振点建立喘振线，或者使用所有的喘振点本身（通常直接使用线段连接）
    if len(surge_df) >= 2:
        # 用户需求：以最高转速的喘振点和最低转速的喘振点拉一条直线
        min_surge = surge_df.iloc[0]
        max_surge = surge_df.iloc[-1]
        
        flow_min, p_min = min_surge[flow_col], min_surge[pressure_col]
        flow_max, p_max = max_surge[flow_col], max_surge[pressure_col]
        
        # 直线方程: flow = m * pressure + b
        if p_max != p_min:
            m = (flow_max - flow_min) / (p_max - p_min)
            b = flow_min - m * p_min
            
            # 使用直线方程过滤：要求 flow >= 计算出的喘振边界 flow
            # 也就意味着在“喘振线右侧”
            df = df[df[flow_col] >= (m * df[pressure_col] + b)]
            
            # 喘振线的作图数据
            surge_line_df = pd.DataFrame({
                flow_col: [flow_min, flow_max],
                pressure_col: [p_min, p_max]
            })
        else:
            surge_line_df = surge_df
    else:
        surge_line_df = surge_df
        
    # 2. 最低压力过滤
    df = df[df[pressure_col] >= min_pressure]
    
    return df, surge_line_df
