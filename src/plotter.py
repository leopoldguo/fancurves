import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import UnivariateSpline, griddata, splprep, splev, interp1d

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_SMOOTH_POINTS = 300


# ─── Performance curve smoothing ─────────────────────────────────────────────

def _smooth_series(
    x: np.ndarray,
    y: np.ndarray,
    n_points: int = _SMOOTH_POINTS,
    smooth_level: float = 3.0,
) -> tuple:
    if len(x) < 4:
        return x, y
    order = np.argsort(x)
    xs, ys = x[order], y[order]
    _, unique_idx = np.unique(xs, return_index=True)
    xs, ys = xs[unique_idx], ys[unique_idx]
    if len(xs) < 4:
        return xs, ys
    auto_s = max(float(len(ys)) * float(np.var(ys)), 1e-10)
    if smooth_level <= 0.0:
        s = 0.0
    else:
        multiplier = 0.05 * (10 ** (smooth_level / 10 * np.log10(100)))
        s = auto_s * multiplier
    try:
        spline = UnivariateSpline(xs, ys, s=s, k=3, ext=3)
        x_fine = np.linspace(xs[0], xs[-1], n_points)
        return x_fine, spline(x_fine)
    except Exception:
        return xs, ys


# ─── Iso-efficiency contour helpers ──────────────────────────────────────────

def _is_closed_path(px: np.ndarray, py: np.ndarray, threshold: float = 0.02) -> bool:
    """Check if a contour segment is closed (first ≈ last point)."""
    path_len = float(np.sum(np.sqrt(np.diff(px)**2 + np.diff(py)**2)))
    endpoint_dist = float(np.sqrt((px[0] - px[-1])**2 + (py[0] - py[-1])**2))
    if path_len < 1e-12:
        return False
    return endpoint_dist < threshold * path_len


def _smooth_path(px: np.ndarray, py: np.ndarray, n_pts: int = 500) -> tuple:
    """
    Densify a 2D contour path using splprep(s=0):
    - Closed paths (first≈last): per=True → smooth, perfectly closed ring
    - Open paths: per=False → ends are preserved exactly, no artificial closure

    s=0 means exact interpolation through all vertices — the cubic spline only
    adds curvature BETWEEN vertices, never deviating from the original path.
    """
    if len(px) < 4:
        return px, py
    # Remove consecutive duplicates
    mask = np.concatenate(([True], np.diff(px)**2 + np.diff(py)**2 > 1e-20))
    px, py = px[mask], py[mask]
    if len(px) < 4:
        return px, py

    closed = _is_closed_path(px, py)
    try:
        k = min(3, len(px) - 1)
        tck, _ = splprep([px, py], s=0, k=k, per=closed)
        u_fine = np.linspace(0., 1., n_pts)
        x_s, y_s = splev(u_fine, tck)
        return x_s, y_s
    except Exception:
        return px, py


def _mask_below_min_speed(EI_pct: np.ndarray,
                           xi: np.ndarray, yi: np.ndarray,
                           df: pd.DataFrame,
                           x_col: str, y_col: str) -> np.ndarray:
    """
    Set efficiency-grid cells to NaN in the region below the lowest-RPM
    performance curve. This prevents contours from being drawn in regions
    that are physically outside the operating envelope.
    """
    if "speed_rpm" not in df.columns:
        return EI_pct
    min_speed = df["speed_rpm"].min()
    min_df = df[df["speed_rpm"] == min_speed].sort_values(x_col)
    xs_min = min_df[x_col].dropna().values
    ys_min = min_df[y_col].dropna().values
    if len(xs_min) < 2:
        return EI_pct
    try:
        min_p_func = interp1d(xs_min, ys_min, bounds_error=False,
                              fill_value=(np.nan, np.nan))
        result = EI_pct.copy()
        for j, xi_val in enumerate(xi):
            min_p = float(min_p_func(xi_val))
            if np.isnan(min_p):
                continue
            for i, yi_val in enumerate(yi):
                if yi_val < min_p:
                    result[i, j] = np.nan
        return result
    except Exception:
        return EI_pct


def _extract_contour_paths(xi, yi, grid_pct, levels_pct):
    """
    Use matplotlib (Agg backend, non-displayed) to extract contour path
    segments. Returns list of (level_value_pct, x_array, y_array).
    Segments that are natural closed loops (around BEP) are returned as
    such by matplotlib's contouring algorithm.
    """
    import numpy.ma as ma
    grid_masked = ma.masked_invalid(grid_pct)
    fig_mpl, ax_mpl = plt.subplots()
    cs = ax_mpl.contour(xi, yi, grid_masked, levels=levels_pct)
    segments = []
    for level_val, segs in zip(cs.levels, cs.allsegs):
        for seg in segs:
            if len(seg) >= 4:
                segments.append((float(level_val), seg[:, 0], seg[:, 1]))
    plt.close(fig_mpl)
    return segments


def _level_color(level_pct: float, lo: float, hi: float) -> str:
    t = min(1.0, max(0.0, (level_pct - lo) / (hi - lo))) if hi > lo else 1.0
    r = int(80  + (180 - 80)  * (1 - t))
    g = int(140 + (60  - 140) * (1 - t))
    b = int(80  * (1 - t))
    return f"rgb({min(255,r)},{min(255,g)},{min(255,b)})"


