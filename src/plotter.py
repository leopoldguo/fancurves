import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import UnivariateSpline, griddata
from typing import Optional, List

_SMOOTH_POINTS = 300


def _smooth_series(
    x: np.ndarray,
    y: np.ndarray,
    n_points: int = _SMOOTH_POINTS,
    smooth_level: float = 3.0,
) -> tuple:
    """
    Fit a smooth spline. smooth_level 0–10:
      0 → exact interpolation, 10 → very smooth (5× auto variance-scaled s).
    """
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
        y_fine = spline(x_fine)
        return x_fine, y_fine
    except Exception:
        return xs, ys


def _add_efficiency_contours(
    fig: go.Figure,
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    eff_col: str = "efficiency",
    contour_step: float = 0.02,
    grid_n: int = 200,
) -> go.Figure:
    """
    Overlay iso-efficiency contour curves on the primary (left Y-axis) panel.

    Uses scipy.interpolate.griddata (linear) to create a fine 2D efficiency
    field from the scattered (flow, pressure, efficiency) data, then draws
    Plotly contour lines at intervals of `contour_step` (e.g. 0.02 = 2%).
    Also plots the Best Efficiency Point (BEP) as a gold star marker.
    """
    if eff_col not in df.columns or df[eff_col].isna().all():
        return fig

    x_data = df[x_col].to_numpy(dtype=float)
    y_data = df[y_col].to_numpy(dtype=float)
    eff_data = df[eff_col].to_numpy(dtype=float)

    # Remove NaN / zero-efficiency rows (e.g. interpolated boundary points)
    valid = np.isfinite(eff_data) & (eff_data > 0)
    if valid.sum() < 4:
        return fig
    x_data, y_data, eff_data = x_data[valid], y_data[valid], eff_data[valid]

    # 2-D grid for contour interpolation
    xi = np.linspace(x_data.min(), x_data.max(), grid_n)
    yi = np.linspace(y_data.min(), y_data.max(), grid_n)
    XI, YI = np.meshgrid(xi, yi)
    EI = griddata((x_data, y_data), eff_data, (XI, YI), method="linear")

    bep_idx   = np.nanargmax(eff_data)
    bep_x     = float(x_data[bep_idx])
    bep_y     = float(y_data[bep_idx])
    bep_eta   = float(eff_data[bep_idx])

    # Contour levels: from (bep - several steps) down to slightly above 0
    eta_start  = max(contour_step, round(bep_eta - 10 * contour_step, 4))
    eta_end    = bep_eta
    contour_levels = list(np.arange(eta_start, eta_end + 1e-9, contour_step))

    # Plotly Contour (on secondary=False, so it shares the left Y axis)
    fig.add_trace(
        go.Contour(
            x=xi, y=yi, z=EI,
            contours=dict(
                start=min(contour_levels),
                end=bep_eta,
                size=contour_step,
                coloring="lines",
                showlabels=True,
                labelfont=dict(size=10, color="darkgreen"),
            ),
            colorscale=[[0, "lightgreen"], [1, "darkgreen"]],
            showscale=False,
            line=dict(width=1.5),
            name="Iso-efficiency",
            opacity=0.8,
        ),
        secondary_y=False,
    )

    # BEP star marker
    fig.add_trace(
        go.Scatter(
            x=[bep_x], y=[bep_y],
            mode="markers+text",
            marker=dict(symbol="star", size=18, color="gold",
                        line=dict(color="darkorange", width=1.5)),
            text=[f"BEP {bep_eta*100:.1f}%"],
            textposition="top right",
            textfont=dict(size=11, color="darkorange"),
            name=f"BEP ({bep_eta*100:.1f}%)",
        ),
        secondary_y=False,
    )

    return fig


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
    eff_contour_step: float = 0.02,
) -> go.Figure:
    """
    Render a professional fan performance map with smooth fitted curves.
    Optionally overlay iso-efficiency contours and BEP marker.
    """
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
                go.Scatter(x=x_s1, y=y1_s,
                           name=f'PR @ {int(speed)} RPM',
                           mode='lines', line=dict(width=2.5),
                           legendgroup=str(speed)),
                secondary_y=False,
            )
            fig.add_trace(
                go.Scatter(x=x_raw, y=y1_raw, mode='markers',
                           marker=dict(size=5, opacity=0.4, symbol='circle'),
                           legendgroup=str(speed), showlegend=False, hoverinfo='skip'),
                secondary_y=False,
            )
            fig.add_trace(
                go.Scatter(x=x_s2, y=y2_s,
                           name=f'Power @ {int(speed)} RPM',
                           mode='lines', line=dict(dash='dash', width=2),
                           legendgroup=str(speed)),
                secondary_y=True,
            )
            fig.add_trace(
                go.Scatter(x=x_raw, y=y2_raw, mode='markers',
                           marker=dict(size=5, opacity=0.4, symbol='diamond'),
                           legendgroup=str(speed), showlegend=False, hoverinfo='skip'),
                secondary_y=True,
            )

    # Surge line
    if (not surge_line_df.empty
            and x_col in surge_line_df.columns
            and y1_col in surge_line_df.columns):
        fig.add_trace(
            go.Scatter(x=surge_line_df[x_col], y=surge_line_df[y1_col],
                       name='Surge Line', mode='lines+markers',
                       line=dict(color='black', width=2.5, dash='dot'),
                       marker=dict(size=8, symbol='diamond-open')),
            secondary_y=False,
        )

    # Iso-efficiency contours (optional)
    if show_efficiency and "efficiency" in df.columns:
        fig = _add_efficiency_contours(
            fig, df, x_col=x_col, y_col=y1_col,
            eff_col="efficiency", contour_step=eff_contour_step,
        )

    # Layout
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
                     showgrid=True, gridcolor='rgba(200,200,200,0.5)', gridwidth=1,
                     showline=True, linecolor='black', linewidth=1.5,
                     ticks="outside", ticklen=6, mirror=True)
    fig.update_yaxes(title_text=y1_label, secondary_y=False,
                     showgrid=True, gridcolor='rgba(200,200,200,0.5)', gridwidth=1,
                     showline=True, linecolor='black', linewidth=1.5,
                     ticks="outside", ticklen=6, mirror=False)
    fig.update_yaxes(title_text=y2_label, secondary_y=True,
                     showgrid=False,
                     showline=True, linecolor='gray', linewidth=1,
                     ticks="outside", ticklen=6)

    return fig
