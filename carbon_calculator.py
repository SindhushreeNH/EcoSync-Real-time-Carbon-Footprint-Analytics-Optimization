"""Carbon footprint calculation utilities."""

import config


class CarbonCalculator:
    """Calculate carbon emissions from computational resources."""

    def __init__(self, region: str = "us_average"):
        self.region = region
        self.emission_factor = config.EMISSION_FACTORS.get(
            region, config.EMISSION_FACTORS["us_average"]
        )

    def cpu_to_kwh(
        self, cpu_percent: float, duration_hours: float, tdp_watts: int = 65
    ) -> float:
        """Convert CPU usage to kWh."""
        actual_power = tdp_watts * (
            config.POWER_ESTIMATES["idle_factor"]
            + (1 - config.POWER_ESTIMATES["idle_factor"]) * (cpu_percent / 100)
        )
        return (actual_power * duration_hours) / 1000

    def ram_to_kwh(self, ram_gb: float, duration_hours: float) -> float:
        """Convert RAM usage to kWh."""
        power_watts = ram_gb * config.POWER_ESTIMATES["ram_per_gb"]
        return (power_watts * duration_hours) / 1000

    def kwh_to_carbon(self, kwh: float) -> float:
        """Convert kWh to kg CO2."""
        return kwh * self.emission_factor

    def calculate_total_emissions(
        self,
        cpu_percent: float,
        ram_gb: float,
        duration_hours: float,
        tdp_watts: int = 65,
    ) -> dict:
        """Calculate total carbon emissions from system usage."""
        cpu_kwh = self.cpu_to_kwh(cpu_percent, duration_hours, tdp_watts)
        ram_kwh = self.ram_to_kwh(ram_gb, duration_hours)
        total_kwh = cpu_kwh + ram_kwh
        total_carbon = self.kwh_to_carbon(total_kwh)

        return {
            "cpu_kwh": round(cpu_kwh, 6),
            "ram_kwh": round(ram_kwh, 6),
            "total_kwh": round(total_kwh, 6),
            "total_carbon_kg": round(total_carbon, 6),
            "trees_equivalent": round(
                total_carbon / (config.TREE_ABSORPTION_RATE / 365), 4
            ),
        }

    def set_region(self, region: str):
        """Update the region and emission factor."""
        self.region = region
        self.emission_factor = config.EMISSION_FACTORS.get(
            region, config.EMISSION_FACTORS["us_average"]
        )
