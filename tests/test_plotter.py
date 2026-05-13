import pandas as pd
from src.plotter import create_performance_curve, create_performance_curve_export, create_performance_report_png

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
    assert fig.layout.yaxis2.title.text == "Shaft Power (kW)"
    assert fig.layout.legend.orientation == "h"
    assert fig.layout.legend.x == 0.5
    assert fig.layout.height >= 500

def test_create_performance_curve_uses_custom_subtitle():
    df = pd.DataFrame({
        "speed_rpm": [1000, 1000],
        "mass_flow": [1.0, 1.5],
        "pressure_ratio": [1.5, 1.4],
        "shaft_power": [5.0, 6.2],
    })

    fig = create_performance_curve(
        df,
        pd.DataFrame(),
        x_col="mass_flow",
        y1_col="pressure_ratio",
        y2_col="shaft_power",
        chart_title="sample.csv",
        chart_subtitle="Performance Curve",
    )

    assert "Performance Curve" in fig.layout.title.text

def test_create_performance_curve_export_adds_summary_without_render_date():
    df = pd.DataFrame({
        "speed_rpm": [1000, 1000],
        "mass_flow": [1.0, 1.5],
        "pressure_ratio": [1.5, 1.4],
        "shaft_power": [5.0, 6.2],
    })
    fig = create_performance_curve(
        df,
        pd.DataFrame(),
        x_col="mass_flow",
        y1_col="pressure_ratio",
        y2_col="shaft_power",
    )

    export_fig = create_performance_curve_export(
        fig,
        summary_lines=["Global BEP: 81.4%", "Highest Speed Case: 78.0%"],
    )
    annotation_text = "\n".join(str(ann.text) for ann in export_fig.layout.annotations)

    assert "Global BEP" in annotation_text
    assert "Highest Speed Case" in annotation_text
    assert "render date" not in annotation_text.lower()
    assert export_fig.layout.height > fig.layout.height

def test_create_performance_report_png_returns_png_bytes():
    df = pd.DataFrame({
        "speed_rpm": [1000, 1000, 2000, 2000],
        "mass_flow": [1.0, 1.5, 1.1, 1.6],
        "pressure_ratio": [1.5, 1.4, 1.7, 1.55],
        "shaft_power": [5.0, 6.2, 7.0, 8.3],
    })

    png = create_performance_report_png(
        df,
        pd.DataFrame({"mass_flow": [1.0, 1.1], "pressure_ratio": [1.5, 1.7]}),
        x_col="mass_flow",
        y1_col="pressure_ratio",
        y2_col="shaft_power",
        x_label="Flow",
        y1_label="Pressure Ratio",
        y2_label="Power",
        title="Sample",
        subtitle="Performance Curve",
        summary_lines=["Global BEP: 81.4%"],
        show_power=True,
    )

    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(png) > 1000
