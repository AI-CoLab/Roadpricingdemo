"""
Theoretical foundations for road pricing models.

This module documents the economic theories underpinning each pricing regime,
providing the intellectual framework that grounds the simulation.

References:
- Pigou, A.C. (1920). The Economics of Welfare.
- Vickrey, W. (1969). Congestion Theory and Transport Investment.
- Walters, A.A. (1961). The Theory and Measurement of Private and Social Cost of Highway Congestion.
- Small, K.A. & Verhoef, E.T. (2007). The Economics of Urban Transportation.
- Bureau of Infrastructure and Transport Research Economics (BITRE) various reports.
- Infrastructure Victoria (2020). Good Move: Fixing Transport Congestion.
- Henry Tax Review (2010). Australia's Future Tax System.
"""


THEORIES = {
    "pigouvian": {
        "name": "Pigouvian Taxation",
        "origin": "Arthur Pigou (1920)",
        "principle": (
            "Road users impose external costs (congestion, pollution, accidents, noise) "
            "on others that are not reflected in their private costs. A Pigouvian tax "
            "sets the charge equal to the marginal external cost, internalising the "
            "externality so that users face the true social cost of their trip."
        ),
        "implication": (
            "Charges should vary by time, location, and vehicle type to reflect the "
            "actual externality imposed. A diesel truck on a congested urban arterial "
            "at peak hour imposes far greater external costs than an EV on a rural "
            "highway at midnight."
        ),
        "regimes": ["congestion", "externality_weighted"],
    },
    "ramsey": {
        "name": "Ramsey Pricing",
        "origin": "Frank Ramsey (1927)",
        "principle": (
            "When a provider must recover fixed costs, prices should be set inversely "
            "proportional to demand elasticity. Users with fewer alternatives (inelastic "
            "demand) pay more; those with options (elastic demand) pay less. This "
            "minimises deadweight loss while meeting a revenue target."
        ),
        "implication": (
            "Freight operators with fixed schedules and few modal alternatives would "
            "face higher charges than discretionary leisure drivers. Politically "
            "contentious but economically efficient for cost recovery."
        ),
        "regimes": ["distance_based"],
    },
    "vickrey_congestion": {
        "name": "Vickrey Congestion Pricing",
        "origin": "William Vickrey (1963, 1969)",
        "principle": (
            "Congestion arises because road space is unpriced at peak times. A "
            "time-varying toll that rises as congestion builds and falls as it "
            "dissipates can spread demand across time, reducing peak congestion "
            "without necessarily reducing total travel. The optimal toll equals the "
            "marginal delay cost imposed on all other users."
        ),
        "implication": (
            "Requires real-time or predictive pricing signals. Most effective on "
            "bottleneck corridors. Stockholm and Singapore provide empirical support: "
            "peak traffic can fall 15-25%% with well-designed congestion charges."
        ),
        "regimes": ["congestion", "cordon"],
    },
    "cost_recovery": {
        "name": "Road Cost Recovery / User-Pays",
        "origin": "Public finance tradition; Henry Tax Review (2010)",
        "principle": (
            "Road infrastructure is a capital asset. Users should pay for the wear "
            "and tear they cause and a fair share of capital costs, analogous to "
            "utility pricing. The fourth-power law means heavy vehicles cause "
            "disproportionate pavement damage relative to their share of traffic."
        ),
        "implication": (
            "Favours weight-distance charges. Australia's current fuel excise "
            "acts as a crude proxy but breaks down as the fleet electrifies: "
            "EVs cause the same road wear but pay zero fuel excise. A mass-distance "
            "charge restores the user-pays link."
        ),
        "regimes": ["weight_distance", "flat_registration"],
    },
    "equity_access": {
        "name": "Equity and Accessibility",
        "origin": "Social welfare economics; Rawlsian justice",
        "principle": (
            "Transport is a derived demand essential for accessing employment, "
            "education, and healthcare. Pricing must consider distributional impacts: "
            "lower-income households spend a higher share of income on transport, "
            "often live in car-dependent outer suburbs, and have fewer modal "
            "alternatives."
        ),
        "implication": (
            "Any pricing scheme needs complementary measures — public transport "
            "investment, concession caps, or revenue recycling — to avoid regressive "
            "outcomes. Pure efficiency pricing without equity safeguards is unlikely "
            "to be politically sustainable."
        ),
        "regimes": ["all"],
    },
    "second_best": {
        "name": "Second-Best Pricing",
        "origin": "Lipsey & Lancaster (1956); Small & Verhoef (2007)",
        "principle": (
            "First-best (Pigouvian) pricing is rarely achievable due to political, "
            "technological, and institutional constraints. Second-best approaches "
            "approximate the ideal within practical limits — e.g., cordon charges "
            "instead of full network pricing, or flat per-km rates instead of "
            "real-time marginal cost pricing."
        ),
        "implication": (
            "The 'perfect' scheme is the enemy of the good. Simpler schemes that "
            "capture most of the welfare gains with lower transaction and political "
            "costs may be preferable. The simulation explores this trade-off."
        ),
        "regimes": ["cordon", "flat_distance", "hybrid"],
    },
}


def get_theoretical_basis(regime_name: str) -> list[dict]:
    """Return all theories that underpin a given pricing regime."""
    results = []
    for key, theory in THEORIES.items():
        if regime_name in theory["regimes"] or "all" in theory["regimes"]:
            results.append({"key": key, **theory})
    return results


def format_theory_summary() -> str:
    """Return a formatted summary of all theories for display."""
    lines = []
    for key, t in THEORIES.items():
        lines.append(f"\n{'='*70}")
        lines.append(f"  {t['name']}  ({t['origin']})")
        lines.append(f"{'='*70}")
        lines.append(f"  Principle: {t['principle']}")
        lines.append(f"  Implication: {t['implication']}")
    return "\n".join(lines)
