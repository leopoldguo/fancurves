import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import UnivariateSpline, griddata, splprep, splev, interp1d

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_SMOOTH_POINTS = 300
_CONTOUR_PTS   = 600


# ─── Performance curve smoothing ─────────────────────────────────────────────

def _smooth_series(x, y, n_points=_SMOOTH_POINTS, smooth_level=3.0):
    if len(x) < 4:
        return x, y
    order = np.argsort(x)
    xs, ys = x[order], y[order]
    _, ui = np.unique(xs, return_index=True)
    xs, ys = xs[ui], ys[ui]
    if len(xs) < 4:
        return xs, ys
    auto_s = max(float(len(ys)) * float(np.var(ys)), 1e-10)
    if smooth_level <= 0.0:
        s = 0.0
    else:
        multiplier = 0.01 * smooth_level
        s = auto_s * multiplier
    try:
        sp = UnivariateSpline(xs, ys, s=s, k=3, ext=3)
        return np.linspace(xs[0], xs[-1], n_points), sp(np.linspace(xs[0], xs[-1], n_points))
    except Exception:
        return xs, ys


# ─── Iso-efficiency contour helpers ──────────────────────────────────────────

def _is_closed_path(px, py, threshold=0.02):
    path_len = float(np.sum(np.sqrt(np.diff(px)**2 + np.diff(py)**2)))
    ep_dist  = float(np.sqrt((px[0]-px[-1])**2 + (py[0]-py[-1])**2))
    return path_len > 1e-12 and ep_dist < threshold * path_len


def _smooth_path(px, py, n_pts=_CONTOUR_PTS, smooth_level=5.0):
    """
    2-D parametric cubic spline for contour paths.
    - Normalizes x and y to [0,1] to prevent massive aspect ratio differences
      (e.g., m3/h vs Pressure Ratio) from distorting the splprep arc-length calculation.
    """
    if len(px) < 4:
        return px, py
    dup = np.concatenate(([True], np.diff(px)**2 + np.diff(py)**2 > 1e-20))
    px, py = px[dup], py[dup]
    if len(px) < 4:
        return px, py

    closed = _is_closed_path(px, py)
    n = len(px)

    # Normalize to [0, 1] to ensure x and y variance are on the same scale
    px_min, px_max = px.min(), px.max()
    py_min, py_max = py.min(), py.max()
    px_range = max(px_max - px_min, 1e-12)
    py_range = max(py_max - py_min, 1e-12)

    px_norm = (px - px_min) / px_range
    py_norm = (py - py_min) / py_range

    # The contour data is already noise-free (just jagged due to grid resolution).
    # We want to bound the average deviation. User controls max average deviation
    # from 0% to 1% of the bounding box size.
    # e = target average error = 0.001 * smooth_level (At level 10, e = 0.01 = 1%)
    # s = sum of squared errors = n * e^2
    target_err_norm = 0.001 * float(smooth_level)
    s = float(n) * (target_err_norm ** 2)

    try:
        k = min(3, n - 1)
        tck, _ = splprep([px_norm, py_norm], s=s, k=k, per=closed)
        u_fine = np.linspace(0., 1., n_pts)
        xs_norm, ys_norm = splev(u_fine, tck)

        # Scale back to original dimensions
        xs = xs_norm * px_range + px_min
        ys = ys_norm * py_range + py_min

        return np.array(xs), np.array(ys)
    except Exception:
        return px, py


def _mask_below_min_speed(EI_pct, xi, yi, df, x_col, y_col):
    """Set grid cells below lowest-RPM curve to NaN."""
    if "speed_rpm" not in df.columns:
        return EI_pct
    min_speed = df["speed_rpm"].min()
    min_df = df[df["speed_rpm"] == min_speed].sort_values(x_col)
    xs_m = min_df[x_col].dropna().values
    ys_m = min_df[y_col].dropna().values
    if len(xs_m) < 2:
        return EI_pct
    try:
        fn = interp1d(xs_m, ys_m, bounds_error=False, fill_value=(np.nan, np.nan))
        result = EI_pct.copy()
        for j, xv in enumerate(xi):
            mp = float(fn(xv))
            if not np.isnan(mp):
                result[:, j] = np.where(yi < mp, np.nan, result[:, j])
        return result
    except Exception:
        return EI_pct


