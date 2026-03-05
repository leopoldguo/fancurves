import pandas as pd
from src.plotter import create_performance_curve

def test_create_performance_curve_returns_figure():
    df = pd.DataFrame({
        "speed_rpm": [1000, 1000, 2000],
        "mass_flow": [1.0, 1.5, 2.0],
        "pressure_ratio": [1.5, 1.4, 1.2],
        "shaft_power": [5.0, 6.2, 7.5]
    })
    
    surge_df = pd.DataFrame({
        "mass_flow": [1.0, 2.0],
        "pressure_ratio": [1.5, 1.2]
    })
    
    fig = create_performance_curve(
        df, 
        surge_df,
        x_col="mass_flow", 
        y1_col="pressure_ratio", 
        y2_col="shaft_power",
        x_label="Flow (kg/s)",
        y1_label="Pressure Ratio",
        y2_label="Shaft Power (kW)"
    )
    
    # 断言返回的是 Plotly 图形对象
    assert fig.__class__.__name__ == "Figure"
    # 断言已配置双轴
    assert any(axis.title.text == "Shaft Power (kW)" for axis in fig.layout.values() if hasattr(axis, 'title'))
