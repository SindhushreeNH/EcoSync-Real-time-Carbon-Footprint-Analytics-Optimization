"""EcoSync: Real-time Carbon Footprint Analytics & Optimization."""

import streamlit as st
from utils import CarbonCalculator, DataCollector, GreenScheduler
from components import render_dashboard, render_analytics, render_scheduler
import config

# Page configuration
st.set_page_config(
    page_title="EcoSync - Carbon Analytics",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    .main > div {
        padding-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize session state variables."""
    if "data_collector" not in st.session_state:
        st.session_state.data_collector = DataCollector()
    if "carbon_calculator" not in st.session_state:
        st.session_state.carbon_calculator = CarbonCalculator()
    if "green_scheduler" not in st.session_state:
        st.session_state.green_scheduler = GreenScheduler()


def main():
    """Main application entry point."""
    init_session_state()

    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/earth-planet.png", width=80)
        st.title("EcoSync")
        st.markdown("*Carbon Footprint Analytics*")

        st.divider()

        # Navigation
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "📈 Analytics", "🌿 Green Scheduler"],
            label_visibility="collapsed",
        )

        st.divider()

        # Settings
        st.subheader("⚙️ Settings")

        region = st.selectbox(
            "Region",
            list(config.EMISSION_FACTORS.keys()),
            format_func=lambda x: x.replace("_", " ").title(),
        )
        st.session_state.carbon_calculator.set_region(region)

        st.caption(
            f"Emission Factor: {config.EMISSION_FACTORS[region]} kg CO₂/kWh"
        )

        st.divider()

        # Info
        st.markdown(
            """
            ### About
            EcoSync helps you monitor and optimize 
            your computational carbon footprint.
            
            **Features:**
            - Real-time monitoring
            - AI-powered forecasting
            - Smart scheduling
            - Emissions tracking
            """
        )

        st.divider()
        st.caption("Built with ❤️ for sustainability")

    # Main content
    if page == "📊 Dashboard":
        render_dashboard(
            st.session_state.data_collector,
            st.session_state.carbon_calculator,
        )
    elif page == "📈 Analytics":
        render_analytics(
            st.session_state.data_collector,
            st.session_state.carbon_calculator,
        )
    elif page == "🌿 Green Scheduler":
        render_scheduler(
            st.session_state.data_collector,
            st.session_state.carbon_calculator,
            st.session_state.green_scheduler,
        )


if __name__ == "__main__":
    main()
