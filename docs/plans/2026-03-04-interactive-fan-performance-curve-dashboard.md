# 交互式风机性能曲线数据看板 - 实施计划

> **给 Claude 的提示:** 必需的子技能 (REQUIRED SUB-SKILL): 使用 `superpowers:executing-plans` 逐项执行此计划。

**目标 (Goal):** 构建一个轻量级的 Streamlit Web 应用，用于解析 CFX 导出的 CSV 结果数据，并动态呈现高保真、交互式的风机性能曲线。

**架构 (Architecture):** 
1. **前端应用 (`src/app.py`)**: 包含文件上传器、侧边栏控制项和主显示区域的 Streamlit 用户界面。
2. **数据解析器 (`src/data_parser.py`)**: 基于 Pandas 的模块，用于读取 CSV，将中文表头标准化（例如“质量流量” -> “mass_flow”），并进行单位转换。
3. **绘图器 (`src/plotter.py`)**: 基于 Plotly 的渲染器，用于创建适合工程报告的双 Y 轴图表（流量与压比、功率的关系）。

**技术栈 (Tech Stack):** Python, Streamlit, Pandas, Plotly, Pytest

---

### 任务 1：项目骨架与依赖项

**文件:**
- 创建: `requirements.txt`
- 创建: `src/__init__.py`
- 创建: `tests/__init__.py`

**第 1 步：定义依赖项**

创建包含以下内容的 `requirements.txt`：
```text
streamlit>=1.30.0
pandas>=2.0.0
plotly>=5.18.0
pytest>=7.0.0
```

**第 2 步：提交 (Commit)**

```bash
git add requirements.txt src/__init__.py tests/__init__.py
git commit -m "chore: setup initial project structure and dependencies"
```

---

### 任务 2：数据解析器 - 表头标准化 (TDD)

**文件:**
- 创建: `src/data_parser.py`
- 创建: `tests/test_data_parser.py`

**第 1 步：编写失败的测试**

```python
# tests/test_data_parser.py
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
```

**第 2 步：运行测试以验证其失败**

运行: `pytest tests/test_data_parser.py -v`
预期结果: 失败 (FAIL)，提示 `ModuleNotFoundError: No module named 'src'` 或是 `ImportError: cannot import name 'normalize_dataframe'`

**第 3 步：编写最小实现**

```python
# src/data_parser.py
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
```

**第 4 步：运行测试以验证其通过**

运行: `pytest tests/test_data_parser.py -v`
预期结果: 通过 (PASS)

**第 5 步：提交 (Commit)**

```bash
git add src/data_parser.py tests/test_data_parser.py
git commit -m "feat: implement CSV header normalization for CFX data"
```

---

### 任务 3：数据解析器 - 单位转换 (TDD)

**文件:**
- 修改: `src/data_parser.py`
- 修改: `tests/test_data_parser.py`

**第 1 步：编写失败的测试**

```python
# 补充到 tests/test_data_parser.py
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
```

**第 2 步：运行测试以验证其失败**

运行: `pytest tests/test_data_parser.py::test_convert_flow_units -v`
预期结果: 失败 (FAIL)

**第 3 步：编写最小实现**

```python
# 补充到 src/data_parser.py

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
```

**第 4 步：运行测试以验证其通过**

运行: `pytest tests/test_data_parser.py::test_convert_flow_units -v`
预期结果: 通过 (PASS)

**第 5 步：提交 (Commit)**

```bash
git add src/data_parser.py tests/test_data_parser.py
git commit -m "feat: add robust unit conversion for flow rates"
```

---

### 任务 4：数据处理 - 喘振线与最低压力过滤 (TDD)

**文件:**
- 修改: `src/data_parser.py`
- 修改: `tests/test_data_parser.py`

**第 1 步：编写失败的测试**

```python
# 补充到 tests/test_data_parser.py
from src.data_parser import filter_operating_points

def test_filter_operating_points():
    df = pd.DataFrame({
        "speed_rpm": [1000, 1000, 2000, 2000],
        "display_flow": [0.5, 1.0, 1.5, 2.0],
        "pressure_ratio": [1.2, 1.1, 1.8, 1.5]
    })
    
    # 喘振点将通过最低流量找到：1000转 (0.5, 1.2), 2000转 (1.5, 1.8)
    # 假设我们设定最低压比为 1.15，那么点 (1.0, 1.1) 应该被过滤掉
    
    filtered_df, surge_line_df = filter_operating_points(df, flow_col="display_flow", pressure_col="pressure_ratio", min_pressure=1.15)
    
    assert len(filtered_df) == 3
    assert 1.1 not in filtered_df["pressure_ratio"].values
    
    # 检查喘振线是否包含两个点
    assert len(surge_line_df) == 2
```

