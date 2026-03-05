import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import UnivariateSpline
from typing import Optional

# Number of points used when rendering each smooth curve
_SMOOTH_POINTS = 300


def _smooth_series(
    x: np.ndarray,
    y: np.ndarray,
    n_points: int = _SMOOTH_POINTS,
    smooth_level: float = 3.0,
) -> tuple:
    """
    Fit a smooth spline through (x, y) using UnivariateSpline.

    smooth_level (0–10):
      0   → exact interpolation (s ≈ 0)
      3   → moderate (scipy auto default ≈ n·var(y))
      10  → very smooth (5× auto)

    The scipy `s` parameter is the maximum allowed sum of squared residuals.
    We scale it as:   s = auto_s × multiplier
    where auto_s = n·var(y)  (scipy's own heuristic, internally ~len(y)).
    """
    if len(x) < 4:
        return x, y

    order = np.argsort(x)
    xs, ys = x[order], y[order]

    _, unique_idx = np.unique(xs, return_index=True)
    xs, ys = xs[unique_idx], ys[unique_idx]

    if len(xs) < 4:
        return xs, ys

    # Compute variance-normalised smoothing factor
    auto_s = max(float(len(ys)) * float(np.var(ys)), 1e-10)

    if smooth_level <= 0.0:
        s = 0.0                                  # exact (interpolating)
    else:
        # Map [0.1, 10] → [0.05×auto, 5×auto]  with exponential feel
        multiplier = 0.05 * (10 ** (smooth_level / 10 * np.log10(100)))
        s = auto_s * multiplier

    try:
        spline = UnivariateSpline(xs, ys, s=s, k=3, ext=3)
        x_fine = np.linspace(xs[0], xs[-1], n_points)
        y_fine = spline(x_fine)
        return x_fine, y_fine
    except Exception:
        return xs, ys


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
) -> go.Figure:
    """
    Render a professional fan performance chart with smooth fitted curves.
    Each RPM speed generates: a smooth fitted pressure curve + a smooth fitted
    power curve (dashed), each backed by faint raw-data markers.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "speed_rpm" in df.columns:
        speeds = sorted(df["speed_rpm"].unique())
        for speed in speeds:
            speed_df = df[df["speed_rpm"] == speed].sort_values(by=x_col)
            x_raw = speed_df[x_col].to_numpy(dtype=float)
            y1_raw = speed_df[y1_col].to_numpy(dtype=float)
            y2_raw = speed_df[y2_col].to_numpy(dtype=float)

            x_s1, y1_s = _smooth_series(x_raw, y1_raw, smooth_level=smooth_level)
            x_s2, y2_s = _smooth_series(x_raw, y2_raw, smooth_level=smooth_level)

            # Pressure smooth curve
            fig.add_trace(
                go.Scatter(
                    x=x_s1, y=y1_s,
                    name=f'PR @ {int(speed)} RPM',
                    mode='lines',
                    line=dict(width=2.5),
                    legendgroup=str(speed),
                ),
                secondary_y=False,
            )
            # Raw CFD markers (faint, for reference)
            fig.add_trace(
                go.Scatter(
                    x=x_raw, y=y1_raw,
                    mode='markers',
                    marker=dict(size=5, opacity=0.4, symbol='circle'),
                    legendgroup=str(speed),
                    showlegend=False,
                    hoverinfo='skip',
                ),
                secondary_y=False,
            )

            # Power smooth curve (dashed)
            fig.add_trace(
                go.Scatter(
                    x=x_s2, y=y2_s,
                    name=f'Power @ {int(speed)} RPM',
                    mode='lines',
                    line=dict(dash='dash', width=2),
                    legendgroup=str(speed),
                ),
                secondary_y=True,
            )
            # Raw power markers (faint)
            fig.add_trace(
                go.Scatter(
                    x=x_raw, y=y2_raw,
                    mode='markers',
                    marker=dict(size=5, opacity=0.4, symbol='diamond'),
                    legendgroup=str(speed),
                    showlegend=False,
                    hoverinfo='skip',
                ),
                secondary_y=True,
            )

    # Surge line — straight line, no smoothing needed
    if (not surge_line_df.empty
            and x_col in surge_line_df.columns
            and y1_col in surge_line_df.columns):
        fig.add_trace(
            go.Scatter(
                x=surge_line_df[x_col],
                y=surge_line_df[y1_col],
                name='Surge Line',
                mode='lines+markers',
                line=dict(color='black', width=2.5, dash='dot'),
                marker=dict(size=8, symbol='diamond-open'),
            ),
            secondary_y=False,
        )

    # Engineering / publication quality layout
    fig.update_layout(
        title_text="Fan Performance Map",
        title_font_size=18,
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        font=dict(family="Arial, sans-serif", size=13),
        legend=dict(
            orientation="v",
            bordercolor="lightgray",
            borderwidth=1,
            bgcolor="rgba(255,255,255,0.85)",
        ),
        margin=dict(l=80, r=80, t=80, b=60),
    )

    fig.update_xaxes(
        title_text=x_label,
        showgrid=True, gridcolor='rgba(200,200,200,0.5)', gridwidth=1,
        showline=True, linecolor='black', linewidth=1.5,
        ticks="outside", ticklen=6, mirror=True,
    )
    fig.update_yaxes(
        title_text=y1_label, secondary_y=False,
        showgrid=True, gridcolor='rgba(200,200,200,0.5)', gridwidth=1,
        showline=True, linecolor='black', linewidth=1.5,
        ticks="outside", ticklen=6, mirror=False,
    )
    fig.update_yaxes(
        title_text=y2_label, secondary_y=True,
        showgrid=False,
        showline=True, linecolor='gray', linewidth=1,
        ticks="outside", ticklen=6,
    )

    return fig
