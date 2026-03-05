import pandas as pd
from src.data_parser import normalize_dataframe

def test_normalize_dataframe_headers():
    data = {"进口流量(kg/s)": [1.2], "压比": [1.05], "轴功率(kW)": [0.85], "设定转速(RPM)": [24000]}
    df = pd.DataFrame(data)
    normalized_df = normalize_dataframe(df)
    
    assert "mass_flow" in normalized_df.columns
    assert "pressure_ratio" in normalized_df.columns
    assert "shaft_power" in normalized_df.columns
    assert "speed_rpm" in normalized_df.columns

from src.data_parser import convert_flow_units

def test_convert_flow_units():
    # 1 kg/s 转换到 m^3/min (假设标准空气密度 ~1.225 kg/m^3，或作为特定配置传入)
    # 因为密度可变，我们可以测试一个标称转换或者将密度作为参数传入。
    # 对于 CFM: 1 m^3/min = 35.3147 CFM
    val_kg_s = 1.225
    val_m3_min = convert_flow_units(val_kg_s, from_unit="kg/s", to_unit="m3/min", density=1.225)
    assert round(val_m3_min, 2) == 60.00
    
    val_cfm = convert_flow_units(1.0, from_unit="m3/min", to_unit="CFM")
    assert round(val_cfm, 2) == 35.31
