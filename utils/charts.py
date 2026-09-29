"""
Plotly chart generation module for User Acquisition & Behavior Analytics Dashboard.
Provides modern, visually stunning charts with tailored tooltips, responsive margins,
and cohesive color harmonies.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Modern cohesive color palette
CHART_THEME = {
    "primary": "#4F46E5",     # Indigo
    "secondary": "#06B6D4",   # Cyan
    "success": "#10B981",     # Emerald
    "warning": "#F59E0B",     # Amber
    "danger": "#EF4444",      # Rose Red
    "purple": "#8B5CF6",      # Purple
    "slate": "#64748B",       # Slate
    "font_family": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
}

PALETTE = [
    "#4F46E5", "#06B6D4", "#10B981", "#F59E0B", "#8B5CF6",
    "#EC4899", "#3B82F6", "#14B8A6", "#F97316", "#6366F1"
]


def apply_base_layout(fig, title="", height=380):
    """Apply consistent styling, margins, fonts, and gridlines to Plotly figures."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=15, family=CHART_THEME["font_family"])
        ),
        height=height,
        margin=dict(l=40, r=30, t=50, b=40),
        font=dict(family=CHART_THEME["font_family"], size=12),
        hoverlabel=dict(
            font_size=12,
            font_family=CHART_THEME["font_family"]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        ),
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(148, 163, 184, 0.15)",
        zeroline=False
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(148, 163, 184, 0.15)",
        zeroline=False
    )
    return fig


def create_dual_line_chart(df, date_col, col_left, col_right, title, name_left, name_right,
                           is_currency_left=False, is_currency_right=False):
    """Create a dual-axis time-series chart (e.g. Sessions vs Conversions, or Spend vs Revenue)."""
    fig = go.Figure()
    
    if df.empty:
        fig.add_annotation(text="No data for selected filters", showarrow=False, font=dict(size=14))
        return apply_base_layout(fig, title)
        
    left_prefix = "$" if is_currency_left else ""
    right_prefix = "$" if is_currency_right else ""
    
    fig.add_trace(go.Scatter(
        x=df[date_col],
        y=df[col_left],
        name=name_left,
        mode="lines+markers",
        line=dict(color=CHART_THEME["primary"], width=2.5),
        marker=dict(size=4),
        hovertemplate=f"<b>%{{x|%b %d, %Y}}</b><br>{name_left}: {left_prefix}%{{y:,.2f}}<extra></extra>" if is_currency_left else f"<b>%{{x|%b %d, %Y}}</b><br>{name_left}: %{{y:,}}<extra></extra>"
    ))
    
    fig.add_trace(go.Scatter(
        x=df[date_col],
        y=df[col_right],
        name=name_right,
        mode="lines+markers",
        yaxis="y2",
        line=dict(color=CHART_THEME["success"], width=2.5, dash="dot"),
        marker=dict(size=4),
        hovertemplate=f"<b>%{{x|%b %d, %Y}}</b><br>{name_right}: {right_prefix}%{{y:,.2f}}<extra></extra>" if is_currency_right else f"<b>%{{x|%b %d, %Y}}</b><br>{name_right}: %{{y:,}}<extra></extra>"
    ))
    
    fig = apply_base_layout(fig, title)
    fig.update_layout(
        yaxis=dict(
            title=dict(text=name_left, font=dict(color=CHART_THEME["primary"]))
        ),
        yaxis2=dict(
            title=dict(text=name_right, font=dict(color=CHART_THEME["success"])),
            overlaying="y",
            side="right",
            showgrid=False
        )
    )
    return fig


def create_donut_chart(df, labels_col, values_col, title, hole=0.55):
    """Create a sleek donut chart for channel or device distributions."""
    fig = go.Figure()
    
    if df.empty or df[values_col].sum() == 0:
        fig.add_annotation(text="No data for selected filters", showarrow=False, font=dict(size=14))
        return apply_base_layout(fig, title)
        
    fig.add_trace(go.Pie(
        labels=df[labels_col],
        values=df[values_col],
        hole=hole,
        marker=dict(colors=PALETTE[:len(df)]),
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Share: %{percent}<br>Total: %{value:,.0f}<extra></extra>"
    ))
    
    fig = apply_base_layout(fig, title)
    fig.update_layout(showlegend=False)
    return fig


def create_horizontal_bar_chart(df, y_col, x_col, title, x_title="", is_percent=False, is_currency=False):
    """Create a styled horizontal bar chart."""
    fig = go.Figure()
    
    if df.empty:
        fig.add_annotation(text="No data for selected filters", showarrow=False, font=dict(size=14))
        return apply_base_layout(fig, title)
        
    # Sort for visual hierarchy
    sorted_df = df.sort_values(by=x_col, ascending=True)
    
    fmt = ".2%" if is_percent else ("$,.2f" if is_currency else ",.0f")
    
    fig.add_trace(go.Bar(
        y=sorted_df[y_col],
        x=sorted_df[x_col],
        orientation="h",
        marker=dict(
            color=sorted_df[x_col],
            colorscale=[[0, "#818CF8"], [1, "#4338CA"]],
            line=dict(width=0)
        ),
        text=sorted_df[x_col].apply(lambda v: f"{v*100:.1f}%" if is_percent else (f"${v:,.2f}" if is_currency else f"{v:,.0f}")),
        textposition="outside",
        hovertemplate=f"<b>%{{y}}</b><br>{x_title}: %{{x:{fmt}}}<extra></extra>"
    ))
    
    fig = apply_base_layout(fig, title, height=max(320, len(df) * 35))
    fig.update_xaxes(title_text=x_title)
    return fig


