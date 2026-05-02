"""Green scheduling optimization utilities."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config


class GreenScheduler:
    """Schedule tasks during low-carbon periods."""

    def __init__(self):
        self.scheduled_tasks = []

    def find_green_windows(
        self, carbon_data: pd.DataFrame, window_hours: int = 2
    ) -> list:
        """Find optimal low-carbon time windows."""
        if carbon_data.empty:
            return []

        df = carbon_data.copy()
        df = df.sort_values("timestamp")

        # Calculate rolling average carbon intensity
        df["rolling_carbon"] = (
            df["carbon_intensity"].rolling(window=window_hours, min_periods=1).mean()
        )

        # Find windows below threshold
        green_windows = []
        threshold = config.SCHEDULING_CONFIG["low_carbon_threshold"]

        low_carbon_periods = df[df["rolling_carbon"] < threshold]

        if not low_carbon_periods.empty:
            # Group consecutive periods
            low_carbon_periods = low_carbon_periods.copy()
            low_carbon_periods["group"] = (
                low_carbon_periods["timestamp"].diff() > timedelta(hours=1)
            ).cumsum()

            for _, group in low_carbon_periods.groupby("group"):
                green_windows.append(
                    {
                        "start": group["timestamp"].min(),
                        "end": group["timestamp"].max(),
                        "avg_carbon": group["carbon_intensity"].mean(),
                        "duration_hours": len(group),
                    }
                )

        return sorted(green_windows, key=lambda x: x["avg_carbon"])

    def get_scheduling_recommendation(
        self, task_duration_hours: float, carbon_forecast: pd.DataFrame
    ) -> dict:
        """Get recommendation for scheduling a task."""
        if carbon_forecast.empty:
            return {"recommendation": "No forecast data available"}

        # Find the best window
        windows = self.find_green_windows(
            carbon_forecast, window_hours=int(np.ceil(task_duration_hours))
        )

        if not windows:
            # Find the lowest carbon period anyway
            best_time = carbon_forecast.loc[
                carbon_forecast["carbon_intensity"].idxmin()
            ]
            return {
                "recommendation": "Schedule at lowest available carbon intensity",
                "suggested_start": best_time["timestamp"],
                "expected_carbon_intensity": best_time["carbon_intensity"],
                "is_green_window": False,
            }

        best_window = windows[0]
        return {
            "recommendation": "Green window available",
            "suggested_start": best_window["start"],
            "suggested_end": best_window["end"],
            "expected_carbon_intensity": best_window["avg_carbon"],
            "is_green_window": True,
            "potential_savings_percent": round(
                (1 - best_window["avg_carbon"] / carbon_forecast["carbon_intensity"].mean())
                * 100,
                1,
            ),
        }

    def calculate_carbon_savings(
        self,
        task_kwh: float,
        current_intensity: float,
        optimal_intensity: float,
    ) -> dict:
        """Calculate potential carbon savings from rescheduling."""
        current_emissions = task_kwh * current_intensity
        optimal_emissions = task_kwh * optimal_intensity
        savings = current_emissions - optimal_emissions

        return {
            "current_emissions_kg": round(current_emissions, 4),
            "optimal_emissions_kg": round(optimal_emissions, 4),
            "savings_kg": round(savings, 4),
            "savings_percent": round((savings / current_emissions) * 100, 1)
            if current_emissions > 0
            else 0,
            "trees_saved_daily": round(savings / (config.TREE_ABSORPTION_RATE / 365), 4),
        }

    def add_scheduled_task(self, task: dict):
        """Add a task to the schedule."""
        self.scheduled_tasks.append(task)

    def get_scheduled_tasks(self) -> list:
        """Get all scheduled tasks."""
        return self.scheduled_tasks
