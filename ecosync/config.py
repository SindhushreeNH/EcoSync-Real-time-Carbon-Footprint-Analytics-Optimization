"""Configuration settings for EcoSync."""

# Carbon emission factors (kg CO2 per kWh) by region
EMISSION_FACTORS = {
    "us_average": 0.42,
    "eu_average": 0.30,
    "uk": 0.23,
    "germany": 0.35,
    "france": 0.05,
    "china": 0.58,
    "india": 0.71,
}

# Power consumption estimates (Watts)
POWER_ESTIMATES = {
    "cpu_tdp_default": 65,
    "ram_per_gb": 3,
    "idle_factor": 0.3,
}

# Green scheduling thresholds
SCHEDULING_CONFIG = {
    "low_carbon_threshold": 0.25,  # kg CO2/kWh
    "peak_hours": list(range(9, 18)),  # 9 AM to 6 PM
    "off_peak_hours": list(range(0, 6)) + list(range(22, 24)),
}

# Dashboard refresh rate (seconds)
REFRESH_RATE = 5

# Trees absorption rate (kg CO2 per tree per year)
TREE_ABSORPTION_RATE = 21.77
