"""
Road pricing regime implementations.

Each regime is a class that, given a trip description, returns the charge.
This allows the simulation engine to apply any regime uniformly across
the fleet and network.

Design note: regimes are deliberately kept as pure functions of trip
attributes so they can be compared on a level playing field.
"""

from dataclasses import dataclass


@dataclass
class Trip:
    """Describes a single representative trip for pricing purposes."""
    vehicle_type: str          # key into FLEET dict
    distance_km: float
    road_type: str             # key into ROAD_NETWORK dict
    hour_of_day: int           # 0-23
    mass_tonnes: float         # gross vehicle mass
    is_urban: bool
    volume_capacity_ratio: float  # V/C ratio on the link (0.0 - 1.5+)


class StatusQuo:
    """
    Current Australian system: fuel excise + flat registration + selective tolls.

    Theory: Cost-recovery (crude proxy via fuel tax).
    Strengths: Simple, low admin cost, somewhat proportional to use.
    Weaknesses: Eroding revenue base as EVs grow; no congestion signal;
                heavy vehicles under-charged relative to road damage.
    """
    name = "Status Quo (Fuel Excise + Registration)"
    short_name = "Status Quo"

    def charge_per_km(self, trip: Trip, fleet_data: dict) -> float:
        veh = fleet_data[trip.vehicle_type]
        # Fuel excise component
        fuel_charge = veh["fuel_l_per_100km"] / 100 * veh["fuel_excise_per_l"]
        # Annualised registration per km
        reg_per_km = veh["registration_pa"] / max(veh["avg_vkt_pa"], 1)
        # Existing tolls (stylised: urban freeways only, ~$0.30/km avg)
        toll = 0.30 if trip.road_type == "urban_freeway" else 0.0
        return fuel_charge + reg_per_km + toll


class FlatDistanceBased:
    """
    Flat per-kilometre charge, same rate for all vehicles and times.

    Theory: Second-best approximation of user-pays.
    Strengths: Simple, technology-neutral (EVs pay same as ICE), easy to
               understand and administer.
    Weaknesses: No congestion signal, no externality differentiation,
                regressive for rural/outer-suburban drivers with long commutes.
    """
    name = "Flat Distance-Based Charge"
    short_name = "Flat Distance"

    def __init__(self, rate_per_km: float = 0.025):
        self.rate_per_km = rate_per_km

    def charge_per_km(self, trip: Trip, fleet_data: dict) -> float:
        return self.rate_per_km


class TimeOfDayCongestion:
    """
    Distance charge that varies by time of day and congestion level.

    Theory: Vickrey congestion pricing + Pigouvian externality correction.
    Strengths: Directly targets congestion externality, sends efficient
               price signals, can reduce peak demand 15-25%.
    Weaknesses: Complex, requires monitoring infrastructure, distributional
                concerns (shift workers, parents with school drop-off).
    """
    name = "Time-of-Day Congestion Charge"
    short_name = "Congestion"

    def __init__(self, base_rate: float = 0.015,
                 peak_multiplier: float = 4.0,
                 shoulder_multiplier: float = 2.0):
        self.base_rate = base_rate
        self.peak_multiplier = peak_multiplier
        self.shoulder_multiplier = shoulder_multiplier
        self.peak_hours = {7, 8, 16, 17}
        self.shoulder_hours = {6, 9, 10, 15, 18, 19}

    def charge_per_km(self, trip: Trip, fleet_data: dict) -> float:
        if trip.hour_of_day in self.peak_hours and trip.is_urban:
            multiplier = self.peak_multiplier
        elif trip.hour_of_day in self.shoulder_hours and trip.is_urban:
            multiplier = self.shoulder_multiplier
        else:
            multiplier = 1.0
        # Scale further by actual congestion level
        congestion_factor = 1.0 + max(0, trip.volume_capacity_ratio - 0.7) * 2.0
        return self.base_rate * multiplier * congestion_factor


class CordonCharge:
    """
    Fixed charge for entering a defined urban zone (CBD cordon).

    Theory: Second-best pricing (Vickrey); empirically proven in London,
            Stockholm, Singapore.
    Strengths: Simple to implement (cameras at entry points), clear signal,
               effective at reducing CBD traffic.
    Weaknesses: Boundary effects (traffic diverts around cordon), doesn't
                price distance within or outside the zone, limited geographic
                scope, can disadvantage inner-city residents.
    """
    name = "CBD Cordon Charge"
    short_name = "Cordon"

    def __init__(self, cordon_charge: float = 8.0,
                 applies_peak_only: bool = True):
        self.cordon_charge = cordon_charge
        self.applies_peak_only = applies_peak_only
        self.peak_hours = set(range(6, 19))  # 6 AM to 7 PM

    def charge_per_km(self, trip: Trip, fleet_data: dict) -> float:
        # Cordon only applies to urban trips; amortise over avg trip distance
        if not trip.is_urban:
            return 0.0
        if self.applies_peak_only and trip.hour_of_day not in self.peak_hours:
            return 0.0
        # Only ~20% of urban trips cross CBD cordon
        cordon_probability = 0.20 if trip.road_type in (
            "urban_freeway", "urban_arterial") else 0.05
        avg_trip_km = 12.0  # average urban trip length
        return self.cordon_charge * cordon_probability / avg_trip_km