def _add_efficiency_contours(
    fig: go.Figure,
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    eff_col: str = "efficiency",
    contour_step_pct: float = 2.0,
    grid_n: int = 300,
) -> go.Figure:
    """
    Overlay iso-efficiency contours with three key behaviours:

    1. Innermost ring (around BEP): matplotlib returns it as a closed loop.
       splprep(per=True) makes it a perfectly smooth, circular/elliptical ring.

    2. Outer rings that reach the data boundary: matplotlib returns them as
       open segments. splprep(per=False) keeps endpoints honest, no fake closure.

    3. Region below lowest-RPM performance curve: masked to NaN before
       computing contours, so no contour lines are drawn there.
    """
    if eff_col not in df.columns or df[eff_col].isna().all():
        return fig

    x_data   = df[x_col].to_numpy(dtype=float)
    y_data   = df[y_col].to_numpy(dtype=float)
    eff_data = df[eff_col].to_numpy(dtype=float)

    valid = np.isfinite(eff_data) & (eff_data > 1e-6)
    if valid.sum() < 4:
        return fig
    x_data, y_data, eff_data = x_data[valid], y_data[valid], eff_data[valid]

    # BEP from raw data
    bep_idx     = int(np.nanargmax(eff_data))
    bep_x       = float(x_data[bep_idx])
    bep_y       = float(y_data[bep_idx])
    bep_eta_pct = float(eff_data[bep_idx]) * 100.0

    # 2-D efficiency grid (%)
    xi = np.linspace(x_data.min(), x_data.max(), grid_n)
    yi = np.linspace(y_data.min(), y_data.max(), grid_n)
    XI, YI = np.meshgrid(xi, yi)
    EI_pct = griddata((x_data, y_data), eff_data * 100.0, (XI, YI),
                       method="linear")   # NaN outside convex hull

    # Mask region below lowest-RPM curve so no contours appear there
    EI_pct = _mask_below_min_speed(EI_pct, xi, yi, df, x_col, y_col)

    # Contour levels (%)
    step      = contour_step_pct
    bep_floor = float(np.floor(bep_eta_pct / step) * step)
    lo_level  = max(step, bep_floor - 10 * step)
    levels    = list(np.arange(lo_level, bep_floor + 0.001, step))
    if not levels:
        return fig

    segments = _extract_contour_paths(xi, yi, EI_pct, levels)

    lo_pct, hi_pct = levels[0], levels[-1]
    shown_levels   = set()

    for level_pct, px, py in segments:
        px_arr  = np.array(px)
        py_arr  = np.array(py)
        closed  = _is_closed_path(px_arr, py_arr)
        px_s, py_s = _smooth_path(px_arr, py_arr)

        color          = _level_color(level_pct, lo_pct, hi_pct)
        show_in_legend = level_pct not in shown_levels
        shown_levels.add(level_pct)

        mid = len(px_s) // 2
        customdata = np.full(len(px_s), level_pct)

        fig.add_trace(
            go.Scatter(
                x=px_s, y=py_s,
                mode='lines+text' if (show_in_legend and len(px_s) > 20) else 'lines',
                line=dict(color=color, width=1.8),
                text=([""] * mid + [f"{level_pct:.0f}%"] + [""] * (len(px_s) - mid - 1)
                      if (show_in_legend and len(px_s) > 20) else None),
                textposition="middle right",
                textfont=dict(size=10, color=color),
                customdata=customdata,
                hovertemplate="Eff: %{customdata:.0f}%<extra></extra>",
                # Closed rings get a filled marker at the end to look tidy
                name=f"η={level_pct:.0f}%{'  ⊙' if closed else ''}",
                legendgroup="iso_eff",
                legendgrouptitle_text="等效率线" if not shown_levels - {level_pct} else None,
                showlegend=show_in_legend,
            ),
            secondary_y=False,
        )

    # BEP gold star
    fig.add_trace(
        go.Scatter(
            x=[bep_x], y=[bep_y],
            mode="markers+text",
            marker=dict(symbol="star", size=18, color="gold",
                        line=dict(color="darkorange", width=1.5)),
            text=[f"BEP {bep_eta_pct:.1f}%"],
            textposition="top right",
            textfont=dict(size=11, color="darkorange"),
            name=f"BEP ({bep_eta_pct:.1f}%)",
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
    smooth_level: float = 3.0,
    show_efficiency: bool = False,
    eff_contour_step: float = 2.0,
) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "speed_rpm" in df.columns:
        speeds = sorted(df["speed_rpm"].unique())
        for speed in speeds:
            speed_df = df[df["speed_rpm"] == speed].sort_values(by=x_col)
            x_raw  = speed_df[x_col].to_numpy(dtype=float)
            y1_raw = speed_df[y1_col].to_numpy(dtype=float)
            y2_raw = speed_df[y2_col].to_numpy(dtype=float)

            x_s1, y1_s = _smooth_series(x_raw, y1_raw, smooth_level=smooth_level)
            x_s2, y2_s = _smooth_series(x_raw, y2_raw, smooth_level=smooth_level)

            fig.add_trace(
                go.Scatter(x=x_s1, y=y1_s, name=f'PR @ {int(speed)} RPM',
                           mode='lines', line=dict(width=2.5),
                           legendgroup=str(speed)),
                secondary_y=False)
            fig.add_trace(
                go.Scatter(x=x_raw, y=y1_raw, mode='markers',
                           marker=dict(size=5, opacity=0.4, symbol='circle'),
                           legendgroup=str(speed), showlegend=False, hoverinfo='skip'),
                secondary_y=False)
            fig.add_trace(
                go.Scatter(x=x_s2, y=y2_s, name=f'Power @ {int(speed)} RPM',
                           mode='lines', line=dict(dash='dash', width=2),
                           legendgroup=str(speed)),
                secondary_y=True)
            fig.add_trace(
                go.Scatter(x=x_raw, y=y2_raw, mode='markers',
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
        )

    fig.update_layout(
        title_text="Fan Performance Map",
        title_font_size=18,
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
    fig.update_yaxes(title_text=y2_label, secondary_y=True,
                     showgrid=False, showline=True, linecolor='gray',
                     ticks="outside", ticklen=6)
    return fig
