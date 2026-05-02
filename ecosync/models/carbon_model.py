"""Carbon emission forecasting models."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


class CarbonForecastModel:
    """Forecast carbon emissions using time series analysis."""

    def __init__(self, model_type: str = "prophet"):
        self.model_type = model_type
        self.model = None
        self.is_fitted = False

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for Prophet model."""
        prophet_df = df[["timestamp", "carbon_intensity"]].copy()
        prophet_df.columns = ["ds", "y"]
        prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
        return prophet_df

    def fit(self, df: pd.DataFrame):
        """Fit the forecasting model."""
        if not PROPHET_AVAILABLE:
            self.is_fitted = True
            self._last_data = df.copy()
            return

        prophet_df = self.prepare_data(df)

        self.model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        self.model.fit(prophet_df)
        self.is_fitted = True

    def predict(self, hours_ahead: int = 24) -> pd.DataFrame:
        """Generate forecast for future hours."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        if not PROPHET_AVAILABLE:
            return self._simple_forecast(hours_ahead)

        future = self.model.make_future_dataframe(periods=hours_ahead, freq="h")
        forecast = self.model.predict(future)

        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(hours_ahead)
        result.columns = [
            "timestamp",
            "carbon_intensity",
            "carbon_lower",
            "carbon_upper",
        ]

        # Clip to realistic values
        result["carbon_intensity"] = result["carbon_intensity"].clip(0.05, 0.8)
        result["carbon_lower"] = result["carbon_lower"].clip(0.05, 0.8)
        result["carbon_upper"] = result["carbon_upper"].clip(0.05, 0.8)

        return result

    def _simple_forecast(self, hours_ahead: int) -> pd.DataFrame:
        """Simple fallback forecast without Prophet."""
        last_time = self._last_data["timestamp"].max()
        future_times = pd.date_range(
            start=last_time + timedelta(hours=1), periods=hours_ahead, freq="h"
        )

        # Use historical patterns
        hour_means = self._last_data.groupby(
            self._last_data["timestamp"].dt.hour
        )["carbon_intensity"].mean()

        predictions = []
        for t in future_times:
            base = hour_means.get(t.hour, 0.35)
            noise = np.random.normal(0, 0.02)
            predictions.append(np.clip(base + noise, 0.05, 0.8))

        return pd.DataFrame(
            {
                "timestamp": future_times,
                "carbon_intensity": predictions,
                "carbon_lower": [p - 0.05 for p in predictions],
                "carbon_upper": [p + 0.05 for p in predictions],
            }
        )


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
        # Find carbon intensity at scheduled time
        forecast_at_time = carbon_forecast[
            carbon_forecast["timestamp"] >= scheduled_time
        ].head(int(np.ceil(duration_hours)))

        if forecast_at_time.empty:
            avg_intensity = 0.35
        else:
            avg_intensity = forecast_at_time["carbon_intensity"].mean()

        # Calculate energy consumption
        emissions = self.calculator.calculate_total_emissions(
            cpu_percent, ram_gb, duration_hours
        )

        # Adjust for forecasted carbon intensity
        self.calculator.emission_factor = avg_intensity
        adjusted_emissions = self.calculator.calculate_total_emissions(
            cpu_percent, ram_gb, duration_hours
        )

        return {
            "scheduled_time": scheduled_time,
            "duration_hours": duration_hours,
            "forecasted_carbon_intensity": round(avg_intensity, 3),
            "predicted_kwh": adjusted_emissions["total_kwh"],
            "predicted_carbon_kg": adjusted_emissions["total_carbon_kg"],
            "confidence": "high" if len(forecast_at_time) >= duration_hours else "medium",
        }
