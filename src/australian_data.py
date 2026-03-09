"""
Australian transport data module.

Provides calibrated parameters for the simulation based on publicly available
Australian data sources:

- ABS Motor Vehicle Census (2023): fleet composition, growth trends
- BITRE Information Sheet 109: road expenditure and revenue
- BITRE Yearbook: vehicle-km travelled by road type and vehicle class
- Infrastructure Australia: congestion cost estimates
- ATAP (Australian Transport Assessment and Planning): value of time
- NTC Heavy Vehicle Charges: mass-distance cost data
- State transport surveys (VISTA, HTS): trip purpose and time-of-day profiles
- CSIRO GenCost / ABS: fuel and energy cost projections
- National Greenhouse Accounts Factors (DCCEEW): emission factors

All monetary values in 2024 AUD unless stated otherwise.
"""

import numpy as np

# ---------------------------------------------------------------------------
# Vehicle fleet composition (ABS Motor Vehicle Census 2023, projected to 2026)
# ---------------------------------------------------------------------------
FLEET = {
    "passenger_ice": {
        "label": "Passenger – ICE",
        "count": 14_200_000,
        "avg_mass_t": 1.55,
        "avg_vkt_pa": 11_800,  # km per annum
        "fuel_l_per_100km": 8.9,
        "co2_g_per_km": 205,
        "nox_g_per_km": 0.25,
        "pm25_g_per_km": 0.005,
        "fuel_excise_per_l": 0.502,  # cents converted to $/L
        "registration_pa": 350,      # avg across states
        "share_peak": 0.38,          # share of VKT in peak periods
        "elasticity_price": -0.30,   # short-run demand elasticity to price
        "crash_cost_per_km": 0.035,  # external crash cost
    },
    "passenger_phev": {
        "label": "Passenger – PHEV",
        "count": 180_000,
        "avg_mass_t": 1.85,
        "avg_vkt_pa": 13_000,
        "fuel_l_per_100km": 3.5,
        "co2_g_per_km": 85,
        "nox_g_per_km": 0.10,
        "pm25_g_per_km": 0.003,
        "fuel_excise_per_l": 0.502,
        "registration_pa": 350,
        "share_peak": 0.38,
        "elasticity_price": -0.25,
        "crash_cost_per_km": 0.035,
    },
    "passenger_bev": {
        "label": "Passenger – BEV",
        "count": 320_000,
        "avg_mass_t": 1.95,
        "avg_vkt_pa": 13_500,
        "fuel_l_per_100km": 0.0,
        "co2_g_per_km": 0,  # tailpipe; grid emissions handled separately
        "nox_g_per_km": 0.0,
        "pm25_g_per_km": 0.002,  # tyre/brake PM still present
        "fuel_excise_per_l": 0.0,
        "registration_pa": 350,
        "share_peak": 0.40,
        "elasticity_price": -0.20,
        "crash_cost_per_km": 0.038,  # slightly heavier
    },
    "lcv_ice": {
        "label": "Light Commercial – ICE",
        "count": 3_900_000,
        "avg_mass_t": 2.2,
        "avg_vkt_pa": 15_500,
        "fuel_l_per_100km": 11.2,
        "co2_g_per_km": 260,
        "nox_g_per_km": 0.45,
        "pm25_g_per_km": 0.010,
        "fuel_excise_per_l": 0.502,
        "registration_pa": 450,
        "share_peak": 0.30,
        "elasticity_price": -0.15,
        "crash_cost_per_km": 0.042,
    },
    "lcv_bev": {
        "label": "Light Commercial – BEV",
        "count": 25_000,
        "avg_mass_t": 2.5,
        "avg_vkt_pa": 14_000,
        "fuel_l_per_100km": 0.0,
        "co2_g_per_km": 0,
        "nox_g_per_km": 0.0,
        "pm25_g_per_km": 0.003,
        "fuel_excise_per_l": 0.0,
        "registration_pa": 450,
        "share_peak": 0.30,
        "elasticity_price": -0.12,
        "crash_cost_per_km": 0.045,
    },
    "rigid_truck": {
        "label": "Rigid Truck",
        "count": 520_000,
        "avg_mass_t": 10.0,
        "avg_vkt_pa": 22_000,
        "fuel_l_per_100km": 22.0,
        "co2_g_per_km": 580,
        "nox_g_per_km": 3.5,
        "pm25_g_per_km": 0.06,
        "fuel_excise_per_l": 0.502,  # partial rebate via fuel tax credit
        "registration_pa": 1_800,
        "share_peak": 0.22,
        "elasticity_price": -0.10,
        "crash_cost_per_km": 0.12,
    },
    "artic_truck": {
        "label": "Articulated Truck",
        "count": 105_000,
        "avg_mass_t": 38.0,
        "avg_vkt_pa": 85_000,
        "fuel_l_per_100km": 52.0,
        "co2_g_per_km": 1_370,
        "nox_g_per_km": 8.0,
        "pm25_g_per_km": 0.12,
        "fuel_excise_per_l": 0.502,
        "registration_pa": 8_500,
        "share_peak": 0.15,
        "elasticity_price": -0.08,
        "crash_cost_per_km": 0.25,
    },
    "bus": {
        "label": "Bus",
        "count": 95_000,
        "avg_mass_t": 14.0,
        "avg_vkt_pa": 45_000,
        "fuel_l_per_100km": 35.0,
        "co2_g_per_km": 920,
        "nox_g_per_km": 5.0,
        "pm25_g_per_km": 0.08,
        "fuel_excise_per_l": 0.0,  # buses exempt via fuel tax credit
        "registration_pa": 2_500,
        "share_peak": 0.50,
        "elasticity_price": -0.05,
        "crash_cost_per_km": 0.06,  # lower per-km due to passengers carried
    },
    "motorcycle": {
        "label": "Motorcycle",
        "count": 870_000,
        "avg_mass_t": 0.22,
        "avg_vkt_pa": 4_500,
        "fuel_l_per_100km": 4.5,
        "co2_g_per_km": 105,
        "nox_g_per_km": 0.15,
        "pm25_g_per_km": 0.002,
        "fuel_excise_per_l": 0.502,
        "registration_pa": 200,
        "share_peak": 0.35,
        "elasticity_price": -0.35,
        "crash_cost_per_km": 0.08,
    },
}


