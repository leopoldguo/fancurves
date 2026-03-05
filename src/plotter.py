import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import UnivariateSpline

# Number of points to use when rendering each smooth curve
_SMOOTH_POINTS = 300

def _smooth_series(x: np.ndarray, y: np.ndarray, n_points: int = _SMOOTH_POINTS, smoothing_factor: float = None) -> tuple[np.ndarray, np.ndarray]:
    """
    Fit a smooth spline through (x, y) data using least-squares UnivariateSpline.
    The smoothing_factor `s` controls how tightly to follow the raw data;
    s=None lets scipy choose automatically, larger values give smoother curves.
    Returns (x_smooth, y_smooth) with n_points resolution.
    """
    if len(x) < 4:
        # Not enough points for a cubic spline – fall back to linear
        return x, y

    # Sort by x (required by UnivariateSpline)
    order = np.argsort(x)
    xs, ys = x[order], y[order]

    # Remove duplicate x values (can arise from interpolated boundary points)
    _, unique_idx = np.unique(xs, return_index=True)
    xs, ys = xs[unique_idx], ys[unique_idx]

    if len(xs) < 4:
        return xs, ys

    # Determine smoothing factor: default scales with data variance to allow
    # visible deviation from individual CFD points for a "clean" fan-curve look.
    if smoothing_factor is None:
        # s proportional to n * variance of y – produces well-behaved fit
        smoothing_factor = len(ys) * np.var(ys) * 0.5

    try:
        spline = UnivariateSpline(xs, ys, s=smoothing_factor, k=3, ext=3)
        x_fine = np.linspace(xs[0], xs[-1], n_points)
        y_fine = spline(x_fine)
        return x_fine, y_fine
    except Exception:
        # Fall back to raw data if spline fails
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
    smoothing_factor: float = None,
) -> go.Figure:
    """
    Render a professional fan performance chart with smooth fitted curves.
    Each RPM speed generates two smooth traces (pressure + power).
    Raw data points are shown as small markers behind the fitted line.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "speed_rpm" in df.columns:
        speeds = sorted(df["speed_rpm"].unique())
        for speed in speeds:
            speed_df = df[df["speed_rpm"] == speed].sort_values(by=x_col)
            x_raw = speed_df[x_col].to_numpy(dtype=float)
            y1_raw = speed_df[y1_col].to_numpy(dtype=float)
            y2_raw = speed_df[y2_col].to_numpy(dtype=float)

            # ── Smooth fitted curves ──────────────────────────────────────
            x_s1, y1_s = _smooth_series(x_raw, y1_raw, smoothing_factor=smoothing_factor)
            x_s2, y2_s = _smooth_series(x_raw, y2_raw, smoothing_factor=smoothing_factor)

            # Pressure curve (smooth line)
            fig.add_trace(
                go.Scatter(
                    x=x_s1, y=y1_s,
                    name=f'PR @ {speed} RPM',
                    mode='lines',
                    line=dict(width=2.5),
                    legendgroup=str(speed),
                ),
                secondary_y=False,
            )
            # Raw CFD points (small markers, semi-transparent)
            fig.add_trace(
                go.Scatter(
                    x=x_raw, y=y1_raw,
                    name=f'Data @ {speed} RPM',
                    mode='markers',
                    marker=dict(size=5, opacity=0.45, symbol='circle'),
                    legendgroup=str(speed),
                    showlegend=False,
                ),
                secondary_y=False,
            )

            # Power curve (smooth line, dashed)
            fig.add_trace(
                go.Scatter(
                    x=x_s2, y=y2_s,
                    name=f'Power @ {speed} RPM',
                    mode='lines',
                    line=dict(dash='dash', width=2),
                    legendgroup=str(speed),
                    legendgrouptitle_text=f'{speed} RPM' if speed == speeds[0] else None,
                ),
                secondary_y=True,
            )
            # Raw power points
            fig.add_trace(
                go.Scatter(
                    x=x_raw, y=y2_raw,
                    name=f'Power Data @ {speed} RPM',
                    mode='markers',
                    marker=dict(size=5, opacity=0.45, symbol='diamond'),
                    legendgroup=str(speed),
                    showlegend=False,
                ),
                secondary_y=True,
            )

    # Surge line (raw segment, no smoothing – it's already a straight line)
    if not surge_line_df.empty and x_col in surge_line_df.columns and y1_col in surge_line_df.columns:
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

    # Layout – engineering / publication quality
    fig.update_layout(
        title_text="Fan Performance Curve",
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
        ticks="outside", ticklen=6,
        mirror=True,
    )
    fig.update_yaxes(
        title_text=y1_label,
        secondary_y=False,
        showgrid=True, gridcolor='rgba(200,200,200,0.5)', gridwidth=1,
        showline=True, linecolor='black', linewidth=1.5,
        ticks="outside", ticklen=6,
        mirror=False,
    )
    fig.update_yaxes(
        title_text=y2_label,
        secondary_y=True,
        showgrid=False,
        showline=True, linecolor='gray', linewidth=1,
        ticks="outside", ticklen=6,
    )

    return fig