def _extract_contour_paths(xi, yi, grid_pct, levels_pct):
    import numpy.ma as ma
    gm = ma.masked_invalid(grid_pct)
    fig_m, ax_m = plt.subplots()
    cs = ax_m.contour(xi, yi, gm, levels=levels_pct)
    segs = []
    for lv, sg in zip(cs.levels, cs.allsegs):
        for s in sg:
            if len(s) >= 4:
                segs.append((float(lv), s[:, 0], s[:, 1]))
    plt.close(fig_m)
    return segs


def _level_color(level_pct, lo, hi):
    t = min(1.0, max(0.0, (level_pct - lo) / (hi - lo))) if hi > lo else 1.0
    r = int(80  + (180 - 80) * (1 - t))
    g = int(140 + (60 - 140) * (1 - t))
    b = int(80  * (1 - t))
    return f"rgb({min(255,r)},{min(255,g)},{min(255,b)})"


def _add_efficiency_contours(fig, df, x_col, y_col,
                              eff_col="efficiency",
                              contour_step_pct=2.0,
                              smooth_level=5.0,
                              grid_n=400):
    if eff_col not in df.columns or df[eff_col].isna().all():
        return fig

    xd = df[x_col].to_numpy(float)
    yd = df[y_col].to_numpy(float)
    ed = df[eff_col].to_numpy(float)

    valid = np.isfinite(ed) & (ed > 1e-6)
    if valid.sum() < 4:
        return fig
    xd, yd, ed = xd[valid], yd[valid], ed[valid]

    bep_i   = int(np.nanargmax(ed))
    bep_x   = float(xd[bep_i])
    bep_y   = float(yd[bep_i])
    bep_pct = float(ed[bep_i]) * 100.0

    # Normalize X and Y to [0, 1] before griddata triangulation. 
    # griddata uses Euclidean distance; large unit scales (like m3/h) distort the mesh.
    xd_min, xd_max = xd.min(), xd.max()
    yd_min, yd_max = yd.min(), yd.max()
    xd_range = max(xd_max - xd_min, 1e-12)
    yd_range = max(yd_max - yd_min, 1e-12)
    
    xd_norm = (xd - xd_min) / xd_range
    yd_norm = (yd - yd_min) / yd_range

    xi = np.linspace(xd_min, xd_max, grid_n)
    yi = np.linspace(yd_min, yd_max, grid_n)
    
    xi_norm = (xi - xd_min) / xd_range
    yi_norm = (yi - yd_min) / yd_range
    
    XI_NORM, YI_NORM = np.meshgrid(xi_norm, yi_norm)
    EI = griddata((xd_norm, yd_norm), ed * 100.0, (XI_NORM, YI_NORM), method="linear")
    
    # Masking uses the original scale xi, yi
    EI = _mask_below_min_speed(EI, xi, yi, df, x_col, y_col)

    step  = contour_step_pct
    floor = float(np.floor(bep_pct / step) * step)
    lo    = max(step, floor - 10 * step)
    levels = list(np.arange(lo, floor + 0.001, step))
    if not levels:
        return fig

    segments     = _extract_contour_paths(xi, yi, EI, levels)
    shown_levels = set()

    for lv_pct, px, py in segments:
        px_s, py_s = _smooth_path(np.array(px), np.array(py), smooth_level=smooth_level)
        color       = _level_color(lv_pct, levels[0], levels[-1])
        first       = lv_pct not in shown_levels
        shown_levels.add(lv_pct)
        mid = len(px_s) // 2
        fig.add_trace(
            go.Scatter(
                x=px_s, y=py_s,
                mode='lines+text' if (first and len(px_s) > 20) else 'lines',
                line=dict(color=color, width=1.8),
                text=([""] * mid + [f"{lv_pct:.0f}%"] + [""] * (len(px_s) - mid - 1)
                      if (first and len(px_s) > 20) else None),
                textposition="middle right",
                textfont=dict(size=10, color=color),
                customdata=np.full(len(px_s), lv_pct),
                hovertemplate="Eff: %{customdata:.0f}%<extra></extra>",
                name=f"η={lv_pct:.0f}%",
                legendgroup="iso_eff",
                legendgrouptitle_text="等效率线" if not shown_levels - {lv_pct} else None,
                showlegend=first,
            ),
            secondary_y=False,
        )

    fig.add_trace(
        go.Scatter(
            x=[bep_x], y=[bep_y],
            mode="markers+text",
            marker=dict(symbol="star", size=18, color="#32CD32",
                        line=dict(color="#32CD32", width=1.5)),
            text=[f"BEP {bep_pct:.1f}%"],
            textposition="top right",
            textfont=dict(size=11, color="#32CD32"),
            name=f"BEP ({bep_pct:.1f}%)",
        ),
        secondary_y=False,
    )
    return fig


