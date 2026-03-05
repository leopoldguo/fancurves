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
    - Closed rings: per=True (seamless BEP ellipse).
    - Open paths:  per=False (ends preserved exactly).
    - Smoothing s uses same auto-scale formula as _smooth_series.
    """
    if len(px) < 4:
        return px, py
    dup = np.concatenate(([True], np.diff(px)**2 + np.diff(py)**2 > 1e-20))
    px, py = px[dup], py[dup]
    if len(px) < 4:
        return px, py

    closed = _is_closed_path(px, py)
    n = len(px)
    auto_s = (max(float(n)*float(np.var(px)), 1e-12) +
              max(float(n)*float(np.var(py)), 1e-12)) / 2.0

    if smooth_level <= 0.0:
        s = 0.0
    else:
        multiplier = 0.01 * smooth_level
        s = auto_s * multiplier

    try:
        k = min(3, n - 1)
        tck, _ = splprep([px, py], s=s, k=k, per=closed)
        u_fine = np.linspace(0., 1., n_pts)
        xs, ys = splev(u_fine, tck)
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

    xi = np.linspace(xd.min(), xd.max(), grid_n)
    yi = np.linspace(yd.min(), yd.max(), grid_n)
    XI, YI = np.meshgrid(xi, yi)
    EI = griddata((xd, yd), ed * 100.0, (XI, YI), method="linear")
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
            marker=dict(symbol="star", size=18, color="gold",
                        line=dict(color="darkorange", width=1.5)),
            text=[f"BEP {bep_pct:.1f}%"],
            textposition="top right",
            textfont=dict(size=11, color="darkorange"),
            name=f"BEP ({bep_pct:.1f}%)",
        ),
        secondary_y=False,
    )
    return fig


# ─── Main chart function ──────────────────────────────────────────────────────

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
) -> go.Figure:

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "speed_rpm" in df.columns:
        for speed in sorted(df["speed_rpm"].unique()):
            sd = df[df["speed_rpm"] == speed].sort_values(by=x_col)
            xr  = sd[x_col].to_numpy(float)
            y1r = sd[y1_col].to_numpy(float)

            xs1, y1s = _smooth_series(xr, y1r, smooth_level=perf_smooth)
            fig.add_trace(
                go.Scatter(x=xs1, y=y1s, name=f'PR @ {int(speed)} RPM',
                           mode='lines', line=dict(width=2.5),
                           legendgroup=str(speed)),
                secondary_y=False)
            fig.add_trace(
                go.Scatter(x=xr, y=y1r, mode='markers',
                           marker=dict(size=5, opacity=0.4, symbol='circle'),
                           legendgroup=str(speed), showlegend=False, hoverinfo='skip'),
                secondary_y=False)

            if show_power and y2_col in sd.columns:
                y2r = sd[y2_col].to_numpy(float)
                xs2, y2s = _smooth_series(xr, y2r, smooth_level=perf_smooth)
                fig.add_trace(
                    go.Scatter(x=xs2, y=y2s, name=f'Power @ {int(speed)} RPM',
                               mode='lines', line=dict(dash='dash', width=2),
                               legendgroup=str(speed)),
                    secondary_y=True)
                fig.add_trace(
                    go.Scatter(x=xr, y=y2r, mode='markers',
                               marker=dict(size=5, opacity=0.4, symbol='diamond'),
                               legendgroup=str(speed), showlegend=False, hoverinfo='skip'),
                    secondary_y=True)

    if (not surge_line_df.empty
            and x_col in surge_line_df.columns
            and y1_col in surge_line_df.columns):
        fig.add_trace(
            go.Scatter(x=surge_line_df[x_col], y=surge_line_df[y1_col],
                       name='Surge Line', mode='lines+markers',
                       line=dict(color='black', width=2.5, dash='dot'),
                       marker=dict(size=8, symbol='diamond-open')),
            secondary_y=False)

    if show_efficiency and "efficiency" in df.columns:
        fig = _add_efficiency_contours(
            fig, df, x_col=x_col, y_col=y1_col,
            eff_col="efficiency",
            contour_step_pct=eff_contour_step,
            smooth_level=eff_smooth,
        )

    fig.update_layout(
        title_text="Fan Performance Map", title_font_size=18,
        plot_bgcolor="white", paper_bgcolor="white",
        hovermode="x unified",
        font=dict(family="Arial, sans-serif", size=13),
        legend=dict(orientation="v", bordercolor="lightgray",
                    borderwidth=1, bgcolor="rgba(255,255,255,0.85)"),
        margin=dict(l=80, r=80, t=80, b=60),
    )
    fig.update_xaxes(title_text=x_label,
                     showgrid=True, gridcolor='rgba(200,200,200,0.5)',
                     showline=True, linecolor='black', linewidth=1.5,
                     ticks="outside", ticklen=6, mirror=True)
    fig.update_yaxes(title_text=y1_label, secondary_y=False,
                     showgrid=True, gridcolor='rgba(200,200,200,0.5)',
                     showline=True, linecolor='black', linewidth=1.5,
                     ticks="outside", ticklen=6, mirror=False)
    fig.update_yaxes(title_text=y2_label if show_power else "",
                     secondary_y=True,
                     showgrid=False,
                     showline=show_power, linecolor='gray',
                     ticks="outside" if show_power else "",
                     ticklen=6,
                     showticklabels=show_power)
    return fig
