import pandas as pd

HEADER_MAP = {
    "进口流量": "mass_flow",
    "压比": "pressure_ratio",
    "轴功率": "shaft_power",
    "设定转速": "speed_rpm",
    "等熵效率": "efficiency_pct",   # CFX provides this directly (unit: %)
    "轴向力(N)": "axial_force",
    "进口压力": "p_in_pa",
    "进口温度": "t_in_c"
}

P_ATM_KPA       = 101.325    # kPa
P_ATM_PA        = 101325.0   # Pa
AIR_DENSITY_20C = 1.204      # kg/m³ at 20°C, 1 atm

# Isentropic efficiency constants (only used as fallback when CSV lacks η column)
_GAMMA = 1.4
_CP    = 1005.0    # J/(kg·K)
_T_IN  = 293.15    # K = 20°C

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """将 CFX CSV 的中文表头标准化为内部统一的英文键。"""
    df_clean = df.copy()
    df_clean.columns = df_clean.columns.str.strip()
    rename_dict = {}
    for col in df_clean.columns:
        for ch_key, en_key in HEADER_MAP.items():
            if ch_key in col:
                rename_dict[col] = en_key
                break
    df_clean.rename(columns=rename_dict, inplace=True)
    
    if "axial_force" in df_clean.columns:
        # Invert axial force convention: make Motor -> Inlet positive
        df_clean["axial_force"] = -1 * df_clean["axial_force"]
        
    # 动态填补进口状态与密度
    if "p_in_pa" not in df_clean.columns:
        df_clean["p_in_pa"] = 101325.0
    if "t_in_c" not in df_clean.columns:
        df_clean["t_in_c"] = 20.0
        
    # 理想气体状态方程计算当前点密度: rho = P / (R * T)
    # 取空气气体常数 R ≈ 287.058 J/(kg·K)
    df_clean["rho"] = df_clean["p_in_pa"] / (287.058 * (df_clean["t_in_c"] + 273.15))
        
    return df_clean

def convert_flow_units(value: float, from_unit: str, to_unit: str, density: float = AIR_DENSITY_20C) -> float:
    """在 kg/s, m3/min, m3/h, CFM 之间转换流量单位。
    密度默认使用 20°C、1标准大气压的空气密度 1.204 kg/m³。
    """
    if from_unit == to_unit:
        return value
    m3_min = value
    if from_unit == "kg/s":
        m3_min = (value / density) * 60.0
    elif from_unit == "CFM":
        m3_min = value / 35.3146667
    elif from_unit == "m3/h":
        m3_min = value / 60.0
    if to_unit == "m3/min":
        return m3_min
    elif to_unit == "m3/h":
        return m3_min * 60.0
    elif to_unit == "kg/s":
        return (m3_min / 60.0) * density
    elif to_unit == "CFM":
        return m3_min * 35.3146667
    raise ValueError(f"不支持的单位转换: {from_unit} 到 {to_unit}")

def convert_pressure_ratio_to_kpa(pressure_ratio_series: pd.Series, mode: str) -> pd.Series:
    """
    将压比转换为压力单位：
    - 'pressure_ratio'：保持原始压比不变
    - 'delta_kPa'：差压 = (压比 - 1) × 101.325 kPa
    - 'abs_kPa'：绝对出口压力 = 压比 × 101.325 kPa
    """
    if mode == "delta_kPa":
        return (pressure_ratio_series - 1.0) * P_ATM_KPA
    elif mode == "abs_kPa":
        return pressure_ratio_series * P_ATM_KPA
    else:
        return pressure_ratio_series