# ─── Main chart function ──────────────────────────────────────────────────────

import plotly.colors as pc

def create_performance_curve(
    df: pd.DataFrame,
    surge_line_df: pd.DataFrame,
    x_col: str,
    y1_col: str,
    y2_col: str,
    x_label: str = "Flow Rate",
    y1_label: str = "Pressure Ratio",
    y2_label: str = "Shaft Power",
    perf_smooth: float = 3.0,
    eff_smooth: float = 5.0,
    show_power: bool = True,
    show_efficiency: bool = False,
    eff_contour_step: float = 2.0,
    chart_title: str = "",        # 文件名，作为图表副标题
) -> go.Figure:

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    dense_eff_list = []
    # Bright vivid palette for dark mode
    colors = ["#FF3B30", "#FF9500", "#FFCC00", "#4CD964", "#5AC8FA", "#007AFF", "#AF52DE", "#FF2D55"]

    if "speed_rpm" in df.columns:
        for i, speed in enumerate(sorted(df["speed_rpm"].unique(), reverse=True)):
            color = colors[i % len(colors)]
            
            sd = df[df["speed_rpm"] == speed].sort_values(by=x_col)
            xr  = sd[x_col].to_numpy(float)
            y1r = sd[y1_col].to_numpy(float)

            xs1, y1s = _smooth_series(xr, y1r, smooth_level=perf_smooth)
            
            if show_efficiency and "efficiency" in sd.columns:
                er = sd["efficiency"].to_numpy(float)
                try:
                    fn_eff = interp1d(xr, er, kind='linear', fill_value="extrapolate")
                    es1 = fn_eff(xs1)
                    df_pts = pd.DataFrame({
                        x_col: xs1,
                        y1_col: y1s,
                        "efficiency": es1,
                        "speed_rpm": speed
                    })
                    dense_eff_list.append(df_pts)
                except Exception:
                    pass

            fig.add_trace(
                go.Scatter(x=xs1, y=y1s, name=f'PR @ {int(speed)} RPM',
                           mode='lines', line=dict(color=color, width=2.5),
                           legendgroup=str(speed)),
                secondary_y=False)
            fig.add_trace(
                go.Scatter(x=xr, y=y1r, mode='markers',
                           marker=dict(color=color, size=5, opacity=0.4, symbol='circle'),
                           legendgroup=str(speed), showlegend=False, hoverinfo='skip'),
                secondary_y=False)

            if show_power and y2_col in sd.columns:
                y2r = sd[y2_col].to_numpy(float)
                xs2, y2s = _smooth_series(xr, y2r, smooth_level=perf_smooth)
                fig.add_trace(
                    go.Scatter(x=xs2, y=y2s, name=f'Power @ {int(speed)} RPM',
                               mode='lines', line=dict(color=color, dash='dash', width=2),
                               legendgroup=str(speed)),
                    secondary_y=True)
                fig.add_trace(
                    go.Scatter(x=xr, y=y2r, mode='markers',
                               marker=dict(color=color, size=5, opacity=0.4, symbol='diamond'),
                               legendgroup=str(speed), showlegend=False, hoverinfo='skip'),
                    secondary_y=True)

    if (not surge_line_df.empty
            and x_col in surge_line_df.columns
            and y1_col in surge_line_df.columns):
        fig.add_trace(
            go.Scatter(x=surge_line_df[x_col], y=surge_line_df[y1_col],
                       name='Surge Line', mode='lines+markers',
                       line=dict(color='#FF3B30', width=2.5, dash='dot'),
                       marker=dict(size=8, symbol='diamond-open', color='#FF3B30')),
            secondary_y=False)

    if show_efficiency and "efficiency" in df.columns:
        eff_df = df
        if dense_eff_list:
            eff_df = pd.concat(dense_eff_list, ignore_index=True)
            
        fig = _add_efficiency_contours(
            fig, eff_df, x_col=x_col, y_col=y1_col,
            eff_col="efficiency",
            contour_step_pct=eff_contour_step,
            smooth_level=eff_smooth,
        )

    # 去掉文件名的后缀（如 .csv）
    _display_title = chart_title.rsplit(".", 1)[0] if chart_title and "." in chart_title else chart_title

    # 标题和副标题对调：使用 Plotly 支持的 HTML 标签保证两者完美居中对齐
    if _display_title:
        main_title_text = f"<b>{_display_title}</b><br><span style='font-size:15px;color:#A0B4D0;'>性能曲线图</span>"
    else:
        main_title_text = "<b>性能曲线图</b>"
    
    # 移除之前的 annotation，完全用 title 接管
    annotations = []

    fig.update_layout(
        title=dict(text=main_title_text, x=0.5, y=0.96, xanchor="center", yanchor="top", font=dict(size=22, color="#F5F7FA")),
        plot_bgcolor="#131B2E", paper_bgcolor="#131B2E",
        hovermode="x unified",
        font=dict(family='"Microsoft YaHei", "WenQuanYi Micro Hei", "Noto Sans CJK SC", Arial, sans-serif', size=13, color="#E8EDF5"),
        legend=dict(orientation="v", bordercolor="rgba(126,170,238,0.3)",
                    borderwidth=1, bgcolor="rgba(19,27,46,0.90)"),
        margin=dict(l=80, r=80, t=100, b=60),
        annotations=annotations,
    )
    fig.update_xaxes(title_text=x_label,
                     showgrid=True, gridcolor='rgba(94,128,200,0.2)',
                     showline=True, linecolor='rgba(94,128,200,0.5)', linewidth=1.5,
                     ticks="outside", ticklen=6, tickcolor='rgba(94,128,200,0.5)', mirror=True)
    fig.update_yaxes(title_text=y1_label, secondary_y=False,
                     showgrid=True, gridcolor='rgba(94,128,200,0.2)',
                     showline=True, linecolor='rgba(94,128,200,0.5)', linewidth=1.5,
                     ticks="outside", ticklen=6, tickcolor='rgba(94,128,200,0.5)', mirror=True)
    fig.update_yaxes(title_text=y2_label if show_power else "",
                     secondary_y=True,
                     showgrid=False,
                     showline=show_power, linecolor='rgba(94,128,200,0.5)',
                     ticks="outside" if show_power else "",
                     ticklen=6, tickcolor='rgba(94,128,200,0.5)' if show_power else "rgba(0,0,0,0)",
                     showticklabels=show_power)
    return fig


