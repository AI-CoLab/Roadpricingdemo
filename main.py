#!/usr/bin/env python3
"""
Australian Road Pricing Simulation
===================================

Simulates the effects of seven different road pricing regimes on Australia's
road network, using calibrated data on fleet composition, travel demand,
road types, and externality costs.

Produces:
  - A comprehensive narrative report (printed to stdout and saved to file)
  - Nine visualisation charts (saved to output/)
  - A CSV summary of key metrics

Usage:
    python main.py                    # Run with 2026 fleet
    python main.py --year 2030        # Run with projected 2030 fleet
    python main.py --no-charts        # Skip chart generation
    python main.py --sensitivity      # Include sensitivity analysis

Theoretical grounding:
    Pigouvian taxation, Vickrey congestion pricing, Ramsey pricing,
    cost-recovery / user-pays, second-best theory, equity considerations.

Data sources:
    ABS Motor Vehicle Census, BITRE, Infrastructure Australia, ATAP,
    NTC, state transport surveys (VISTA/HTS), DCCEEW emission factors.
"""

import argparse
import os
import sys
import time

import pandas as pd

from src.simulation import run_simulation, run_sensitivity
from src.visualisation import generate_all_charts
from src.report import generate_report
from src.pricing_regimes import (
    TimeOfDayCongestion, HybridReformPackage, FlatDistanceBased,
)


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Australian Road Pricing Simulation"
    )
    parser.add_argument(
        "--year", choices=["2026", "2030"], default="2026",
        help="Fleet year for simulation (default: 2026)"
    )
    parser.add_argument(
        "--no-charts", action="store_true",
        help="Skip chart generation"
    )
    parser.add_argument(
        "--sensitivity", action="store_true",
        help="Run sensitivity analysis on key parameters"
    )
    args = parser.parse_args()

    print("\n" + "=" * 74)
    print("  AUSTRALIAN ROAD PRICING SIMULATION")
    print("  Modelling alternative futures for road funding and management")
    print("=" * 74)

    # ── Run main simulation ──
    print(f"\n  Running simulation with {args.year} fleet data...")
    t0 = time.time()
    df = run_simulation(fleet_year=args.year)
    elapsed = time.time() - t0
    print(f"  Simulation complete in {elapsed:.1f}s — "
          f"{len(df)} regimes evaluated.")

    # ── Save CSV ──
    csv_path = os.path.join(OUTPUT_DIR, "simulation_results.csv")
    export_cols = [
        "regime", "regime_full", "revenue_bn", "vkt_bn", "vkt_post_bn",
        "vkt_change_pct", "co2_mt", "congestion_cost_bn",
        "externality_cost_bn", "avg_passenger_charge_per_km",
        "avg_hv_charge_per_km", "urban_revenue_share", "rural_revenue_share",
        "peak_revenue_share",
    ]
    df[export_cols].to_csv(csv_path, index=False, float_format="%.4f")
    print(f"  Results saved to {csv_path}")

    # ── Generate report ──
    report = generate_report(df, fleet_year=args.year)
    report_path = os.path.join(OUTPUT_DIR, "report.txt")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"  Report saved to {report_path}")

    # Print report to stdout
    print("\n")
    print(report)

    # ── Generate charts ──
    if not args.no_charts:
        print("\n  Generating visualisations...")
        chart_paths = generate_all_charts(df)
        for p in chart_paths:
            print(f"    ✓ {os.path.basename(p)}")
        print(f"\n  {len(chart_paths)} charts saved to {OUTPUT_DIR}/")

    # ── Sensitivity analysis ──
    if args.sensitivity:
        print("\n" + "─" * 74)
        print("  SENSITIVITY ANALYSIS")
        print("─" * 74)

        # Vary congestion peak multiplier
        print("\n  1. Congestion charge: varying peak multiplier (2x to 8x)...")
        sens_cong = run_sensitivity(
            parameter_name="Peak Multiplier",
            values=[2.0, 3.0, 4.0, 5.0, 6.0, 8.0],
            regime_class=TimeOfDayCongestion,
            regime_kwargs={"base_rate": 0.015, "shoulder_multiplier": 2.0},
            param_kwarg_key="peak_multiplier",
        )
        print(f"     Revenue range: ${sens_cong['revenue_bn'].min():.1f}B "
              f"to ${sens_cong['revenue_bn'].max():.1f}B")
        print(f"     VKT change range: {sens_cong['vkt_change_pct'].min():.1f}% "
              f"to {sens_cong['vkt_change_pct'].max():.1f}%")

        # Vary flat distance rate
        print("\n  2. Flat distance charge: varying rate ($0.01 to $0.06/km)...")
        sens_flat = run_sensitivity(
            parameter_name="Per-km Rate",
            values=[0.01, 0.02, 0.025, 0.03, 0.04, 0.06],
            regime_class=FlatDistanceBased,
            regime_kwargs={},
            param_kwarg_key="rate_per_km",
        )
        print(f"     Revenue range: ${sens_flat['revenue_bn'].min():.1f}B "
              f"to ${sens_flat['revenue_bn'].max():.1f}B")

        # Vary hybrid peak surcharge
        print("\n  3. Hybrid reform: varying peak surcharge ($0.02 to $0.10/km)...")
        sens_hybrid = run_sensitivity(
            parameter_name="Peak Surcharge",
            values=[0.02, 0.03, 0.04, 0.06, 0.08, 0.10],
            regime_class=HybridReformPackage,
            regime_kwargs={"base_rate": 0.025, "weight_factor_per_tonne": 0.003},
            param_kwarg_key="peak_surcharge",
        )
        print(f"     Revenue range: ${sens_hybrid['revenue_bn'].min():.1f}B "
              f"to ${sens_hybrid['revenue_bn'].max():.1f}B")

        # Save sensitivity results
        sens_all = pd.concat([sens_cong, sens_flat, sens_hybrid],
                             ignore_index=True)
        sens_csv = os.path.join(OUTPUT_DIR, "sensitivity_results.csv")
        sens_export = [
            "param_name", "param_value", "regime", "revenue_bn",
            "vkt_change_pct", "co2_mt", "congestion_cost_bn",
        ]
        sens_all[sens_export].to_csv(sens_csv, index=False, float_format="%.4f")
        print(f"\n  Sensitivity results saved to {sens_csv}")

    # ── Closing ──
    print("\n" + "=" * 74)
    print("  Simulation complete.")
    print("  Charts and data are in the output/ directory.")
    print("  The report presents trade-offs — the policy choice is yours.")
    print("=" * 74 + "\n")


if __name__ == "__main__":
    main()