def compute_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    """
    填入内部统一的 'efficiency' 列（小数，[0,1] 范围）。

    优先级：
    1. 直接使用 CSV 中 CFX 计算好的「等熵效率(%)」列（efficiency_pct），
       除以 100 转为小数。这是最准确的来源，无需重新计算。
    2. 若 CSV 中没有效率列，则用等熵效率公式作为后备：
           η = ṁ · cp · Tin · [(PR)^((γ-1)/γ) - 1] / P_shaft
    """
    result = df.copy()

    # --- 优先：直接从 CSV 中读取 ---
    if "efficiency_pct" in result.columns:
        # CSV stores efficiency as % (e.g. 80.5). Convert to fraction [0, 1].
        result["efficiency"] = pd.to_numeric(result["efficiency_pct"],
                                             errors="coerce").clip(0, 100) / 100.0
        return result

    # --- 后备：isentropic formula ---
    try:
        exponent = (_GAMMA - 1.0) / _GAMMA
        W_is     = (result["mass_flow"]
                    * _CP
                    * _T_IN
                    * (result["pressure_ratio"] ** exponent - 1.0))
        W_shaft  = result["shaft_power"] * 1000.0
        result["efficiency"] = (W_is / W_shaft).clip(0, 1)
    except KeyError:
        result["efficiency"] = float("nan")

    return result