def create_performance_curve_export(fig_dark: go.Figure) -> go.Figure:
    """从暗色交互图表生成白底、底部图例的导出版本（用于国标截图）。"""
    import copy
    fig = copy.deepcopy(fig_dark)
    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family='"Microsoft YaHei", "WenQuanYi Micro Hei", "Noto Sans CJK SC", Arial, sans-serif', color="#000000"),
        title_font_color="#000000",
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.18,
            xanchor="center", x=0.5,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#CCCCCC", borderwidth=1,
            font=dict(color="#000000")
        ),
        margin=dict(l=80, r=80, t=100, b=120),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#E0E0E0", linecolor="#666666",
                     tickcolor="#666666", title_font_color="#000000", tickfont_color="#000000")
    fig.update_yaxes(showgrid=True, gridcolor="#E0E0E0", linecolor="#666666",
                     tickcolor="#666666", title_font_color="#000000", tickfont_color="#000000")
    # 更新 annotations（副标题文字颜色）
    for ann in fig.layout.annotations:
        ann.font.color = "#333333"

    # 添加带 slogon 的 Logo (logo_compressor_light.png 适配白底)
    import os
    import base64
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_compressor_light.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64_logo = base64.b64encode(f.read()).decode()
        fig.add_layout_image(
            dict(
                source=f"data:image/png;base64,{b64_logo}",
                xref="paper", yref="paper",
                x=0.18, y=1.00,  # X 往右移以对齐标题，Y 微调垂直居中
                sizex=0.25, sizey=0.25,
                xanchor="right", yanchor="top",
                opacity=1.0,
                layer="above"
            )
        )

    return fig