# ---------------------------------------------------------------------------
# Fleet projection to 2030 (for scenario analysis)
# ---------------------------------------------------------------------------
FLEET_PROJECTION_2030 = {
    "passenger_ice": {"count_factor": 0.88, "note": "declining as EVs grow"},
    "passenger_phev": {"count_factor": 3.0, "note": "rapid adoption phase"},
    "passenger_bev": {"count_factor": 6.0, "note": "strong growth to ~1.9M"},
    "lcv_ice": {"count_factor": 0.92},
    "lcv_bev": {"count_factor": 8.0, "note": "from very low base"},
    "rigid_truck": {"count_factor": 1.05},
    "artic_truck": {"count_factor": 1.08},
    "bus": {"count_factor": 1.02},
    "motorcycle": {"count_factor": 1.0},
}


# ---------------------------------------------------------------------------
# Road network summary (stylised Australian network)
# ---------------------------------------------------------------------------
ROAD_NETWORK = {
    "urban_freeway": {
        "label": "Urban Freeway / Motorway",
        "total_lane_km": 8_200,
        "free_flow_speed_kmh": 100,
        "capacity_veh_per_lane_hr": 2_000,
        "lanes": 3.5,  # average across directions
        "share_national_vkt": 0.12,
        "maintenance_cost_per_lane_km_pa": 85_000,
        "congestion_profile": "high",
    },
    "urban_arterial": {
        "label": "Urban Arterial",
        "total_lane_km": 52_000,
        "free_flow_speed_kmh": 60,
        "capacity_veh_per_lane_hr": 900,
        "lanes": 2.0,
        "share_national_vkt": 0.32,
        "maintenance_cost_per_lane_km_pa": 45_000,
        "congestion_profile": "high",
    },
    "urban_local": {
        "label": "Urban Local Street",
        "total_lane_km": 280_000,
        "free_flow_speed_kmh": 50,
        "capacity_veh_per_lane_hr": 600,
        "lanes": 1.0,
        "share_national_vkt": 0.15,
        "maintenance_cost_per_lane_km_pa": 12_000,
        "congestion_profile": "low",
    },
    "rural_highway": {
        "label": "Rural Highway / National Highway",
        "total_lane_km": 42_000,
        "free_flow_speed_kmh": 110,
        "capacity_veh_per_lane_hr": 1_200,
        "lanes": 1.5,
        "share_national_vkt": 0.28,
        "maintenance_cost_per_lane_km_pa": 25_000,
        "congestion_profile": "none",
    },
    "rural_local": {
        "label": "Rural / Remote Local Road",
        "total_lane_km": 520_000,
        "free_flow_speed_kmh": 80,
        "capacity_veh_per_lane_hr": 800,
        "lanes": 1.0,
        "share_national_vkt": 0.13,
        "maintenance_cost_per_lane_km_pa": 6_000,
        "congestion_profile": "none",
    },
}