def create_funnel_chart(stages, counts, drop_offs=None):
    """
    Create an e-commerce conversion funnel chart with stages, counts, and dual conversion percentages.
    Clearly distinguishes Entry-Session Conversion Rate (%) vs. Step Conversion Rate (%).
    """
    fig = go.Figure()
    
    if not counts or sum(counts) == 0:
        fig.add_annotation(text="No funnel event data available", showarrow=False, font=dict(size=14))
        return apply_base_layout(fig, "E-Commerce User Conversion Funnel")
        
    bar_texts = []
    custom_data = []
    base_count = counts[0] if counts[0] > 0 else 0
    
    for i in range(len(counts)):
        cnt = counts[i]
        entry_pct = (cnt / base_count * 100) if base_count > 0 else 0.0
        
        if i == 0:
            step_pct = 100.0 if base_count > 0 else 0.0
            drop_pct = 0.0
            bar_text = f"{cnt:,} sessions (100% of Entry)"
        else:
            prev_cnt = counts[i - 1]
            step_pct = (cnt / prev_cnt * 100) if prev_cnt > 0 else 0.0
            if drop_offs is not None and i < len(drop_offs):
                drop_pct = drop_offs[i] * 100
            else:
                drop_pct = ((prev_cnt - cnt) / prev_cnt * 100) if prev_cnt > 0 else 0.0
            bar_text = f"{cnt:,} ({entry_pct:.1f}% Entry | {step_pct:.1f}% Step)"
            
        bar_texts.append(bar_text)
        custom_data.append([entry_pct, step_pct, drop_pct])
        
    fig.add_trace(go.Funnel(
        y=stages,
        x=counts,
        text=bar_texts,
        textinfo="text",
        opacity=0.9,
        marker=dict(
            color=["#4F46E5", "#3B82F6", "#06B6D4", "#10B981", "#059669"],
            line=dict(width=1, color="rgba(255,255,255,0.2)")
        ),
        connector=dict(line=dict(color="rgba(148, 163, 184, 0.4)", width=1)),
        customdata=custom_data,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Sessions: %{x:,}<br>"
            "Entry-Session Conversion Rate: %{customdata[0]:.1f}% (vs Stage 1)<br>"
            "Step Conversion Rate: %{customdata[1]:.1f}% (vs previous stage)<br>"
            "Drop-off Rate: %{customdata[2]:.1f}%<extra></extra>"
        )
    ))
    
    fig = apply_base_layout(fig, "E-Commerce User Conversion Funnel", height=420)
    fig.update_layout(margin=dict(l=150, r=40, t=50, b=40))
    return fig


def create_scatter_plot(df, x_col, y_col, size_col, text_col, title, x_title, y_title,
                        is_x_percent=False, is_y_percent=False):
    """Create a bubble/scatter chart (e.g. CTR vs Position or CPC vs ROAS)."""
    fig = go.Figure()
    
    if df.empty:
        fig.add_annotation(text="No data for selected filters", showarrow=False, font=dict(size=14))
        return apply_base_layout(fig, title)
        
    # Scale bubble sizes safely
    sizes = df[size_col] if size_col and size_col in df.columns else [10] * len(df)
    max_size = max(sizes) if max(sizes) > 0 else 1
    scaled_sizes = [max(8, min(40, (s / max_size) * 35)) for s in sizes]
    
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode="markers+text",
        text=df[text_col] if text_col and text_col in df.columns else None,
        textposition="top center",
        marker=dict(
            size=scaled_sizes,
            color=df[y_col],
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title=dict(text=y_title), len=0.7),
            line=dict(width=1, color="rgba(0,0,0,0.2)")
        ),
        hovertemplate=f"<b>%{{text}}</b><br>{x_title}: %{{x}}<br>{y_title}: %{{y}}<br>{size_col}: %{{marker.size}}<extra></extra>"
    ))
    
    fig = apply_base_layout(fig, title, height=400)
    fig.update_xaxes(title_text=x_title)
    fig.update_yaxes(title_text=y_title)
    return fig


def create_grouped_bar_chart(df, x_col, y1_col, y2_col, title, name1, name2, y_title=""):
    """Create a grouped bar chart comparing two metrics across dimensions (e.g. Clicks vs Sessions)."""
    fig = go.Figure()
    
    if df.empty:
        fig.add_annotation(text="No data for selected filters", showarrow=False, font=dict(size=14))
        return apply_base_layout(fig, title)
        
    fig.add_trace(go.Bar(
        x=df[x_col],
        y=df[y1_col],
        name=name1,
        marker_color=CHART_THEME["secondary"],
        hovertemplate=f"<b>%{{x}}</b><br>{name1}: %{{y:,}}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        x=df[x_col],
        y=df[y2_col],
        name=name2,
        marker_color=CHART_THEME["primary"],
        hovertemplate=f"<b>%{{x}}</b><br>{name2}: %{{y:,}}<extra></extra>"
    ))
    
    fig = apply_base_layout(fig, title)
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text=y_title)
    return fig