def create_axial_force_curve(df: pd.DataFrame, x_col: str, force_col: str, flow_unit: str) -> go.Figure:
    """绘制轴向力曲线，支持 Y 轴自由动态缩放。"""
    fig = go.Figure()
    
    unique_speeds = sorted(df["speed_rpm"].unique(), reverse=True)
    palette = ["#FF3B30", "#FF9500", "#FFCC00", "#4CD964", "#5AC8FA", "#007AFF", "#AF52DE", "#FF2D55"]
    
    for i, speed in enumerate(unique_speeds):
        speed_df = df[df["speed_rpm"] == speed].sort_values(x_col)
        color = palette[i % len(palette)]
        
        fig.add_trace(go.Scatter(
            x=speed_df[x_col], y=speed_df[force_col],
            mode='lines+markers',
            name=f"{int(speed)} RPM",
            line=dict(color=color, width=2.5),
            marker=dict(size=6, symbol='circle')
        ))
        
    fig.add_hline(y=0, line_color="#555555", line_width=1)

    fig.update_layout(
        title_text="总轴向力特性分析图 (F_total = F_backplate - F_blade_hub)", title_font_size=16,
        plot_bgcolor="#131B2E", paper_bgcolor="#131B2E",
        hovermode="x unified",
        font=dict(family="IBM Plex Sans, sans-serif", size=13, color="#E8EDF5"),
        legend=dict(orientation="v", bordercolor="rgba(126,170,238,0.3)",
                    borderwidth=1, bgcolor="rgba(19,27,46,0.90)"),
        margin=dict(l=80, r=80, t=80, b=60),
    )
    fig.update_xaxes(title_text=f"流量 ({flow_unit})",
                     showgrid=True, gridcolor='rgba(94,128,200,0.2)',
                     showline=True, linecolor='rgba(94,128,200,0.5)', linewidth=1.5,
                     ticks="outside", ticklen=6, tickcolor='rgba(94,128,200,0.5)', mirror=True)
    fig.update_yaxes(title_text="总轴向力 (N) [指向入口为正]",
                     showgrid=True, gridcolor='rgba(94,128,200,0.2)',
                     showline=True, linecolor='rgba(94,128,200,0.5)', linewidth=1.5,
                     ticks="outside", ticklen=6, tickcolor='rgba(94,128,200,0.5)', mirror=True)
    return fig