def filter_operating_points(
    df: pd.DataFrame,
    flow_col: str,
    pressure_col: str,
    min_pressure: float,
    max_power: float = None,
    power_col: str = "shaft_power"
):
    """
    Filters operating points with linear interpolation at boundaries.
    Phase A: minimum pressure threshold
    Phase B: maximum shaft power threshold (optional)
    Phase C: surge line
    """
    if "speed_rpm" not in df.columns or df.empty:
        return df, pd.DataFrame()

    surge_points = []
    truncated_rows = []
    peak_info = {}
    
    # Pre-process: truncation and anchor points
    for speed in sorted(df["speed_rpm"].unique()):
        speed_df = df[df["speed_rpm"] == speed].sort_values(by=flow_col)
        if len(speed_df) == 0:
            continue
            
        # Ensure numeric for accurate max finding
        speed_df[pressure_col] = pd.to_numeric(speed_df[pressure_col], errors='coerce')
        
        # Find the point of maximum pressure
        max_p_idx = speed_df[pressure_col].idxmax()
        max_p_val = float(speed_df.loc[max_p_idx, pressure_col])
        max_p_flow = float(speed_df.loc[max_p_idx, flow_col])
        
        peak_info[speed] = {"flow": max_p_flow, "pressure": max_p_val}
        
        # Discard points to the left of the maximum pressure peak (where pressure dropped)
        speed_df_valid = speed_df[speed_df[flow_col] >= max_p_flow]
        truncated_rows.append(speed_df_valid)
        
        # Calculate the 1.1x flow anchor for maximum operating pressure
        anchor_flow = max_p_flow * 1.1
        surge_points.append({
            "speed_rpm": speed,
            flow_col: anchor_flow,
            pressure_col: max_p_val
        })
        
    df = pd.concat(truncated_rows, ignore_index=True)
    surge_df = pd.DataFrame(surge_points).sort_values(by="speed_rpm")

    m_surge, b_surge = None, None
    if len(surge_df) >= 2:
        valid_lines = []
        n_anchors = len(surge_df)
        # Try all pairs to find a line that conservatively bounds all anchors to the left.
        # i.e., Q_anchor <= m * P_anchor + b for all points.
        for i in range(n_anchors):
            for j in range(i + 1, n_anchors):
                pi, qi = surge_df.iloc[i][pressure_col], surge_df.iloc[i][flow_col]
                pj, qj = surge_df.iloc[j][pressure_col], surge_df.iloc[j][flow_col]
                if abs(pi - pj) > 1e-9:
                    m = (qi - qj) / (pi - pj)
                    b = qi - m * pi
                    
                    is_safe = True
                    for k in range(n_anchors):
                        pk = surge_df.iloc[k][pressure_col]
                        qk = surge_df.iloc[k][flow_col]
                        if qk > m * pk + b + 1e-6:
                            is_safe = False
                            break
                    if is_safe:
                        valid_lines.append((m, b))
        
        if valid_lines:
            # Pick the line with the smallest slope (steepest in P vs Q, most vertical bounding line)
            m_surge, b_surge = min(valid_lines, key=lambda x: abs(x[0]))
        else:
            # Fallback: simple linear regression shifted to the right to be conservative
            from scipy.stats import linregress
            slope, intercept, _, _, _ = linregress(surge_df[pressure_col], surge_df[flow_col])
            m_surge = slope
            b_surge = intercept
            max_shift = 0.0
            for k in range(n_anchors):
                pk = surge_df.iloc[k][pressure_col]
                qk = surge_df.iloc[k][flow_col]
                shift = qk - (m_surge * pk + b_surge)
                if shift > max_shift:
                    max_shift = shift
            b_surge += max_shift

    def _interp(p1: dict, p2: dict, ratio: float) -> dict:
        return {col: p1[col] + ratio * (p2[col] - p1[col])
                if isinstance(p1[col], (int, float)) else p1[col]
                for col in p1.keys()}

    new_rows = []
    for speed in df["speed_rpm"].unique():
        speed_df = df[df["speed_rpm"] == speed].sort_values(by=flow_col)
        points = speed_df.to_dict("records")
        if not points:
            continue

        # Phase A: Minimum Pressure
        refined = []
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            in1 = p1[pressure_col] >= min_pressure
            in2 = p2[pressure_col] >= min_pressure
            if in1:
                refined.append(p1)
            if in1 != in2:
                dp = p2[pressure_col] - p1[pressure_col]
                if abs(dp) > 1e-12:
                    ratio = (min_pressure - p1[pressure_col]) / dp
                    interp = _interp(p1, p2, ratio)
                    interp[pressure_col] = min_pressure
                    refined.append(interp)
        if points[-1][pressure_col] >= min_pressure:
            refined.append(points[-1])

        # Phase B: Maximum Power
        if max_power is not None and power_col in (points[0] if points else {}):
            power_refined = []
            for i in range(len(refined) - 1):
                p1, p2 = refined[i], refined[i + 1]
                in1 = p1[power_col] <= max_power
                in2 = p2[power_col] <= max_power
                if in1:
                    power_refined.append(p1)
                if in1 != in2:
                    dp = p2[power_col] - p1[power_col]
                    if abs(dp) > 1e-12:
                        ratio = (max_power - p1[power_col]) / dp
                        interp = _interp(p1, p2, ratio)
                        interp[power_col] = max_power
                        power_refined.append(interp)
            if refined and refined[-1][power_col] <= max_power:
                power_refined.append(refined[-1])
            refined = power_refined

        # Phase C: Surge Line
        if m_surge is not None and refined:
            surge_refined = []
            for i in range(len(refined) - 1):
                p1, p2 = refined[i], refined[i + 1]
                in1 = p1[flow_col] >= (m_surge * p1[pressure_col] + b_surge)
                in2 = p2[flow_col] >= (m_surge * p2[pressure_col] + b_surge)
                if in1:
                    surge_refined.append(p1)
                if in1 != in2:
                    dp = p2[pressure_col] - p1[pressure_col]
                    if abs(dp) > 1e-12:
                        k = (p2[flow_col] - p1[flow_col]) / dp
                        den = k - m_surge
                        if abs(den) > 1e-12:
                            pi = (b_surge - p1[flow_col] + k * p1[pressure_col]) / den
                            fi = m_surge * pi + b_surge
                            ratio_s = (pi - p1[pressure_col]) / dp
                            interp = _interp(p1, p2, ratio_s)
                            interp[pressure_col] = pi
                            interp[flow_col] = fi
                            surge_refined.append(interp)
            if refined and refined[-1][flow_col] >= (m_surge * refined[-1][pressure_col] + b_surge):
                surge_refined.append(refined[-1])
            refined = surge_refined

        new_rows.extend(refined)

    result_df = pd.DataFrame(new_rows)
    # 喘振线视觉：使用全部转速的锚点，保证线经过每条速度曲线的左侧边界
    # 按压力从低到高排列，使绘图折线从低速→高速方向连接
    if m_surge is not None and not surge_df.empty:
        surge_line_df = surge_df[[flow_col, pressure_col]].sort_values(by=pressure_col).reset_index(drop=True)
    else:
        surge_line_df = pd.DataFrame()

    return result_df, surge_line_df, peak_info
