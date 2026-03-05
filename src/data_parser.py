import pandas as pd

HEADER_MAP = {
    "进口流量": "mass_flow",
    "压比": "pressure_ratio",
    "轴功率": "shaft_power",
    "设定转速": "speed_rpm"
}

P_ATM_KPA = 101.325  # 标准大气压，单位 kPa

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
    return df_clean.rename(columns=rename_dict)

def convert_flow_units(value: float, from_unit: str, to_unit: str, density: float = 1.204) -> float:
    """在 kg/s, m3/min, m3/h, CFM 之间转换流量单位。
    密度默认使用 20°C、1标准大气压的空气密度 1.204 kg/m³。
    """
    if from_unit == to_unit:
        return value
    # 先将所有单位转换为 m3/min 作为中间基准
    m3_min = value
    if from_unit == "kg/s":
        m3_min = (value / density) * 60.0
    elif from_unit == "CFM":
        m3_min = value / 35.3146667
    elif from_unit == "m3/h":
        m3_min = value / 60.0
    # m3/min: no conversion needed, m3_min = value already

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
        return pressure_ratio_series  # pressure_ratio, no change

def filter_operating_points(
    df: pd.DataFrame,
    flow_col: str,
    pressure_col: str,
    min_pressure: float,
    max_power: float = None,
    power_col: str = "shaft_power"
):
    """
    Filters operating points with linear interpolation at boundaries:
    - Drops/interpolates at the minimum pressure threshold.
    - Drops/interpolates at the linear surge line boundary.
    - Optionally drops/interpolates at the maximum shaft power threshold.
    """
    if "speed_rpm" not in df.columns or df.empty:
        return df, pd.DataFrame()

    # 1. Compute surge points (min flow per speed) for the surge line
    surge_points = []
    for speed in sorted(df["speed_rpm"].unique()):
        speed_df = df[df["speed_rpm"] == speed]
        surge_points.append(speed_df.loc[speed_df[flow_col].idxmin()])
    surge_df = pd.DataFrame(surge_points).sort_values(by="speed_rpm")

    # Linear surge line: flow = m_surge * pressure + b_surge
    m_surge, b_surge = None, None
    if len(surge_df) >= 2:
        p_lo, f_lo = surge_df.iloc[0][pressure_col], surge_df.iloc[0][flow_col]
        p_hi, f_hi = surge_df.iloc[-1][pressure_col], surge_df.iloc[-1][flow_col]
        if p_hi != p_lo:
            m_surge = (f_hi - f_lo) / (p_hi - p_lo)
            b_surge = f_lo - m_surge * p_lo

    def _interp(p1: dict, p2: dict, ratio: float) -> dict:
        """Linear interpolation of all numeric fields between two points."""
        return {col: p1[col] + ratio * (p2[col] - p1[col])
                if isinstance(p1[col], (int, float)) else p1[col]
                for col in p1.keys()}

    new_rows = []
    for speed in df["speed_rpm"].unique():
        speed_df = df[df["speed_rpm"] == speed].sort_values(by=flow_col)
        points = speed_df.to_dict("records")
        if not points:
            continue

        # ---- Phase A: Minimum Pressure Interpolation ----
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

        # ---- Phase B: Maximum Power Interpolation ----
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

        # ---- Phase C: Surge Line Interpolation ----
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

    surge_line_df = pd.DataFrame({
        flow_col: [surge_df.iloc[0][flow_col], surge_df.iloc[-1][flow_col]],
        pressure_col: [surge_df.iloc[0][pressure_col], surge_df.iloc[-1][pressure_col]]
    }) if m_surge is not None else pd.DataFrame()

    return result_df, surge_line_df
