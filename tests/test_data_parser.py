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
