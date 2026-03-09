"""
Visualisation module for road pricing simulation results.

Generates a suite of charts that tell the story of trade-offs across
pricing regimes, making the analysis compelling and accessible.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from .australian_data import FLEET

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Consistent colour palette for regimes
REGIME_COLORS = {
    "Status Quo": "#7f8c8d",
    "Flat Distance": "#3498db",
    "Congestion": "#e74c3c",
    "Cordon": "#9b59b6",
    "Weight-Distance": "#e67e22",
    "Externality": "#2ecc71",
    "Hybrid": "#1abc9c",
}


def _save(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _regime_color(name):
    return REGIME_COLORS.get(name, "#34495e")


def plot_revenue_comparison(df: pd.DataFrame) -> str:
    """Bar chart comparing annual revenue by regime."""
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = [_regime_color(r) for r in df["regime"]]
    bars = ax.bar(df["regime"], df["revenue_bn"], color=colors, edgecolor="white",
                  linewidth=0.5)

    # Add value labels
    for bar, val in zip(bars, df["revenue_bn"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"${val:.1f}B", ha="center", va="bottom", fontsize=10,
                fontweight="bold")

    # Reference lines
    ax.axhline(y=28.3, color="#e74c3c", linestyle="--", alpha=0.7, linewidth=1.5)
    ax.text(len(df) - 0.5, 28.8, "Current road revenue ($28.3B)",
            ha="right", fontsize=9, color="#e74c3c")
    ax.axhline(y=32.5, color="#e67e22", linestyle=":", alpha=0.6, linewidth=1.5)
    ax.text(len(df) - 0.5, 33.0, "Road expenditure ($32.5B)",
            ha="right", fontsize=9, color="#e67e22")

    ax.set_ylabel("Annual Revenue ($ Billion)", fontsize=12)
    ax.set_title("Revenue Generation by Pricing Regime", fontsize=14,
                 fontweight="bold", pad=15)
    ax.set_ylim(0, max(df["revenue_bn"].max() * 1.25, 40))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0fB"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.xticks(rotation=25, ha="right")
    fig.tight_layout()
    return _save(fig, "01_revenue_comparison.png")


def plot_trade_off_scatter(df: pd.DataFrame) -> str:
    """
    Scatter plot: Revenue vs Congestion Reduction — the core trade-off.
    Bubble size = externality cost reduction.
    """
    fig, ax = plt.subplots(figsize=(11, 8))

    sq_congestion = df.loc[df["regime"] == "Status Quo",
                           "congestion_cost_bn"].values[0]
    sq_ext = df.loc[df["regime"] == "Status Quo",
                    "externality_cost_bn"].values[0]

    for _, row in df.iterrows():
        cong_reduction = (sq_congestion - row["congestion_cost_bn"]) / sq_congestion * 100
        ext_reduction = (sq_ext - row["externality_cost_bn"]) / sq_ext * 100
        size = max(abs(ext_reduction) * 30, 80)
        color = _regime_color(row["regime"])

        ax.scatter(row["revenue_bn"], cong_reduction, s=size, c=color,
                   alpha=0.8, edgecolors="white", linewidth=1.5, zorder=5)
        ax.annotate(row["regime"],
                    (row["revenue_bn"], cong_reduction),
                    textcoords="offset points", xytext=(10, 8),
                    fontsize=10, fontweight="bold", color=color)

    ax.axhline(y=0, color="gray", linestyle="-", alpha=0.3)
    ax.axvline(x=28.3, color="#e74c3c", linestyle="--", alpha=0.5)
    ax.text(28.5, ax.get_ylim()[0] + 1, "Current\nrevenue",
            fontsize=8, color="#e74c3c")

    ax.set_xlabel("Annual Revenue ($ Billion)", fontsize=12)
    ax.set_ylabel("Congestion Cost Reduction (%)", fontsize=12)
    ax.set_title(
        "The Core Trade-Off: Revenue vs Congestion Relief",
        fontsize=14, fontweight="bold", pad=15
    )
    ax.text(0.02, 0.02,
            "Bubble size reflects total externality cost reduction",
            transform=ax.transAxes, fontsize=9, color="gray", style="italic")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, "02_tradeoff_scatter.png")


def plot_distributional_impact(df: pd.DataFrame) -> str:
    """Stacked bar: urban vs rural revenue burden."""
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(df))
    width = 0.6

    urban = df["urban_revenue_bn"].values
    rural = df["rural_revenue_bn"].values

    ax.bar(x, urban, width, label="Urban", color="#3498db", alpha=0.85)
    ax.bar(x, rural, width, bottom=urban, label="Rural", color="#e67e22",
           alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(df["regime"], rotation=25, ha="right")
    ax.set_ylabel("Revenue Burden ($ Billion)", fontsize=12)
    ax.set_title(
        "Who Pays? Urban vs Rural Revenue Distribution",
        fontsize=14, fontweight="bold", pad=15
    )
    ax.legend(fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, "03_distributional_urban_rural.png")


def plot_vehicle_class_charges(df: pd.DataFrame) -> str:
    """Grouped bar chart: average charge per km by vehicle class and regime."""
    fig, ax = plt.subplots(figsize=(14, 7))

    display_classes = [
        ("passenger_ice", "Car (ICE)"),
        ("passenger_bev", "Car (BEV)"),
        ("lcv_ice", "Light Comm."),
        ("rigid_truck", "Rigid Truck"),
        ("artic_truck", "Artic. Truck"),
    ]

    n_regimes = len(df)
    n_classes = len(display_classes)
    x = np.arange(n_classes)
    width = 0.8 / n_regimes

    for i, (_, row) in enumerate(df.iterrows()):
        charges = [row["avg_charge_by_class"].get(cls, 0) for cls, _ in display_classes]
        offset = (i - n_regimes / 2 + 0.5) * width
        color = _regime_color(row["regime"])
        ax.bar(x + offset, charges, width, label=row["regime"],
               color=color, alpha=0.85, edgecolor="white", linewidth=0.3)

    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label in display_classes], fontsize=11)
    ax.set_ylabel("Average Charge ($/km)", fontsize=12)
    ax.set_title(
        "Who Bears the Cost? Charges by Vehicle Class",
        fontsize=14, fontweight="bold", pad=15
    )
    ax.legend(fontsize=8, ncol=4, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, "04_vehicle_class_charges.png")


def plot_emissions_reduction(df: pd.DataFrame) -> str:
    """Bar chart: CO2 emissions under each regime."""
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = [_regime_color(r) for r in df["regime"]]
    bars = ax.bar(df["regime"], df["co2_mt"], color=colors, edgecolor="white",
                  linewidth=0.5)

    for bar, val in zip(bars, df["co2_mt"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                f"{val:.1f} Mt", ha="center", va="bottom", fontsize=10)

    ax.set_ylabel("Annual CO\u2082 Emissions (Megatonnes)", fontsize=12)
    ax.set_title(
        "Emissions Outcomes: Can Pricing Drive Decarbonisation?",
        fontsize=14, fontweight="bold", pad=15
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.xticks(rotation=25, ha="right")
    fig.tight_layout()
    return _save(fig, "05_emissions_reduction.png")


def plot_demand_response(df: pd.DataFrame) -> str:
    """Bar chart: VKT change (%) under each regime."""
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = [_regime_color(r) for r in df["regime"]]
    bars = ax.barh(df["regime"], df["vkt_change_pct"], color=colors,
                   edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, df["vkt_change_pct"]):
        x_pos = bar.get_width() + (0.3 if val >= 0 else -0.3)
        ha = "left" if val >= 0 else "right"
        ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
                f"{val:+.1f}%", ha=ha, va="center", fontsize=10,
                fontweight="bold")

    ax.axvline(x=0, color="gray", linestyle="-", linewidth=0.8)
    ax.set_xlabel("Change in Vehicle-km Travelled (%)", fontsize=12)
    ax.set_title(
        "Demand Response: How Much Does Driving Change?",
        fontsize=14, fontweight="bold", pad=15
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, "06_demand_response.png")


def plot_scorecard(df: pd.DataFrame) -> str:
    """
    Radar / summary scorecard comparing regimes across multiple dimensions.
    Uses a normalised 0-5 scoring approach.
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    dimensions = [
        "Revenue\nAdequacy",
        "Congestion\nReduction",
        "Emissions\nReduction",
        "Equity\n(Low Regressive)",
        "Simplicity",
        "Political\nFeasibility",
    ]

    sq = df.loc[df["regime"] == "Status Quo"].iloc[0]

    scores = {}
    for _, row in df.iterrows():
        name = row["regime"]
        # Revenue adequacy: how close to $32.5B target
        rev_score = min(5, row["revenue_bn"] / 32.5 * 5)

        # Congestion reduction
        cong_red = (sq["congestion_cost_bn"] - row["congestion_cost_bn"]) / sq["congestion_cost_bn"]
        cong_score = min(5, max(0, cong_red * 25 + 2.5))

        # Emissions reduction
        em_red = (sq["co2_mt"] - row["co2_mt"]) / sq["co2_mt"]
        em_score = min(5, max(0, em_red * 30 + 2.5))

        # Equity (inverse of rural burden relative to urban)
        rural_share = row["rural_revenue_share"]
        # Lower rural share = more equitable (rural has fewer alternatives)
        equity_score = max(0, 5 - rural_share / 10)

        # Simplicity (manual scoring based on regime complexity)
        simplicity_map = {
            "Status Quo": 4.5, "Flat Distance": 4.0, "Congestion": 2.0,
            "Cordon": 3.5, "Weight-Distance": 3.0, "Externality": 1.0,
            "Hybrid": 2.5,
        }
        simp_score = simplicity_map.get(name, 2.5)

        # Political feasibility (correlated with simplicity + familiarity)
        feasibility_map = {
            "Status Quo": 5.0, "Flat Distance": 3.0, "Congestion": 2.0,
            "Cordon": 3.0, "Weight-Distance": 2.5, "Externality": 1.0,
            "Hybrid": 2.5,
        }
        feas_score = feasibility_map.get(name, 2.5)

        scores[name] = [rev_score, cong_score, em_score,
                        equity_score, simp_score, feas_score]

    # Plot as grouped horizontal bars
    n_dim = len(dimensions)
    n_regimes = len(scores)
    y = np.arange(n_dim)
    height = 0.8 / n_regimes

    for i, (name, vals) in enumerate(scores.items()):
        offset = (i - n_regimes / 2 + 0.5) * height
        color = _regime_color(name)
        ax.barh(y + offset, vals, height, label=name, color=color, alpha=0.85,
                edgecolor="white", linewidth=0.3)

    ax.set_yticks(y)
    ax.set_yticklabels(dimensions, fontsize=11)
    ax.set_xlim(0, 5.5)
    ax.set_xlabel("Score (0-5)", fontsize=12)
    ax.set_title(
        "Multi-Dimensional Scorecard: No Single Regime Dominates",
        fontsize=14, fontweight="bold", pad=15
    )
    ax.legend(fontsize=8, ncol=4, loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _save(fig, "07_scorecard.png")


def plot_fuel_excise_erosion() -> str:
    """
    Time series showing fuel excise revenue erosion as fleet electrifies.
    Makes the case for why reform is needed.
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    years = np.arange(2024, 2041)
    base_excise = 11.8  # $B in 2024

    # Scenario 1: Business as usual erosion
    bau_erosion = base_excise * (1 - 0.04) ** (years - 2024)

    # Scenario 2: Accelerated EV adoption
    fast_ev_erosion = base_excise * (1 - 0.07) ** (years - 2024)

    # Road maintenance needs (growing ~2% pa)
    road_needs = 32.5 * (1.02) ** (years - 2024)

    ax.plot(years, bau_erosion, "o-", color="#3498db", linewidth=2.5,
            markersize=4, label="Fuel excise (base case: 4% pa decline)")
    ax.plot(years, fast_ev_erosion, "s--", color="#e74c3c", linewidth=2.5,
            markersize=4, label="Fuel excise (fast EV uptake: 7% pa decline)")
    ax.plot(years, road_needs, "^:", color="#e67e22", linewidth=2.5,
            markersize=4, label="Road expenditure needs (2% pa growth)")

    ax.fill_between(years, fast_ev_erosion, road_needs, alpha=0.1,
                    color="#e74c3c")
    ax.annotate("Growing\nfunding gap",
                xy=(2034, (fast_ev_erosion[10] + road_needs[10]) / 2),
                fontsize=11, fontweight="bold", color="#c0392b",
                ha="center")

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("$ Billion", fontsize=12)
    ax.set_title(
        "The Looming Fiscal Cliff: Fuel Excise Revenue Erosion",
        fontsize=14, fontweight="bold", pad=15
    )
    ax.legend(fontsize=10, loc="center right")
    ax.set_xlim(2024, 2040)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0fB"))
    fig.tight_layout()
    return _save(fig, "00_fuel_excise_erosion.png")


def plot_ev_fairness(df: pd.DataFrame) -> str:
    """Bar chart showing ICE vs BEV charges — the fairness question."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for idx, (vtype_a, vtype_b, title) in enumerate([
        ("passenger_ice", "passenger_bev", "Passenger Cars: ICE vs BEV"),
        ("lcv_ice", "lcv_bev", "Light Commercial: ICE vs BEV"),
    ]):
        ax = axes[idx]
        ice_charges = [row["avg_charge_by_class"].get(vtype_a, 0)
                       for _, row in df.iterrows()]
        bev_charges = [row["avg_charge_by_class"].get(vtype_b, 0)
                       for _, row in df.iterrows()]

        x = np.arange(len(df))
        width = 0.35

        ax.bar(x - width / 2, ice_charges, width, label="ICE",
               color="#e74c3c", alpha=0.8)
        ax.bar(x + width / 2, bev_charges, width, label="BEV",
               color="#2ecc71", alpha=0.8)

        ax.set_xticks(x)
        ax.set_xticklabels(df["regime"], rotation=35, ha="right", fontsize=8)
        ax.set_ylabel("Avg Charge ($/km)", fontsize=10)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.legend(fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.suptitle(
        "Technology Neutrality: Do EVs Pay Their Fair Share?",
        fontsize=14, fontweight="bold", y=1.02
    )
    fig.tight_layout()
    return _save(fig, "08_ev_fairness.png")


def generate_all_charts(df: pd.DataFrame) -> list[str]:
    """Generate all visualisations and return list of file paths."""
    paths = []
    paths.append(plot_fuel_excise_erosion())
    paths.append(plot_revenue_comparison(df))
    paths.append(plot_trade_off_scatter(df))
    paths.append(plot_distributional_impact(df))
    paths.append(plot_vehicle_class_charges(df))
    paths.append(plot_emissions_reduction(df))
    paths.append(plot_demand_response(df))
    paths.append(plot_scorecard(df))
    paths.append(plot_ev_fairness(df))
    return paths
