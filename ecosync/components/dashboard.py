"""Real-time dashboard component."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import config


def render_dashboard(data_collector, carbon_calculator):
    """Render the main dashboard."""
    st.header("📊 Real-time Carbon Dashboard")

    # Get sample data for demonstration
    df = data_collector.generate_sample_data(hours=168)

    # Calculate emissions for historical data
    emissions_data = []
    for _, row in df.iterrows():
        emission = carbon_calculator.calculate_total_emissions(
            cpu_percent=row["cpu_percent"],
            ram_gb=row["ram_used_gb"],
            duration_hours=1,
        )
        emissions_data.append(
            {
                "timestamp": row["timestamp"],
                "carbon_kg": emission["total_carbon_kg"],
                "kwh": emission["total_kwh"],
                "carbon_intensity": row["carbon_intensity"],
            }
        )

    emissions_df = pd.DataFrame(emissions_data)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_carbon = emissions_df["carbon_kg"].sum()
        st.metric(
            "Total Carbon (7 days)",
            f"{total_carbon:.2f} kg CO₂",
            delta=f"{(total_carbon / 7):.2f} kg/day avg",
        )

    with col2:
        total_kwh = emissions_df["kwh"].sum()
        st.metric(
            "Energy Consumed",
            f"{total_kwh:.2f} kWh",
            delta=f"{(total_kwh / 7):.2f} kWh/day",
        )

    with col3:
        trees_equivalent = total_carbon / (config.TREE_ABSORPTION_RATE / 365)
        st.metric(
            "🌳 Trees Needed (Daily)",
            f"{trees_equivalent:.1f}",
            help="Trees needed to offset this carbon (daily equivalent)",
        )

    with col4:
        avg_intensity = emissions_df["carbon_intensity"].mean()
        st.metric(
            "Avg Carbon Intensity",
            f"{avg_intensity:.3f} kg/kWh",
            delta="Grid average" if avg_intensity < 0.4 else "Above average",
            delta_color="normal" if avg_intensity < 0.4 else "inverse",
        )

    st.divider()

    # Live carbon intensity chart
    st.subheader("Carbon Intensity Over Time")

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Carbon Emissions (kg CO₂/hour)", "Grid Carbon Intensity"),
    )

    fig.add_trace(
        go.Scatter(
            x=emissions_df["timestamp"],
            y=emissions_df["carbon_kg"],
            mode="lines",
            name="Carbon Emissions",
            fill="tozeroy",
            fillcolor="rgba(255, 99, 71, 0.3)",
            line=dict(color="tomato"),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=emissions_df["timestamp"],
            y=emissions_df["carbon_intensity"],
            mode="lines",
            name="Grid Intensity",
            line=dict(color="forestgreen"),
        ),
        row=2,
        col=1,
    )

    # Add threshold line
    fig.add_hline(
        y=config.SCHEDULING_CONFIG["low_carbon_threshold"],
        line_dash="dash",
        line_color="green",
        annotation_text="Green Threshold",
        row=2,
        col=1,
    )

    fig.update_layout(height=500, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    # Resource usage breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("CPU Usage Distribution")
        fig_cpu = px.histogram(
            df,
            x="cpu_percent",
            nbins=30,
            color_discrete_sequence=["steelblue"],
        )
        fig_cpu.update_layout(
            xaxis_title="CPU Usage (%)", yaxis_title="Frequency"
        )
        st.plotly_chart(fig_cpu, use_container_width=True)

    with col2:
        st.subheader("Hourly Carbon Pattern")
        hourly_avg = emissions_df.copy()
        hourly_avg["hour"] = pd.to_datetime(hourly_avg["timestamp"]).dt.hour
        hourly_pattern = hourly_avg.groupby("hour")["carbon_kg"].mean().reset_index()

        fig_hourly = px.bar(
            hourly_pattern,
            x="hour",
            y="carbon_kg",
            color="carbon_kg",
            color_continuous_scale="RdYlGn_r",
        )
        fig_hourly.update_layout(
            xaxis_title="Hour of Day", yaxis_title="Avg Carbon (kg)"
        )
        st.plotly_chart(fig_hourly, use_container_width=True)

    # Daily summary table
    st.subheader("Daily Summary")
    daily_summary = emissions_df.copy()
    daily_summary["date"] = pd.to_datetime(daily_summary["timestamp"]).dt.date
    daily_agg = (
        daily_summary.groupby("date")
        .agg(
            {
                "carbon_kg": "sum",
                "kwh": "sum",
                "carbon_intensity": "mean",
            }
        )
        .reset_index()
    )
    daily_agg.columns = ["Date", "Carbon (kg)", "Energy (kWh)", "Avg Intensity"]
    daily_agg["Trees Equivalent"] = daily_agg["Carbon (kg)"] / (
        config.TREE_ABSORPTION_RATE / 365
    )

    st.dataframe(
        daily_agg.style.format(
            {
                "Carbon (kg)": "{:.3f}",
                "Energy (kWh)": "{:.4f}",
                "Avg Intensity": "{:.3f}",
                "Trees Equivalent": "{:.2f}",
            }
        ),
        use_container_width=True,
    )
