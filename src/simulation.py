"""
Simulation engine for road pricing scenarios.

Generates representative trips from the Australian fleet/network data,
applies each pricing regime, models demand response (elasticity), and
computes outcome metrics for comparison.

The simulation uses a stratified sampling approach: for each combination of
vehicle type × road type × hour of day, it calculates a representative
trip and weights it by the volume of such trips in the real network.
"""

import numpy as np
import pandas as pd

from .australian_data import (
    FLEET, FLEET_PROJECTION_2030, ROAD_NETWORK,
    HOURLY_DEMAND_PROFILE, PEAK_HOURS, SHOULDER_HOURS,
    EXTERNALITY_COSTS, BPR_ALPHA, BPR_BETA,
    total_national_vkt,
)
from .pricing_regimes import Trip, ALL_REGIMES


# ---------------------------------------------------------------------------
# Average trip distance by road type (km) — derived from survey data
# ---------------------------------------------------------------------------
AVG_TRIP_DISTANCE = {
    "urban_freeway": 18.0,
    "urban_arterial": 8.5,
    "urban_local": 3.5,
    "rural_highway": 65.0,
    "rural_local": 22.0,
}


def _is_urban(road_type: str) -> bool:
    return road_type.startswith("urban")


def _volume_capacity_ratio(road_type: str, hour: int) -> float:
    """
    Estimate V/C ratio for a road type at a given hour.
    Uses the demand profile and congestion characteristics.
    """
    road = ROAD_NETWORK[road_type]
    profile = road["congestion_profile"]
    demand_share = HOURLY_DEMAND_PROFILE[hour]

    if profile == "none":
        return 0.3  # rural roads rarely congested

    # Scale demand share to V/C — calibrated so peak urban arterials hit ~0.95
    if profile == "high":
        base_vc = 0.45
        peak_demand = max(HOURLY_DEMAND_PROFILE[h] for h in PEAK_HOURS)
        vc = base_vc + 0.55 * (demand_share / peak_demand)
    else:  # low
        base_vc = 0.25
        peak_demand = max(HOURLY_DEMAND_PROFILE[h] for h in PEAK_HOURS)
        vc = base_vc + 0.30 * (demand_share / peak_demand)

    return min(vc, 1.3)


def _congestion_delay_factor(vc_ratio: float) -> float:
    """BPR delay function: ratio of actual to free-flow travel time."""
    return 1.0 + BPR_ALPHA * (vc_ratio ** BPR_BETA)


def _compute_trip_weight(veh_key: str, road_type: str, hour: int) -> float:
    """
    Weight of this vehicle×road×hour cell in total national VKT.
    """
    veh = FLEET[veh_key]
    road = ROAD_NETWORK[road_type]
    annual_vkt = veh["count"] * veh["avg_vkt_pa"]
    road_share = road["share_national_vkt"]
    hour_share = HOURLY_DEMAND_PROFILE[hour]
    return annual_vkt * road_share * hour_share


