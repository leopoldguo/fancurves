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
    val_kg_s = 1.225
    val_m3_min = convert_flow_units(val_kg_s, from_unit="kg/s", to_unit="m3/min", density=1.225)
    assert round(val_m3_min, 2) == 60.00
    
    val_cfm = convert_flow_units(1.0, from_unit="m3/min", to_unit="CFM")
    assert round(val_cfm, 2) == 35.31

from src.data_parser import filter_operating_points

def test_filter_operating_points_with_interpolation():
    # Test pressure threshold interpolation
    df = pd.DataFrame({
        "speed_rpm": [1000, 1000],
        "display_flow": [10.0, 20.0],
        "pressure_ratio": [1.2, 1.0], # Segment crosses 1.1
        "shaft_power": [100, 200]
    })
    
    # Target min_pressure = 1.1. Middle should be interpolated.
    # p = 1.1 is halfway between 1.2 and 1.0. 
    # Flow should be halfway between 10 and 20 -> 15.0
    # Power should be halfway between 100 and 200 -> 150.0
    
    filtered_df, surge_line_df = filter_operating_points(df, flow_col="display_flow", pressure_col="pressure_ratio", min_pressure=1.1)
    
    # Should have p=1.2 (inside) and p=1.1 (interpolated)
    assert len(filtered_df) == 2
    assert any(abs(v - 1.1) < 1e-4 for v in filtered_df["pressure_ratio"].values)
    assert any(abs(v - 15.0) < 1e-4 for v in filtered_df["display_flow"].values)
    assert any(abs(v - 150.0) < 1e-4 for v in filtered_df["shaft_power"].values)

def test_filter_operating_points_with_surge_interpolation():
    # Operating data
    # We provide points that will form anchors:
    # 1000 RPM: max p=1.0 at f=1.0, anchor: p=1.0, f=0.95
    # 1500 RPM: max p=2.0 at f=0.0, anchor: p=2.0, f=0.0
    # 2000 RPM: max p=2.0 at f=2.0, anchor: p=2.0, f=1.9
    
    # Auto-surge bounds anchors.
    # Line between 1000 RPM anchor (1.0, 0.95) and 2000 RPM anchor (2.0, 1.9):
    # m = (1.9 - 0.95)/(2.0 - 1.0) = 0.95, b = 0
    # Line is Q = 0.95 * P (bounds the 1500 RPM perfectly)
    
    # 1500 RPM curve: Q = -2P + 4
    # Intersects Q = 0.95 P -> 0.95 P = -2P + 4 -> 2.95 P = 4 -> P = 1.3559, Q = 1.288
    
    op_df = pd.DataFrame({
        "speed_rpm": [1000, 2000, 1500, 1500],
        "display_flow": [1.0, 2.0, 0.0, 2.0],
        "pressure_ratio": [1.0, 2.0, 2.0, 1.0] 
    })
    
    filtered_df, surge_line_df = filter_operating_points(op_df, flow_col="display_flow", pressure_col="pressure_ratio", min_pressure=0.0)
    
    speed_1500 = filtered_df[filtered_df["speed_rpm"] == 1500]
    assert len(speed_1500) == 2
    
    # Check if interpolated point exists (f approx 1.288)
    assert any(abs(v - 1.288) < 0.01 for v in speed_1500["display_flow"])
