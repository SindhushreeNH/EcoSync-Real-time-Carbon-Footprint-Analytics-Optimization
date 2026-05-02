"""Green scheduler component."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from models.carbon_model import CarbonForecastModel
import config


def render_scheduler(data_collector, carbon_calculator, green_scheduler):
    """Render the green scheduler page."""
    st.header("🌿 Green Scheduler")

    st.markdown(
        """
        Schedule your compute-intensive tasks during low-carbon periods 
        to minimize environmental impact.
        """
    )

    # Generate data and forecast
    df = data_collector.generate_sample_data(hours=168)
    model = CarbonForecastModel()
    model.fit(df)
    forecast = model.predict(hours_ahead=48)

    # Task configuration
    st.subheader("Configure Task")

    col1, col2 = st.columns(2)

    with col1:
        task_name = st.text_input("Task Name", "Data Backup")
        task_duration = st.slider("Duration (hours)", 1, 12, 2)
        cpu_usage = st.slider("Expected CPU Usage (%)", 10, 100, 50)

    with col2:
        task_type = st.selectbox(
            "Task Type",
            ["Backup", "Model Training", "Data Processing", "Batch Job", "Other"],
        )
        ram_usage = st.slider("Expected RAM (GB)", 1, 64, 8)
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])

    # Get scheduling recommendation
    if st.button("🔍 Find Optimal Schedule", type="primary"):
        recommendation = green_scheduler.get_scheduling_recommendation(
            task_duration, forecast
        )

        st.divider()
        st.subheader("Scheduling Recommendation")

        if recommendation.get("is_green_window"):
            st.success("✅ Green window found!")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Suggested Start",
                    recommendation["suggested_start"].strftime("%Y-%m-%d %H:%M"),
                )
            with col2:
                st.metric(
                    "Carbon Intensity",
                    f"{recommendation['expected_carbon_intensity']:.3f} kg/kWh",
                )
            with col3:
                st.metric(
                    "Potential Savings",
                    f"{recommendation.get('potential_savings_percent', 0):.1f}%",
                )
        else:
            st.warning("⚠️ No ideal green window in forecast period")
            st.info(f"Best available: {recommendation.get('suggested_start')}")

        # Calculate savings
        current_intensity = df["carbon_intensity"].iloc[-1]
        optimal_intensity = recommendation.get("expected_carbon_intensity", 0.3)

        emissions = carbon_calculator.calculate_total_emissions(
            cpu_usage, ram_usage, task_duration
        )

        savings = green_scheduler.calculate_carbon_savings(
            emissions["total_kwh"], current_intensity, optimal_intensity
        )

        st.subheader("Estimated Impact")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("If Run Now", f"{savings['current_emissions_kg']:.4f} kg CO₂")
        with col2:
            st.metric(
                "If Optimized", f"{savings['optimal_emissions_kg']:.4f} kg CO₂"
            )
        with col3:
            st.metric(
                "Savings",
                f"{savings['savings_kg']:.4f} kg",
                delta=f"{savings['savings_percent']}%",
            )
        with col4:
            st.metric("🌳 Trees Saved", f"{savings['trees_saved_daily']:.4f}")

    # Forecast visualization
    st.divider()
    st.subheader("48-Hour Carbon Forecast")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=forecast["timestamp"],
            y=forecast["carbon_intensity"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color="steelblue"),
        )
    )

    # Highlight green windows
    green_mask = forecast["carbon_intensity"] < config.SCHEDULING_CONFIG["low_carbon_threshold"]
    green_periods = forecast[green_mask]

    fig.add_trace(
        go.Scatter(
            x=green_periods["timestamp"],
            y=green_periods["carbon_intensity"],
            mode="markers",
            name="Green Windows",
            marker=dict(color="green", size=12, symbol="star"),
        )
    )

    fig.add_hline(
        y=config.SCHEDULING_CONFIG["low_carbon_threshold"],
        line_dash="dash",
        line_color="green",
        annotation_text="Green Threshold",
    )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Carbon Intensity (kg CO₂/kWh)",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Green windows table
    windows = green_scheduler.find_green_windows(forecast, window_hours=2)

    if windows:
        st.subheader("Available Green Windows")
        windows_df = pd.DataFrame(windows)
        windows_df["start"] = pd.to_datetime(windows_df["start"]).dt.strftime(
            "%Y-%m-%d %H:%M"
        )
        windows_df["end"] = pd.to_datetime(windows_df["end"]).dt.strftime("%H:%M")
        windows_df["avg_carbon"] = windows_df["avg_carbon"].round(3)
        windows_df.columns = ["Start", "End", "Avg Intensity", "Duration (hrs)"]
        st.dataframe(windows_df, use_container_width=True)
    else:
        st.info("No green windows available in the forecast period.")

    # Tips
    st.divider()
    st.subheader("💡 Optimization Tips")

    tips = [
        "**Batch similar tasks** together to run during a single green window",
        "**Pre-schedule recurring jobs** (like backups) during off-peak hours (22:00-06:00)",
        "**Spread non-urgent workloads** across multiple green windows",
        "**Monitor patterns** to identify consistent low-carbon periods in your region",
        "**Consider workload shifting** to regions with cleaner grids when possible",
    ]

    for tip in tips:
        st.markdown(f"- {tip}")
