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
