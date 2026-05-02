"""Carbon emission forecasting models (Streamlit Cloud safe version)."""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Prevent Prophet Stan backend crash on Streamlit Cloud
os.environ["CMDSTAN"] = ""

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except Exception:
    PROPHET_AVAILABLE = False


class CarbonForecastModel:
    """Forecast carbon emissions using time series analysis."""

    def __init__(self, model_type: str = "prophet"):
        self.model_type = model_type
        self.model = None
        self.is_fitted = False
        self._last_data = None
        self.use_prophet = PROPHET_AVAILABLE

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for Prophet model."""
        prophet_df = df[["timestamp", "carbon_intensity"]].copy()
        prophet_df.columns = ["ds", "y"]
        prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
        return prophet_df

    def fit(self, df: pd.DataFrame):
        """Fit forecasting model with automatic fallback."""
        self._last_data = df.copy()

        # Try Prophet first
        if self.use_prophet:
            try:
                prophet_df = self.prepare_data(df)

                self.model = Prophet(
                    daily_seasonality=True,
                    weekly_seasonality=True,
                    yearly_seasonality=False,
                    changepoint_prior_scale=0.05,
                )

                self.model.fit(prophet_df)
                self.is_fitted = True
                return

            except Exception as e:
                print("Prophet backend failed, switching to fallback model:", e)
                self.use_prophet = False

        # Fallback model (no Prophet)
        self.is_fitted = True

    def predict(self, hours_ahead: int = 24) -> pd.DataFrame:
        """Generate forecast for future hours."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        # Use Prophet if available
        if self.use_prophet and self.model is not None:
            try:
                future = self.model.make_future_dataframe(
                    periods=hours_ahead,
                    freq="h"
                )

                forecast = self.model.predict(future)

                result = forecast[
                    ["ds", "yhat", "yhat_lower", "yhat_upper"]
                ].tail(hours_ahead)

                result.columns = [
                    "timestamp",
                    "carbon_intensity",
                    "carbon_lower",
                    "carbon_upper",
                ]

                return self._clip_values(result)

            except Exception as e:
                print("Prediction failed, using fallback:", e)

        # fallback prediction
        return self._simple_forecast(hours_ahead)

    def _simple_forecast(self, hours_ahead: int) -> pd.DataFrame:
        """Simple fallback forecast without Prophet."""
        last_time = self._last_data["timestamp"].max()

        future_times = pd.date_range(
            start=last_time + timedelta(hours=1),
            periods=hours_ahead,
            freq="h",
        )

        hour_means = self._last_data.groupby(
            self._last_data["timestamp"].dt.hour
        )["carbon_intensity"].mean()

        predictions = []

        for t in future_times:
            base = hour_means.get(t.hour, 0.35)
            noise = np.random.normal(0, 0.02)
            predictions.append(np.clip(base + noise, 0.05, 0.8))

        result = pd.DataFrame(
            {
                "timestamp": future_times,
                "carbon_intensity": predictions,
                "carbon_lower": [p - 0.05 for p in predictions],
                "carbon_upper": [p + 0.05 for p in predictions],
            }
        )

        return self._clip_values(result)

    def _clip_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure forecast values remain realistic."""
        df["carbon_intensity"] = df["carbon_intensity"].clip(0.05, 0.8)
        df["carbon_lower"] = df["carbon_lower"].clip(0.05, 0.8)
        df["carbon_upper"] = df["carbon_upper"].clip(0.05, 0.8)
        return df


class EmissionPredictor:
    """Predict total emissions based on workload forecasts."""

    def __init__(self, carbon_calculator):
        self.calculator = carbon_calculator
        self.carbon_model = CarbonForecastModel()

    def predict_task_emissions(
        self,
        cpu_percent: float,
        ram_gb: float,
        duration_hours: float,
        scheduled_time: datetime,
        carbon_forecast: pd.DataFrame,
    ) -> dict:
        """Predict emissions for a scheduled task."""

        forecast_at_time = carbon_forecast[
            carbon_forecast["timestamp"] >= scheduled_time
        ].head(int(np.ceil(duration_hours)))

        if forecast_at_time.empty:
            avg_intensity = 0.35
        else:
            avg_intensity = forecast_at_time["carbon_intensity"].mean()

        emissions = self.calculator.calculate_total_emissions(
            cpu_percent,
            ram_gb,
            duration_hours,
        )

        self.calculator.emission_factor = avg_intensity

        adjusted_emissions = self.calculator.calculate_total_emissions(
            cpu_percent,
            ram_gb,
            duration_hours,
        )

        return {
            "scheduled_time": scheduled_time,
            "duration_hours": duration_hours,
            "forecasted_carbon_intensity": round(avg_intensity, 3),
            "predicted_kwh": adjusted_emissions["total_kwh"],
            "predicted_carbon_kg": adjusted_emissions["total_carbon_kg"],
            "confidence": (
                "high"
                if len(forecast_at_time) >= duration_hours
                else "medium"
            ),
        }
