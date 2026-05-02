"""System resource data collection utilities."""

import psutil
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


class DataCollector:
    """Collect system resource usage data."""

    def __init__(self):
        self.history = []

    def get_current_metrics(self) -> dict:
        """Get current system resource metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        return {
            "timestamp": datetime.now(),
            "cpu_percent": cpu_percent,
            "ram_used_gb": memory.used / (1024**3),
            "ram_total_gb": memory.total / (1024**3),
            "ram_percent": memory.percent,
        }

    def collect_sample(self) -> dict:
        """Collect and store a sample."""
        metrics = self.get_current_metrics()
        self.history.append(metrics)
        return metrics

    def get_history_df(self) -> pd.DataFrame:
        """Get historical data as DataFrame."""
        if not self.history:
            return pd.DataFrame()
        return pd.DataFrame(self.history)

    def generate_sample_data(self, hours: int = 168) -> pd.DataFrame:
        """Generate realistic sample data for demonstration."""
        np.random.seed(42)
        timestamps = pd.date_range(
            end=datetime.now(), periods=hours, freq="h"
        )

        # Simulate daily patterns
        hour_of_day = timestamps.hour
        day_of_week = timestamps.dayofweek

        # Base load with daily pattern
        base_cpu = 20 + 30 * np.sin((hour_of_day - 6) * np.pi / 12)
        base_cpu = np.clip(base_cpu, 10, 80)

        # Weekend reduction
        weekend_factor = np.where(day_of_week >= 5, 0.6, 1.0)
        cpu_percent = base_cpu * weekend_factor + np.random.normal(0, 5, hours)
        cpu_percent = np.clip(cpu_percent, 5, 95)

        # RAM follows similar pattern but more stable
        ram_percent = 40 + 0.3 * cpu_percent + np.random.normal(0, 3, hours)
        ram_percent = np.clip(ram_percent, 20, 85)

        # Simulate varying carbon intensity (grid mix)
        carbon_intensity = 0.35 + 0.15 * np.sin(
            (hour_of_day - 14) * np.pi / 12
        ) + np.random.normal(0, 0.03, hours)
        carbon_intensity = np.clip(carbon_intensity, 0.1, 0.6)

        df = pd.DataFrame(
            {
                "timestamp": timestamps,
                "cpu_percent": cpu_percent,
                "ram_percent": ram_percent,
                "ram_used_gb": ram_percent * 0.32,  # Assuming 32GB total
                "carbon_intensity": carbon_intensity,
            }
        )

        return df

    def clear_history(self):
        """Clear collected history."""
        self.history = []
