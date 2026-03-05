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