**第 2 步：运行测试以验证其失败**

运行: `pytest tests/test_data_parser.py::test_filter_operating_points -v`
预期结果: 失败 (FAIL)

**第 3 步：编写最小实现**

```python
# 补充到 src/data_parser.py

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
```

**第 4 步：运行测试以验证其通过**

运行: `pytest tests/test_data_parser.py::test_filter_operating_points -v`
预期结果: 通过 (PASS)

**第 5 步：提交 (Commit)**

```bash
git add src/data_parser.py tests/test_data_parser.py
git commit -m "feat: add surge line interpolation and minimum pressure filtering"
```

---

### 任务 5：绘图器模块 (TDD)

**文件:**
- 创建: `src/plotter.py`
- 创建: `tests/test_plotter.py`

**第 1 步：编写失败的测试**

```python
# tests/test_plotter.py
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
```

**第 2 步：运行测试以验证其失败**

运行: `pytest tests/test_plotter.py -v`
预期结果: 失败 (FAIL)

**第 3 步：编写最小实现**

```python
# src/plotter.py
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
```

**第 4 步：运行测试以验证其通过**

运行: `pytest tests/test_plotter.py -v`
预期结果: 通过 (PASS)

**第 5 步：提交 (Commit)**

```bash
git add src/plotter.py tests/test_plotter.py
git commit -m "feat: implement dual-Y Plotly chart generation"
```

---

### 任务 6：Streamlit 应用 UI

**文件:**
- 创建: `src/app.py`

*由于 UI 是视觉上的，我们编写应用代码并通过浏览器进行手动测试。*

**第 1 步：编写 UI 代码**

```python
# src/app.py
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
    raw_df = pd.read_csv(uploaded_file)
    df = normalize_dataframe(raw_df)
    
    if "mass_flow" in df.columns:
        # 为了演示上下文，应用模拟的单位转换
        df["display_flow"] = df["mass_flow"].apply(lambda x: convert_flow_units(x, "kg/s", flow_unit))
    else:
        st.error("未能识别流量列，请确保 CSV 包含'进口流量'等关键词。")
        st.stop()
        
    # 允许用户设置最低压力（压比或绝对压力），默认为找到的数据最小值
    # 根据用户提到的“压比或绝对压力”，这里我们使用实际存在的列
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
    
    # 坐标轴水平过滤
    min_flow, max_flow = float(filtered_df["display_flow"].min()), float(filtered_df["display_flow"].max())
    flow_range = st.sidebar.slider("X轴显示范围", min_flow, max_flow, (min_flow, max_flow))
    
    mask = (filtered_df["display_flow"] >= flow_range[0]) & (filtered_df["display_flow"] <= flow_range[1])
    final_df = filtered_df.loc[mask]
    
    # 2. 绘图
    st.subheader("性能曲线图")
    
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
    
    # 3. 导出
    # Plotly Modebar 提供了原生支持，但是如果需要特定的格式，我们可以添加 Streamlit 的下载按钮。
    st.info("提示：将鼠标悬停在图表右上角即可直接下载 PNG 格式的高清图片。")
else:
    st.info("请从左侧导入 CSV 数据文件开始。")
```

**第 2 步：运行手动测试**

运行: `streamlit run src/app.py`
预期结果: Streamlit 应用在本地启动。上传一个样本 CSV，验证单位下拉菜单和滑块功能，并确保证图表渲染清晰。

**第 3 步：提交 (Commit)**

```bash
git add src/app.py
git commit -m "feat: build active streamlit frontend app"
```

---

### 任务 7：GitHub Actions 工作流

**文件:**
- 创建: `.github/workflows/test.yml`

**第 1 步：编写测试实现**

```yaml
# .github/workflows/test.yml
name: Python Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run Pytest
      run: pytest tests/ -v
```

**第 2 步：提交 (Commit)**

```bash
git add .github/workflows/test.yml
git commit -m "ci: add github actions for test automation"
```