def run_simulation(
    regimes=None,
    fleet_year: str = "2026",
    include_demand_response: bool = True,
) -> pd.DataFrame:
    """
    Run the full simulation across all vehicle×road×hour combinations
    for each pricing regime.

    Returns a DataFrame with one row per regime, containing aggregated
    outcome metrics.
    """
    if regimes is None:
        regimes = ALL_REGIMES

    # Select fleet data
    if fleet_year == "2030":
        fleet_data = {}
        for k, v in FLEET.items():
            fleet_data[k] = dict(v)
            proj = FLEET_PROJECTION_2030.get(k, {})
            fleet_data[k]["count"] = int(v["count"] * proj.get("count_factor", 1.0))
    else:
        fleet_data = FLEET

    results = []

    for regime in regimes:
        total_revenue = 0.0
        total_vkt = 0.0
        total_vkt_post = 0.0
        total_co2_kg = 0.0
        total_congestion_cost = 0.0
        total_externality_cost = 0.0
        total_charge_cost = 0.0

        # Per-vehicle-class accumulators
        class_revenue = {}
        class_vkt = {}
        class_charge_per_km = {}

        # Distributional: urban vs rural
        urban_revenue = 0.0
        rural_revenue = 0.0
        urban_vkt = 0.0
        rural_vkt = 0.0

        # Peak vs off-peak
        peak_revenue = 0.0
        offpeak_revenue = 0.0

        for veh_key, veh in fleet_data.items():
            class_revenue[veh_key] = 0.0
            class_vkt[veh_key] = 0.0
            class_charge_per_km[veh_key] = []

            for road_type in ROAD_NETWORK:
                for hour in range(24):
                    weight = _compute_trip_weight(veh_key, road_type, hour)
                    if weight < 1e-6:
                        continue

                    is_urban = _is_urban(road_type)
                    vc_ratio = _volume_capacity_ratio(road_type, hour)

                    trip = Trip(
                        vehicle_type=veh_key,
                        distance_km=AVG_TRIP_DISTANCE[road_type],
                        road_type=road_type,
                        hour_of_day=hour,
                        mass_tonnes=veh["avg_mass_t"],
                        is_urban=is_urban,
                        volume_capacity_ratio=vc_ratio,
                    )

                    charge_km = regime.charge_per_km(trip, fleet_data)

                    # Demand response: apply price elasticity
                    if include_demand_response:
                        # Change in cost relative to status quo benchmark
                        sq_charge = ALL_REGIMES[0].charge_per_km(trip, fleet_data)
                        price_change_pct = (
                            (charge_km - sq_charge) / max(sq_charge, 0.001)
                        )
                        elasticity = veh["elasticity_price"]
                        demand_factor = max(
                            0.5,
                            min(1.5, 1.0 + elasticity * price_change_pct)
                        )
                    else:
                        demand_factor = 1.0

                    adjusted_weight = weight * demand_factor

                    # Revenue
                    km_revenue = charge_km * adjusted_weight
                    total_revenue += km_revenue
                    total_vkt += weight
                    total_vkt_post += adjusted_weight

                    # Emissions
                    total_co2_kg += veh["co2_g_per_km"] / 1000 * adjusted_weight

                    # Congestion cost (delay × value of time)
                    delay_factor = _congestion_delay_factor(vc_ratio)
                    if is_urban:
                        # Extra delay hours per km
                        speed = ROAD_NETWORK[road_type]["free_flow_speed_kmh"]
                        free_flow_time_hr = 1.0 / speed
                        actual_time_hr = free_flow_time_hr * delay_factor
                        delay_hr = actual_time_hr - free_flow_time_hr
                        cong_cost = (
                            delay_hr
                            * EXTERNALITY_COSTS["congestion_vot_per_hour"]
                            * adjusted_weight
                        )
                        total_congestion_cost += cong_cost

                    # Full externality cost
                    ext_co2 = (veh["co2_g_per_km"] / 1e6
                               * EXTERNALITY_COSTS["co2_per_tonne"]
                               * adjusted_weight)
                    ext_nox = (veh["nox_g_per_km"] / 1e3
                               * EXTERNALITY_COSTS["nox_per_kg"]
                               * adjusted_weight)
                    ext_pm = (veh["pm25_g_per_km"] / 1e3
                              * EXTERNALITY_COSTS["pm25_per_kg"]
                              * adjusted_weight)
                    ext_crash = veh["crash_cost_per_km"] * adjusted_weight
                    ext_noise = (
                        EXTERNALITY_COSTS["noise_per_vkt_urban"] if is_urban
                        else EXTERNALITY_COSTS["noise_per_vkt_rural"]
                    ) * adjusted_weight
                    total_externality_cost += (
                        ext_co2 + ext_nox + ext_pm + ext_crash + ext_noise
                    )

                    total_charge_cost += charge_km * adjusted_weight

                    # Per-class
                    class_revenue[veh_key] += km_revenue
                    class_vkt[veh_key] += adjusted_weight
                    class_charge_per_km[veh_key].append(charge_km)

                    # Urban/rural split
                    if is_urban:
                        urban_revenue += km_revenue
                        urban_vkt += adjusted_weight
                    else:
                        rural_revenue += km_revenue
                        rural_vkt += adjusted_weight

                    # Peak/off-peak
                    if hour in PEAK_HOURS:
                        peak_revenue += km_revenue
                    else:
                        offpeak_revenue += km_revenue

        # Compute average charge per km by vehicle class
        avg_charge_by_class = {}
        for k in class_charge_per_km:
            charges = class_charge_per_km[k]
            avg_charge_by_class[k] = np.mean(charges) if charges else 0.0

        # Passenger car equivalent average charge
        passenger_types = ["passenger_ice", "passenger_phev", "passenger_bev"]
        passenger_vkt = sum(class_vkt.get(t, 0) for t in passenger_types)
        passenger_rev = sum(class_revenue.get(t, 0) for t in passenger_types)
        avg_passenger_charge = (
            passenger_rev / passenger_vkt if passenger_vkt > 0 else 0
        )

        # Heavy vehicle average charge
        hv_types = ["rigid_truck", "artic_truck"]
        hv_vkt = sum(class_vkt.get(t, 0) for t in hv_types)
        hv_rev = sum(class_revenue.get(t, 0) for t in hv_types)
        avg_hv_charge = hv_rev / hv_vkt if hv_vkt > 0 else 0

        results.append({
            "regime": regime.short_name,
            "regime_full": regime.name,
            "revenue_bn": total_revenue / 1e9,
            "vkt_bn": total_vkt / 1e9,
            "vkt_post_bn": total_vkt_post / 1e9,
            "vkt_change_pct": (total_vkt_post - total_vkt) / total_vkt * 100,
            "co2_mt": total_co2_kg / 1e9,  # megatonnes
            "congestion_cost_bn": total_congestion_cost / 1e9,
            "externality_cost_bn": total_externality_cost / 1e9,
            "avg_passenger_charge_per_km": avg_passenger_charge,
            "avg_hv_charge_per_km": avg_hv_charge,
            "urban_revenue_share": urban_revenue / max(total_revenue, 1) * 100,
            "rural_revenue_share": rural_revenue / max(total_revenue, 1) * 100,
            "peak_revenue_share": peak_revenue / max(total_revenue, 1) * 100,
            "avg_charge_by_class": avg_charge_by_class,
            "class_revenue": class_revenue,
            "class_vkt": class_vkt,
            "urban_revenue_bn": urban_revenue / 1e9,
            "rural_revenue_bn": rural_revenue / 1e9,
        })

    return pd.DataFrame(results)


def run_sensitivity(
    parameter_name: str,
    values: list,
    regime_class,
    regime_kwargs: dict,
    param_kwarg_key: str,
) -> pd.DataFrame:
    """
    Run sensitivity analysis: vary one parameter across a range of values
    and return outcomes for a single regime.
    """
    rows = []
    for val in values:
        kwargs = dict(regime_kwargs)
        kwargs[param_kwarg_key] = val
        regime = regime_class(**kwargs)
        df = run_simulation(regimes=[regime], include_demand_response=True)
        row = df.iloc[0].to_dict()
        row["param_value"] = val
        row["param_name"] = parameter_name
        rows.append(row)
    return pd.DataFrame(rows)