class WeightDistance:
    """
    Charge per km scaled by vehicle mass (using fourth-power pavement damage).

    Theory: Cost-recovery / user-pays (AASHTO fourth-power law);
            Henry Tax Review recommendation.
    Strengths: Directly links charge to road damage caused, fair across
               vehicle classes, technology-neutral.
    Weaknesses: Politically difficult for freight industry, needs mass
                verification, could increase consumer prices.
    """
    name = "Weight-Distance Charge"
    short_name = "Weight-Distance"

    def __init__(self, base_rate: float = 0.02, reference_mass_t: float = 1.5):
        self.base_rate = base_rate
        self.reference_mass_t = reference_mass_t

    def charge_per_km(self, trip: Trip, fleet_data: dict) -> float:
        # Fourth-power damage scaling (capped for practical purposes)
        damage_ratio = (trip.mass_tonnes / self.reference_mass_t) ** 2
        # Using square rather than fourth power for practical charge design
        # (full fourth power would make truck charges politically infeasible)
        # but still creates strong differentiation
        return self.base_rate * min(damage_ratio, 500.0)


class ExternalityWeighted:
    """
    Charge that reflects full marginal external costs: congestion +
    emissions + crash risk + noise.

    Theory: First-best Pigouvian pricing — charge equals marginal external cost.
    Strengths: Economically optimal, incentivises efficient behaviour across
               all externality dimensions.
    Weaknesses: Extremely complex, requires real-time data on emissions and
                congestion, charges can be very high at peak times creating
                political opposition, high administrative cost.
    """
    name = "Full Externality-Weighted Charge"
    short_name = "Externality"

    def __init__(self, co2_price_per_t: float = 75.0,
                 congestion_vot: float = 22.50):
        self.co2_price_per_t = co2_price_per_t
        self.congestion_vot = congestion_vot

    def charge_per_km(self, trip: Trip, fleet_data: dict) -> float:
        veh = fleet_data[trip.vehicle_type]

        # Emissions cost
        co2_cost = veh["co2_g_per_km"] / 1_000_000 * self.co2_price_per_t
        nox_cost = veh["nox_g_per_km"] / 1_000 * 12.50
        pm_cost = veh["pm25_g_per_km"] / 1_000 * 340.0
        emission_cost = co2_cost + nox_cost + pm_cost

        # Congestion cost (marginal delay imposed on others)
        if trip.is_urban and trip.volume_capacity_ratio > 0.5:
            # Derivative of BPR delay function w.r.t. volume
            vc = trip.volume_capacity_ratio
            marginal_delay_hrs = 0.15 * 4 * (vc ** 3) / 60  # per km, in hours
            congestion_cost = marginal_delay_hrs * self.congestion_vot * 15
            # 15 = approximate number of other vehicles affected per marginal vehicle
        else:
            congestion_cost = 0.0

        # Crash externality
        crash_cost = veh["crash_cost_per_km"]

        # Noise
        noise_cost = 0.008 if trip.is_urban else 0.001

        return emission_cost + congestion_cost + crash_cost + noise_cost


class HybridReformPackage:
    """
    Pragmatic reform: distance charge + congestion top-up + weight adjustment.
    Replaces fuel excise and registration.

    Theory: Second-best pricing informed by all theories — balances efficiency,
            equity, revenue adequacy, and political feasibility.
    Strengths: Captures most welfare gains of first-best pricing while being
               implementable, technology-neutral, provides stable revenue base.
    Weaknesses: More complex than status quo, requires GNSS/odometer tech,
                transition challenges.
    """
    name = "Hybrid Reform Package"
    short_name = "Hybrid"

    def __init__(self, base_rate: float = 0.025,
                 peak_surcharge: float = 0.04,
                 weight_factor_per_tonne: float = 0.003):
        self.base_rate = base_rate
        self.peak_surcharge = peak_surcharge
        self.weight_factor_per_tonne = weight_factor_per_tonne
        self.peak_hours = {7, 8, 16, 17}

    def charge_per_km(self, trip: Trip, fleet_data: dict) -> float:
        # Base distance charge
        charge = self.base_rate

        # Peak congestion surcharge (urban only)
        if trip.hour_of_day in self.peak_hours and trip.is_urban:
            charge += self.peak_surcharge

        # Weight adjustment (modest, reflecting road wear)
        if trip.mass_tonnes > 3.5:
            charge += self.weight_factor_per_tonne * trip.mass_tonnes

        return charge


# Registry of all regimes for the simulation
ALL_REGIMES = [
    StatusQuo(),
    FlatDistanceBased(rate_per_km=0.025),
    TimeOfDayCongestion(base_rate=0.015, peak_multiplier=4.0),
    CordonCharge(cordon_charge=8.0),
    WeightDistance(base_rate=0.02),
    ExternalityWeighted(co2_price_per_t=75.0),
    HybridReformPackage(base_rate=0.025, peak_surcharge=0.04),
]
