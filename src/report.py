"""
Report generator — produces a narrative analysis of simulation results.

Designed to be compelling, balanced, and informative without pushing
a single recommendation. Presents trade-offs transparently.
"""

import pandas as pd
from .theory import THEORIES, format_theory_summary


def generate_report(df: pd.DataFrame, fleet_year: str = "2026") -> str:
    """Generate the full narrative report as a string."""
    sq = df.loc[df["regime"] == "Status Quo"].iloc[0]

    sections = []

    # ── Title ──
    sections.append("=" * 74)
    sections.append("  AUSTRALIAN ROAD PRICING: A SIMULATION OF ALTERNATIVE FUTURES")
    sections.append(f"  Fleet year: {fleet_year}  |  All values in 2024 AUD")
    sections.append("=" * 74)

    # ── 1. Why reform? ──
    sections.append("\n" + "─" * 74)
    sections.append("  1. THE CASE FOR REFORM: WHY THE STATUS QUO IS UNSUSTAINABLE")
    sections.append("─" * 74)
    sections.append("""
Australia's road funding model is built on fuel excise — a tax designed for a
century of internal combustion engines. As the fleet electrifies, this
revenue base is eroding at ~4% per year. By 2035, fuel excise could fall
below $6 billion annually while road maintenance needs continue to grow.

Meanwhile, congestion costs Australian capitals an estimated $19 billion per
year, with no price signal to manage demand. Electric vehicles — which cause
the same road wear and congestion as their ICE counterparts — contribute zero
fuel excise. The current system fails on three fronts:

  (a) Revenue adequacy: spending already exceeds hypothecated revenue
  (b) Efficiency: no signal to reduce congestion or optimise road use
  (c) Equity: EVs (disproportionately owned by higher-income households)
      free-ride on infrastructure funded by ICE drivers

The question is not whether to reform, but how.
""")

    # ── 2. Theoretical foundations ──
    sections.append("─" * 74)
    sections.append("  2. THEORETICAL FOUNDATIONS")
    sections.append("─" * 74)
    sections.append("""
This simulation is grounded in six bodies of economic theory, each offering
a different lens on what road pricing should achieve:
""")
    sections.append(format_theory_summary())
    sections.append("""
No single theory provides a complete answer. The tension between Pigouvian
efficiency (charge the full external cost) and equity concerns (protect
vulnerable users) is a genuine trade-off, not a solvable optimisation problem.
The simulation quantifies these tensions.
""")

    # ── 3. Simulation results ──
    sections.append("─" * 74)
    sections.append("  3. SIMULATION RESULTS: SEVEN REGIMES COMPARED")
    sections.append("─" * 74)

    # Summary table
    sections.append("\n  Key Metrics by Regime:")
    sections.append("  " + "-" * 70)
    header = (
        f"  {'Regime':<20} {'Revenue':>10} {'VKT Chg':>9} {'CO₂':>8} "
        f"{'Cong.Cost':>10} {'$/km Car':>9} {'$/km HV':>9}"
    )
    sections.append(header)
    sections.append("  " + "-" * 70)

    for _, row in df.iterrows():
        line = (
            f"  {row['regime']:<20} "
            f"${row['revenue_bn']:>8.1f}B "
            f"{row['vkt_change_pct']:>+7.1f}% "
            f"{row['co2_mt']:>6.1f}Mt "
            f"${row['congestion_cost_bn']:>8.1f}B "
            f"${row['avg_passenger_charge_per_km']:>7.3f} "
            f"${row['avg_hv_charge_per_km']:>7.3f}"
        )
        sections.append(line)
    sections.append("  " + "-" * 70)

    # ── 4. Regime-by-regime analysis ──
    sections.append("\n" + "─" * 74)
    sections.append("  4. REGIME-BY-REGIME ANALYSIS")
    sections.append("─" * 74)

    analyses = _regime_analyses(df, sq)
    for name, text in analyses.items():
        sections.append(f"\n  ▸ {name}")
        sections.append(f"  {'·' * 40}")
        sections.append(text)

    # ── 5. Trade-offs ──
    sections.append("\n" + "─" * 74)
    sections.append("  5. THE INESCAPABLE TRADE-OFFS")
    sections.append("─" * 74)
    sections.append(_tradeoff_analysis(df, sq))

    # ── 6. 2030 outlook ──
    sections.append("\n" + "─" * 74)
    sections.append("  6. LOOKING AHEAD: THE 2030 FLEET")
    sections.append("─" * 74)
    sections.append("""
    By 2030, Australia's passenger BEV fleet is projected to grow from ~320,000
    to ~1.9 million vehicles. PHEVs will triple. The fuel excise gap widens
    dramatically. Under the Status Quo:

      • Fuel excise revenue falls by a further ~$2-3B per year
      • Road wear from heavier EVs continues unpriced
      • Congestion worsens as total VKT grows ~1.5% annually

    Every pricing regime becomes MORE advantageous relative to the Status Quo
    over time, simply because the Status Quo deteriorates. The cost of inaction
    compounds. A regime that looks only marginally better today may represent
    billions in cumulative benefit over a decade.
""")

    # ── 7. Implications ──
    sections.append("─" * 74)
    sections.append("  7. IMPLICATIONS — WITHOUT PRESCRIPTION")
    sections.append("─" * 74)
    sections.append("""
    This simulation deliberately avoids recommending a single regime. Instead,
    it surfaces the value judgements that any decision must confront:

    1. REVENUE vs FREEDOM: Higher charges generate more revenue but restrict
       mobility. How much should government manage travel demand through price?

    2. EFFICIENCY vs EQUITY: Congestion pricing is economically optimal but
       hits shift workers, parents, and outer-suburban commuters hardest.
       Is efficiency worth the distributional cost?

    3. SIMPLICITY vs PRECISION: A flat per-km charge is easy to understand
       and administer but leaves congestion unpriced. Full externality pricing
       captures every dimension but is fiendishly complex. Where on this
       spectrum is the right landing point?

    4. FREIGHT vs PASSENGER: Heavy vehicles cause massively disproportionate
       road damage. Pricing this accurately is fair but raises freight costs —
       which flow through to consumer prices. How much of road wear should
       freight pay for directly?

    5. TRANSITION vs DISRUPTION: Gradual reform (e.g., per-km charge for
       new EVs only) minimises political resistance but delays benefits.
       Comprehensive reform is faster but more disruptive. What pace of
       change is acceptable?

    6. TECHNOLOGY NEUTRALITY: Should the pricing system be indifferent to
       powertrain type (charging ICE and BEV equally per km), or should it
       reward lower-emission vehicles? Each approach has merit.

    These are ultimately political and ethical choices, not technical ones.
    The simulation provides the evidence base; the values are yours.
""")

    sections.append("=" * 74)
    sections.append("  END OF REPORT")
    sections.append("=" * 74)

    return "\n".join(sections)