# ---------------------------------------------------------------------------
# Time-of-day demand profile (proportion of daily VKT by hour)
# Derived from VISTA / HTS journey-to-work and all-purpose trip data
# ---------------------------------------------------------------------------
HOURLY_DEMAND_PROFILE = np.array([
    # 00  01    02    03    04    05    06    07    08    09    10    11
    0.010, 0.006, 0.004, 0.004, 0.008, 0.020, 0.055, 0.090, 0.095, 0.065, 0.055, 0.055,
    # 12  13    14    15    16    17    18    19    20    21    22    23
    0.058, 0.055, 0.060, 0.075, 0.090, 0.088, 0.060, 0.040, 0.028, 0.020, 0.015, 0.012,
])
# Normalise to sum to 1
HOURLY_DEMAND_PROFILE = HOURLY_DEMAND_PROFILE / HOURLY_DEMAND_PROFILE.sum()

# Peak hours (7-9 AM, 4-6 PM)
PEAK_HOURS = [7, 8, 16, 17]
SHOULDER_HOURS = [6, 9, 10, 15, 18, 19]
OFF_PEAK_HOURS = [h for h in range(24) if h not in PEAK_HOURS + SHOULDER_HOURS]


# ---------------------------------------------------------------------------
# Externality cost parameters (AUD per unit, 2024)
# Sources: ATAP, BITRE, ExternE-Transport adapted to Australian conditions
# ---------------------------------------------------------------------------
EXTERNALITY_COSTS = {
    "co2_per_tonne": 75.0,       # social cost of carbon (conservative mid-range)
    "nox_per_kg": 12.50,         # health damage cost
    "pm25_per_kg": 340.0,        # mortality/morbidity cost (urban)
    "noise_per_vkt_urban": 0.008,  # average noise externality
    "noise_per_vkt_rural": 0.001,
    "congestion_vot_per_hour": 22.50,  # ATAP value of travel time (commute)
    "congestion_vot_freight_per_hour": 55.00,  # freight time value
}


# ---------------------------------------------------------------------------
# Current revenue baseline (approximation for calibration)
# Source: BITRE Information Sheet 109, state budgets
# ---------------------------------------------------------------------------
CURRENT_REVENUE = {
    "fuel_excise_total_bn": 11.8,
    "registration_total_bn": 8.2,
    "tolls_total_bn": 4.5,
    "stamp_duty_vehicles_bn": 3.8,
    "total_road_related_bn": 28.3,
    "total_road_expenditure_bn": 32.5,  # spending exceeds hypothecated revenue
    "fuel_excise_erosion_rate_pa": 0.04,  # 4% annual decline as fleet electrifies
}


# ---------------------------------------------------------------------------
# Congestion parameters
# ---------------------------------------------------------------------------
# BPR (Bureau of Public Roads) function parameters: t = t0 * (1 + alpha*(V/C)^beta)
BPR_ALPHA = 0.15
BPR_BETA = 4.0

# Total estimated annual congestion cost (BITRE / Infrastructure Australia)
CONGESTION_COST_TOTAL_BN = 19.0  # $19 billion in major capitals


# ---------------------------------------------------------------------------
# Pavement damage (AASHTO fourth-power law)
# ---------------------------------------------------------------------------
def pavement_damage_factor(mass_tonnes: float, reference_mass: float = 8.2) -> float:
    """
    Relative pavement damage using the fourth-power rule.
    Reference is a standard axle load equivalent (~8.2t single axle).
    """
    return (mass_tonnes / reference_mass) ** 4


# ---------------------------------------------------------------------------
# Helper: total national VKT
# ---------------------------------------------------------------------------
def total_national_vkt() -> float:
    """Total annual vehicle-km travelled across the fleet."""
    return sum(v["count"] * v["avg_vkt_pa"] for v in FLEET.values())


def fuel_excise_revenue() -> float:
    """Approximate annual fuel excise revenue from the fleet."""
    total = 0.0
    for v in FLEET.values():
        litres_pa = v["count"] * v["avg_vkt_pa"] * v["fuel_l_per_100km"] / 100
        total += litres_pa * v["fuel_excise_per_l"]
    return total


def registration_revenue() -> float:
    """Approximate annual registration revenue."""
    return sum(v["count"] * v["registration_pa"] for v in FLEET.values())
