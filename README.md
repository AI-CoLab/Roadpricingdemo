# Australian Road Pricing Simulation

A simulation comparing seven road pricing regimes across Australia's road network,
grounded in transport economics theory and calibrated with Australian data.

## What This Does

Models the effects of different road pricing approaches on:
- **Revenue generation** — can the regime fund road infrastructure?
- **Congestion** — does it reduce peak-hour delays?
- **Emissions** — does it incentivise cleaner transport?
- **Equity** — who bears the cost (urban vs rural, cars vs trucks, ICE vs EV)?
- **Feasibility** — how complex and politically viable is it?

## Pricing Regimes Compared

| Regime | Theory | Key Feature |
|--------|--------|-------------|
| **Status Quo** | Cost-recovery (crude) | Fuel excise + registration + tolls |
| **Flat Distance** | Second-best / user-pays | Same $/km for all vehicles and times |
| **Congestion** | Vickrey / Pigouvian | Time-varying charge, peak multiplier |
| **CBD Cordon** | Second-best (London/Stockholm model) | Fixed charge to enter CBD zone |
| **Weight-Distance** | AASHTO fourth-power / Henry Review | Charge scaled by vehicle mass |
| **Full Externality** | First-best Pigouvian | Charge = marginal external cost |
| **Hybrid Reform** | Pragmatic second-best | Distance + congestion top-up + weight |

## Theoretical Foundations

Six bodies of economic theory inform the model:
- **Pigouvian Taxation** (Pigou 1920) — price the externality
- **Ramsey Pricing** (Ramsey 1927) — minimise deadweight loss for cost recovery
- **Vickrey Congestion Pricing** (Vickrey 1963/1969) — time-varying tolls
- **Cost Recovery / User-Pays** (Henry Tax Review 2010) — road damage charges
- **Equity & Accessibility** (Rawlsian) — distributional fairness
- **Second-Best Theory** (Lipsey & Lancaster 1956) — practical approximations

## Data Sources

Calibrated using publicly available Australian data:
- ABS Motor Vehicle Census (fleet composition)
- BITRE (road expenditure, VKT, congestion costs)
- ATAP (value of time, externality costs)
- NTC (heavy vehicle charges)
- State transport surveys (VISTA, HTS)
- DCCEEW National Greenhouse Accounts (emission factors)

## Quick Start

```bash
pip install -r requirements.txt

# Run the simulation (2026 fleet)
python main.py

# Run with 2030 projected fleet
python main.py --year 2030

# Include sensitivity analysis
python main.py --sensitivity

# Skip chart generation
python main.py --no-charts
```

## Output

Results are saved to `output/`:
- `report.txt` — full narrative analysis
- `simulation_results.csv` — key metrics by regime
- `sensitivity_results.csv` — parameter sensitivity data
- 9 PNG charts showing trade-offs, revenue, emissions, equity, and more

## Project Structure

```
├── main.py                    # Entry point
├── src/
│   ├── theory.py              # Theoretical foundations documentation
│   ├── australian_data.py     # Fleet, network, and externality data
│   ├── pricing_regimes.py     # Seven pricing regime implementations
│   ├── simulation.py          # Simulation engine
│   ├── visualisation.py       # Chart generation
│   └── report.py              # Narrative report generator
├── output/                    # Generated results and charts
└── requirements.txt
```
