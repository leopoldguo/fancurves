import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_performance_curve(
    df: pd.DataFrame, 
    surge_line_df: pd.DataFrame,
    x_col: str, 
    y1_col: str, 
    y2_col: str,
    x_label: str = "Flow Rate",
    y1_label: str = "Pressure Ratio",
    y2_label: str = "Shaft Power"
) -> go.Figure:
    
    # 创建带有第二 Y 轴的子图
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 根据转速分组绘制多条曲线
    if "speed_rpm" in df.columns:
        speeds = df["speed_rpm"].unique()
        for speed in speeds:
            speed_df = df[df["speed_rpm"] == speed]
            
            # 压比 (Pressure Ratio) 迹线
            fig.add_trace(
                go.Scatter(x=speed_df[x_col], y=speed_df[y1_col], name=f'PR @ {speed} RPM', mode='lines+markers', line=dict(shape='spline')),
                secondary_y=False,
            )
            
            # 轴功率 (Shaft Power) 迹线
            fig.add_trace(
                go.Scatter(x=speed_df[x_col], y=speed_df[y2_col], name=f'Power @ {speed} RPM', mode='lines+markers', line=dict(dash='dash', shape='spline')),
                secondary_y=True,
            )
            
    # 添加喘振线 (如果存在的话)
    if not surge_line_df.empty:
        fig.add_trace(
            go.Scatter(x=surge_line_df[x_col], y=surge_line_df[y1_col], name='Surge Line', mode='lines', line=dict(color='black', width=3, dash='dot')),
            secondary_y=False,
        )
    
    # 设置布局格式以实现高保真度的工程外观
    fig.update_layout(
        title_text="Fan Performance Curve",
        plot_bgcolor="white",
        hovermode="x unified"
    )
    
    fig.update_xaxes(title_text=x_label, showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(title_text=y1_label, secondary_y=False, showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(title_text=y2_label, secondary_y=True, showgrid=False)
    
    return fig