def _regime_analyses(df: pd.DataFrame, sq: pd.Series) -> dict:
    """Generate per-regime narrative analysis."""
    analyses = {}

    for _, row in df.iterrows():
        name = row["regime"]
        rev_diff = row["revenue_bn"] - sq["revenue_bn"]
        cong_diff = row["congestion_cost_bn"] - sq["congestion_cost_bn"]
        co2_diff = row["co2_mt"] - sq["co2_mt"]

        if name == "Status Quo":
            analyses[row["regime_full"]] = (
                f"    Revenue: ${row['revenue_bn']:.1f}B | "
                f"Congestion cost: ${row['congestion_cost_bn']:.1f}B | "
                f"CO₂: {row['co2_mt']:.1f}Mt\n\n"
                "    The baseline. Fuel excise provides a rough proxy for road use,\n"
                "    but its effectiveness diminishes each year as EVs grow. Registration\n"
                "    fees bear no relation to actual road use. Congestion is entirely\n"
                "    unpriced outside a handful of toll roads."
            )
        else:
            rev_word = "more" if rev_diff > 0 else "less"
            cong_word = "lower" if cong_diff < 0 else "higher"
            co2_word = "lower" if co2_diff < 0 else "higher"

            analyses[row["regime_full"]] = (
                f"    Revenue: ${row['revenue_bn']:.1f}B "
                f"({rev_diff:+.1f}B vs Status Quo) | "
                f"VKT change: {row['vkt_change_pct']:+.1f}%\n"
                f"    Congestion cost: ${row['congestion_cost_bn']:.1f}B "
                f"({abs(cong_diff):.1f}B {cong_word}) | "
                f"CO₂: {row['co2_mt']:.1f}Mt ({abs(co2_diff):.1f}Mt {co2_word})\n"
                f"    Avg car charge: ${row['avg_passenger_charge_per_km']:.3f}/km | "
                f"Avg heavy vehicle: ${row['avg_hv_charge_per_km']:.3f}/km\n"
                f"    Urban revenue share: {row['urban_revenue_share']:.0f}% | "
                f"Rural: {row['rural_revenue_share']:.0f}%"
            )

    return analyses


def _tradeoff_analysis(df: pd.DataFrame, sq: pd.Series) -> str:
    """Generate the trade-off narrative section."""
    # Find regime with highest revenue
    max_rev = df.loc[df["revenue_bn"].idxmax()]
    # Find regime with lowest congestion
    min_cong = df.loc[df["congestion_cost_bn"].idxmin()]
    # Find regime with lowest CO2
    min_co2 = df.loc[df["co2_mt"].idxmin()]
    # Find regime with lowest VKT impact
    min_vkt_chg = df.loc[df["vkt_change_pct"].abs().idxmin()]

    return f"""
    REVENUE CHAMPION: {max_rev['regime']}
      Generates ${max_rev['revenue_bn']:.1f}B — but at what cost to mobility
      and equity? High charges reduce demand by {max_rev['vkt_change_pct']:.1f}%.

    CONGESTION CHAMPION: {min_cong['regime']}
      Achieves the lowest congestion cost at ${min_cong['congestion_cost_bn']:.1f}B
      — but is complex to administer and politically contentious.

    EMISSIONS CHAMPION: {min_co2['regime']}
      Produces the lowest CO₂ at {min_co2['co2_mt']:.1f}Mt — through a combination
      of demand reduction and incentivising lower-emission vehicles.

    LEAST DISRUPTIVE: {min_vkt_chg['regime']}
      Smallest demand impact at {min_vkt_chg['vkt_change_pct']:+.1f}% VKT change
      — but this also means the least congestion and emissions benefit.

    The fundamental insight: no regime wins on every dimension. Choosing a
    pricing model is choosing which objectives to prioritise and which
    trade-offs to accept. The simulation quantifies these trade-offs so
    the choice can be made with open eyes.
"""
