"""
Australian Road Pricing Simulation — Interactive Dashboard
==========================================================

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.australian_data import (
    FLEET, FLEET_PROJECTION_2030, ROAD_NETWORK,
    HOURLY_DEMAND_PROFILE, EXTERNALITY_COSTS,
    CURRENT_REVENUE, CONGESTION_COST_TOTAL_BN,
)
from src.pricing_regimes import (
    StatusQuo, FlatDistanceBased, TimeOfDayCongestion,
    CordonCharge, WeightDistance, ExternalityWeighted,
    HybridReformPackage,
)
from src.simulation import run_simulation
from src.theory import THEORIES

# ── Page config ──
st.set_page_config(
    page_title="Australian Road Pricing Simulation",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Colour palette ──
COLORS = {
    "Status Quo": "#7f8c8d",
    "Flat Distance": "#3498db",
    "Congestion": "#e74c3c",
    "Cordon": "#9b59b6",
    "Weight-Distance": "#e67e22",
    "Externality": "#2ecc71",
    "Hybrid": "#1abc9c",
}


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert '#rrggbb' to 'rgba(r,g,b,a)' for Plotly compatibility."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR — Controls
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("Simulation Controls")

    st.markdown("---")
    st.subheader("Fleet & Demand")
    fleet_year = st.radio("Fleet year", ["2026", "2030"],
                          help="2030 projects EV growth and ICE decline")
    demand_response = st.checkbox("Model demand elasticity", value=True,
                                  help="Apply price elasticity — users change "
                                       "behaviour in response to charges")

    st.markdown("---")
    st.subheader("Regime Parameters")

    st.markdown("**Flat Distance**")
    flat_rate = st.slider("Per-km rate ($)", 0.01, 0.08, 0.025, 0.005,
                          format="$%.3f")

    st.markdown("**Congestion Charge**")
    cong_base = st.slider("Base rate ($/km)", 0.005, 0.04, 0.015, 0.005,
                           format="$%.3f")
    cong_peak_mult = st.slider("Peak multiplier", 1.5, 8.0, 4.0, 0.5)
    cong_shoulder_mult = st.slider("Shoulder multiplier", 1.0, 4.0, 2.0, 0.5)

    st.markdown("**CBD Cordon**")
    cordon_charge = st.slider("Cordon entry charge ($)", 2.0, 20.0, 8.0, 1.0,
                               format="$%.0f")
    cordon_peak_only = st.checkbox("Peak hours only", value=True)

    st.markdown("**Weight-Distance**")
    wd_base = st.slider("WD base rate ($/km)", 0.005, 0.05, 0.02, 0.005,
                          format="$%.3f")

    st.markdown("**Externality**")
    carbon_price = st.slider("Carbon price ($/tonne)", 25.0, 200.0, 75.0, 5.0,
                              format="$%.0f")
    congestion_vot = st.slider("Value of travel time ($/hr)", 10.0, 50.0, 22.5, 2.5,
                                format="$%.1f")

    st.markdown("**Hybrid Reform**")
    hybrid_base = st.slider("Hybrid base rate ($/km)", 0.01, 0.06, 0.025, 0.005,
                             format="$%.3f")
    hybrid_peak = st.slider("Hybrid peak surcharge ($/km)", 0.01, 0.12, 0.04, 0.01,
                             format="$%.2f")
    hybrid_weight = st.slider("Weight factor ($/t/km)", 0.001, 0.010, 0.003, 0.001,
                               format="$%.3f")

    st.markdown("---")
    st.subheader("Display")
    selected_regimes = st.multiselect(
        "Regimes to compare",
        list(COLORS.keys()),
        default=list(COLORS.keys()),
    )


# ═══════════════════════════════════════════════════════════════════════════
# BUILD REGIMES & RUN SIMULATION
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data
def run_sim(fleet_year, demand_response,
            flat_rate, cong_base, cong_peak_mult, cong_shoulder_mult,
            cordon_charge, cordon_peak_only,
            wd_base, carbon_price, congestion_vot,
            hybrid_base, hybrid_peak, hybrid_weight):
    regimes = [
        StatusQuo(),
        FlatDistanceBased(rate_per_km=flat_rate),
        TimeOfDayCongestion(base_rate=cong_base,
                            peak_multiplier=cong_peak_mult,
                            shoulder_multiplier=cong_shoulder_mult),
        CordonCharge(cordon_charge=cordon_charge,
                     applies_peak_only=cordon_peak_only),
        WeightDistance(base_rate=wd_base),
        ExternalityWeighted(co2_price_per_t=carbon_price,
                            congestion_vot=congestion_vot),
        HybridReformPackage(base_rate=hybrid_base,
                            peak_surcharge=hybrid_peak,
                            weight_factor_per_tonne=hybrid_weight),
    ]
    return run_simulation(
        regimes=regimes,
        fleet_year=fleet_year,
        include_demand_response=demand_response,
    )


df = run_sim(fleet_year, demand_response,
             flat_rate, cong_base, cong_peak_mult, cong_shoulder_mult,
             cordon_charge, cordon_peak_only,
             wd_base, carbon_price, congestion_vot,
             hybrid_base, hybrid_peak, hybrid_weight)

# Filter to selected regimes
df_display = df[df["regime"].isin(selected_regimes)].copy()
color_list = [COLORS[r] for r in df_display["regime"]]


# ═══════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════
st.title("Australian Road Pricing Simulation")
st.markdown(
    "Comparing **seven pricing regimes** across Australia's road network — "
    "grounded in transport economics theory, calibrated with real data. "
    "Adjust parameters in the sidebar to explore trade-offs."
)

# ═══════════════════════════════════════════════════════════════════════════
# TAB LAYOUT
# ═══════════════════════════════════════════════════════════════════════════
tab_overview, tab_tradeoffs, tab_equity, tab_theory, tab_future, tab_data = st.tabs([
    "Overview", "Trade-Offs", "Equity & Distribution",
    "Theoretical Foundations", "2030 Outlook", "Raw Data",
])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
with tab_overview:
    # ── KPI row ──
    st.subheader("The Fiscal Challenge")
    cols = st.columns(4)
    cols[0].metric("Current Road Revenue", "$28.3B",
                   help="Fuel excise + registration + tolls + stamp duty")
    cols[1].metric("Road Expenditure", "$32.5B",
                   delta="-$4.2B gap", delta_color="inverse")
    cols[2].metric("Annual Congestion Cost", "$19B",
                   help="BITRE / Infrastructure Australia estimate for capitals")
    cols[3].metric("Fuel Excise Erosion", "~4% pa",
                   help="Declining as fleet electrifies")

    st.markdown("---")

    # ── Fuel excise erosion chart ──
    st.subheader("The Looming Fiscal Cliff")
    years = np.arange(2024, 2041)
    base_excise = 11.8
    bau = base_excise * (1 - 0.04) ** (years - 2024)
    fast_ev = base_excise * (1 - 0.07) ** (years - 2024)
    road_needs = 32.5 * 1.02 ** (years - 2024)

    fig_erosion = go.Figure()
    fig_erosion.add_trace(go.Scatter(
        x=years, y=bau, mode="lines+markers", name="Fuel excise (base case: 4% pa decline)",
        line=dict(color="#3498db", width=3), marker=dict(size=5)))
    fig_erosion.add_trace(go.Scatter(
        x=years, y=fast_ev, mode="lines+markers", name="Fuel excise (fast EV: 7% pa decline)",
        line=dict(color="#e74c3c", width=3, dash="dash"), marker=dict(size=5)))
    fig_erosion.add_trace(go.Scatter(
        x=years, y=road_needs, mode="lines+markers", name="Road expenditure needs (2% pa growth)",
        line=dict(color="#e67e22", width=3, dash="dot"), marker=dict(size=5)))
    fig_erosion.add_trace(go.Scatter(
        x=np.concatenate([years, years[::-1]]),
        y=np.concatenate([fast_ev, road_needs[::-1]]),
        fill="toself", fillcolor="rgba(231,76,60,0.08)",
        line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig_erosion.add_annotation(x=2034, y=(fast_ev[10] + road_needs[10]) / 2,
                                text="<b>Growing funding gap</b>",
                                showarrow=False, font=dict(size=14, color="#c0392b"))
    fig_erosion.update_layout(
        height=420, template="plotly_white",
        yaxis_title="$ Billion", xaxis_title="Year",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(t=30))
    st.plotly_chart(fig_erosion, use_container_width=True)

    st.markdown("---")

    # ── Revenue comparison ──
    st.subheader("Revenue by Regime")
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Bar(
        x=df_display["regime"], y=df_display["revenue_bn"],
        marker_color=color_list,
        text=[f"${v:.1f}B" for v in df_display["revenue_bn"]],
        textposition="outside", textfont=dict(size=13, color="black"),
    ))
    fig_rev.add_hline(y=28.3, line_dash="dash", line_color="#e74c3c",
                      annotation_text="Current road revenue ($28.3B)",
                      annotation_position="top right")
    fig_rev.add_hline(y=32.5, line_dash="dot", line_color="#e67e22",
                      annotation_text="Road expenditure ($32.5B)",
                      annotation_position="bottom right")
    fig_rev.update_layout(
        height=450, template="plotly_white",
        yaxis_title="Annual Revenue ($ Billion)",
        showlegend=False, margin=dict(t=30))
    st.plotly_chart(fig_rev, use_container_width=True)

    # ── Summary table ──
    st.subheader("Key Metrics Comparison")
    summary = df_display[[
        "regime", "revenue_bn", "vkt_change_pct", "co2_mt",
        "congestion_cost_bn", "avg_passenger_charge_per_km", "avg_hv_charge_per_km",
    ]].copy()
    summary.columns = [
        "Regime", "Revenue ($B)", "VKT Change (%)", "CO₂ (Mt)",
        "Congestion Cost ($B)", "Avg Car Charge ($/km)", "Avg HV Charge ($/km)",
    ]
    st.dataframe(
        summary.style.format({
            "Revenue ($B)": "${:.1f}",
            "VKT Change (%)": "{:+.1f}%",
            "CO₂ (Mt)": "{:.1f}",
            "Congestion Cost ($B)": "${:.1f}",
            "Avg Car Charge ($/km)": "${:.3f}",
            "Avg HV Charge ($/km)": "${:.3f}",
        }).background_gradient(subset=["Revenue ($B)"], cmap="Blues")
         .background_gradient(subset=["Congestion Cost ($B)"], cmap="Reds_r")
         .background_gradient(subset=["CO₂ (Mt)"], cmap="Oranges_r"),
        use_container_width=True, hide_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: TRADE-OFFS
# ═══════════════════════════════════════════════════════════════════════════
with tab_tradeoffs:
    st.subheader("The Core Trade-Off: Revenue vs Congestion Relief")
    st.markdown(
        "Each regime occupies a different position in the trade-off space. "
        "Bubble size reflects total externality cost reduction. "
        "**There is no regime in the top-right corner** — that's the trade-off."
    )

    sq = df.loc[df["regime"] == "Status Quo"].iloc[0]
    fig_scatter = go.Figure()
    for _, row in df_display.iterrows():
        cong_red = (sq["congestion_cost_bn"] - row["congestion_cost_bn"]) / sq["congestion_cost_bn"] * 100
        ext_red = (sq["externality_cost_bn"] - row["externality_cost_bn"]) / sq["externality_cost_bn"] * 100
        size = max(abs(ext_red) * 1.5, 12)
        fig_scatter.add_trace(go.Scatter(
            x=[row["revenue_bn"]], y=[cong_red],
            mode="markers+text", text=[row["regime"]],
            textposition="top center", textfont=dict(size=12, color=COLORS[row["regime"]]),
            marker=dict(size=size, color=COLORS[row["regime"]], opacity=0.8,
                        line=dict(width=1.5, color="white")),
            name=row["regime"],
            hovertemplate=(
                f"<b>{row['regime']}</b><br>"
                f"Revenue: ${row['revenue_bn']:.1f}B<br>"
                f"Congestion reduction: {cong_red:.1f}%<br>"
                f"Externality reduction: {ext_red:.1f}%<br>"
                f"<extra></extra>"
            ),
        ))
    fig_scatter.add_vline(x=28.3, line_dash="dash", line_color="rgba(231,76,60,0.4)",
                          annotation_text="Current revenue")
    fig_scatter.add_hline(y=0, line_color="rgba(0,0,0,0.15)")
    fig_scatter.update_layout(
        height=550, template="plotly_white",
        xaxis_title="Annual Revenue ($ Billion)",
        yaxis_title="Congestion Cost Reduction (%)",
        showlegend=False, margin=dict(t=30))
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")

    # ── Demand response ──
    st.subheader("Demand Response: How Much Does Driving Change?")
    fig_vkt = go.Figure()
    fig_vkt.add_trace(go.Bar(
        y=df_display["regime"], x=df_display["vkt_change_pct"],
        orientation="h", marker_color=color_list,
        text=[f"{v:+.1f}%" for v in df_display["vkt_change_pct"]],
        textposition="outside", textfont=dict(size=12),
    ))
    fig_vkt.add_vline(x=0, line_color="gray", line_width=1)
    fig_vkt.update_layout(
        height=400, template="plotly_white",
        xaxis_title="Change in Vehicle-km Travelled (%)",
        showlegend=False, margin=dict(t=30, l=120))
    st.plotly_chart(fig_vkt, use_container_width=True)

    st.markdown("---")

    # ── Emissions ──
    st.subheader("Emissions Outcomes")
    fig_co2 = go.Figure()
    fig_co2.add_trace(go.Bar(
        x=df_display["regime"], y=df_display["co2_mt"],
        marker_color=color_list,
        text=[f"{v:.1f} Mt" for v in df_display["co2_mt"]],
        textposition="outside", textfont=dict(size=12),
    ))
    fig_co2.update_layout(
        height=420, template="plotly_white",
        yaxis_title="Annual CO₂ Emissions (Megatonnes)",
        showlegend=False, margin=dict(t=30))
    st.plotly_chart(fig_co2, use_container_width=True)

    st.markdown("---")

    # ── Multi-dimensional scorecard ──
    st.subheader("Multi-Dimensional Scorecard")
    st.markdown("No single regime dominates across all dimensions.")

    dimensions = ["Revenue Adequacy", "Congestion Reduction", "Emissions Reduction",
                  "Equity", "Simplicity", "Political Feasibility"]

    simplicity_map = {"Status Quo": 4.5, "Flat Distance": 4.0, "Congestion": 2.0,
                      "Cordon": 3.5, "Weight-Distance": 3.0, "Externality": 1.0, "Hybrid": 2.5}
    feasibility_map = {"Status Quo": 5.0, "Flat Distance": 3.0, "Congestion": 2.0,
                       "Cordon": 3.0, "Weight-Distance": 2.5, "Externality": 1.0, "Hybrid": 2.5}

    fig_radar = go.Figure()
    for _, row in df_display.iterrows():
        rev_score = min(5, row["revenue_bn"] / 32.5 * 5)
        cong_red = (sq["congestion_cost_bn"] - row["congestion_cost_bn"]) / sq["congestion_cost_bn"]
        cong_score = min(5, max(0, cong_red * 25 + 2.5))
        em_red = (sq["co2_mt"] - row["co2_mt"]) / sq["co2_mt"]
        em_score = min(5, max(0, em_red * 30 + 2.5))
        equity_score = max(0, 5 - row["rural_revenue_share"] / 10)
        simp_score = simplicity_map.get(row["regime"], 2.5)
        feas_score = feasibility_map.get(row["regime"], 2.5)

        values = [rev_score, cong_score, em_score, equity_score, simp_score, feas_score]
        values.append(values[0])  # close the radar

        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=dimensions + [dimensions[0]],
            name=row["regime"],
            line=dict(color=COLORS[row["regime"]], width=2.5),
            fill="toself",
            fillcolor=_hex_to_rgba(COLORS[row["regime"]], 0.09),
        ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5.5],
                                    tickvals=[1, 2, 3, 4, 5])),
        height=550, template="plotly_white",
        legend=dict(orientation="h", y=-0.1),
        margin=dict(t=30))
    st.plotly_chart(fig_radar, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: EQUITY & DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════════
with tab_equity:
    st.subheader("Who Pays? Urban vs Rural Revenue Distribution")
    st.markdown(
        "Rural Australians are more car-dependent, with fewer modal alternatives. "
        "Regimes that load costs onto rural users raise serious equity concerns."
    )

    fig_dist = go.Figure()
    fig_dist.add_trace(go.Bar(
        x=df_display["regime"], y=df_display["urban_revenue_bn"],
        name="Urban", marker_color="#3498db",
    ))
    fig_dist.add_trace(go.Bar(
        x=df_display["regime"], y=df_display["rural_revenue_bn"],
        name="Rural", marker_color="#e67e22",
    ))
    fig_dist.update_layout(
        barmode="stack", height=450, template="plotly_white",
        yaxis_title="Revenue Burden ($ Billion)",
        legend=dict(orientation="h", y=-0.12),
        margin=dict(t=30))
    st.plotly_chart(fig_dist, use_container_width=True)

    st.markdown("---")

    # ── Vehicle class charges ──
    st.subheader("Charges by Vehicle Class")
    st.markdown("Who bears the cost across different vehicle types?")

    display_classes = [
        ("passenger_ice", "Car (ICE)"),
        ("passenger_bev", "Car (BEV)"),
        ("passenger_phev", "Car (PHEV)"),
        ("lcv_ice", "Light Comm (ICE)"),
        ("lcv_bev", "Light Comm (BEV)"),
        ("rigid_truck", "Rigid Truck"),
        ("artic_truck", "Artic. Truck"),
        ("bus", "Bus"),
        ("motorcycle", "Motorcycle"),
    ]

    class_data = []
    for _, row in df_display.iterrows():
        for cls_key, cls_label in display_classes:
            class_data.append({
                "Regime": row["regime"],
                "Vehicle": cls_label,
                "Charge ($/km)": row["avg_charge_by_class"].get(cls_key, 0),
            })
    class_df = pd.DataFrame(class_data)

    fig_class = px.bar(
        class_df, x="Vehicle", y="Charge ($/km)", color="Regime",
        barmode="group", color_discrete_map=COLORS,
        height=500,
    )
    fig_class.update_layout(template="plotly_white",
                            legend=dict(orientation="h", y=-0.2),
                            margin=dict(t=30))
    st.plotly_chart(fig_class, use_container_width=True)

    st.markdown("---")

    # ── EV Fairness ──
    st.subheader("Technology Neutrality: Do EVs Pay Their Fair Share?")
    st.markdown(
        "Under the Status Quo, BEVs pay no fuel excise yet cause the same road wear "
        "and congestion. Different regimes treat this gap differently."
    )

    ev_data = []
    for _, row in df_display.iterrows():
        ice_charge = row["avg_charge_by_class"].get("passenger_ice", 0)
        bev_charge = row["avg_charge_by_class"].get("passenger_bev", 0)
        ev_data.append({"Regime": row["regime"], "Powertrain": "ICE", "Charge ($/km)": ice_charge})
        ev_data.append({"Regime": row["regime"], "Powertrain": "BEV", "Charge ($/km)": bev_charge})

    ev_df = pd.DataFrame(ev_data)
    fig_ev = px.bar(
        ev_df, x="Regime", y="Charge ($/km)", color="Powertrain",
        barmode="group", color_discrete_map={"ICE": "#e74c3c", "BEV": "#2ecc71"},
        height=430,
    )
    fig_ev.update_layout(template="plotly_white", margin=dict(t=30))
    st.plotly_chart(fig_ev, use_container_width=True)

    # ── Equity callout ──
    st.info(
        "**Key equity insight:** No regime is perfectly fair. Flat distance charges "
        "are technology-neutral but hit long-distance rural commuters. Congestion charges "
        "are geographically targeted but affect shift workers. Weight-distance is fair for "
        "road damage but raises consumer goods prices. The equity question is: **fair to whom?**"
    )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: THEORETICAL FOUNDATIONS
# ═══════════════════════════════════════════════════════════════════════════
with tab_theory:
    st.subheader("Theoretical Foundations")
    st.markdown(
        "This simulation is grounded in six bodies of economic theory. "
        "Each offers a different lens on what road pricing should achieve."
    )

    for key, t in THEORIES.items():
        with st.expander(f"**{t['name']}** — {t['origin']}", expanded=False):
            st.markdown(f"**Principle:** {t['principle']}")
            st.markdown(f"**Implication for Australia:** {t['implication']}")
            regime_names = ", ".join(r.replace("_", " ").title() for r in t["regimes"])
            st.markdown(f"**Regimes informed:** {regime_names}")

    st.markdown("---")
    st.subheader("How Theory Maps to Regimes")

    theory_map_data = []
    regime_labels = {
        "congestion": "Congestion", "externality_weighted": "Externality",
        "distance_based": "Flat Distance", "cordon": "Cordon",
        "flat_distance": "Flat Distance", "weight_distance": "Weight-Distance",
        "flat_registration": "Status Quo", "hybrid": "Hybrid", "all": "All Regimes",
    }
    for key, t in THEORIES.items():
        for r in t["regimes"]:
            theory_map_data.append({
                "Theory": t["name"],
                "Regime": regime_labels.get(r, r.replace("_", " ").title()),
            })

    theory_df = pd.DataFrame(theory_map_data)
    all_theories = list(THEORIES.values())
    all_theory_names = [t["name"] for t in all_theories]
    all_regime_names = list(COLORS.keys())

    matrix = pd.DataFrame(0, index=all_theory_names, columns=all_regime_names)
    for _, row in theory_df.iterrows():
        if row["Regime"] == "All Regimes":
            for col in matrix.columns:
                matrix.loc[row["Theory"], col] = 1
        elif row["Regime"] in matrix.columns:
            matrix.loc[row["Theory"], row["Regime"]] = 1

    fig_heat = px.imshow(
        matrix.values,
        x=matrix.columns.tolist(),
        y=matrix.index.tolist(),
        color_continuous_scale=["#ffffff", "#1abc9c"],
        labels=dict(color="Applies"),
        height=380,
    )
    fig_heat.update_layout(template="plotly_white", margin=dict(t=30),
                            coloraxis_showscale=False)
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")
    st.markdown(
        "**The central tension:** Pigouvian efficiency says charge the full external cost. "
        "Equity theory says protect vulnerable users. Second-best theory says pursue the "
        "achievable, not the perfect. These tensions cannot be resolved technically — "
        "they require value judgements."
    )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 5: 2030 OUTLOOK
# ═══════════════════════════════════════════════════════════════════════════
with tab_future:
    st.subheader("The 2030 Fleet: Why Reform Becomes More Urgent")

    # Fleet composition comparison
    fleet_2026 = {v["label"]: v["count"] for v in FLEET.values()}
    fleet_2030 = {}
    for k, v in FLEET.items():
        proj = FLEET_PROJECTION_2030.get(k, {})
        fleet_2030[v["label"]] = int(v["count"] * proj.get("count_factor", 1.0))

    fleet_comp = pd.DataFrame({
        "Vehicle Type": list(fleet_2026.keys()),
        "2026": list(fleet_2026.values()),
        "2030": list(fleet_2030.values()),
    })
    fleet_comp["Change"] = fleet_comp["2030"] - fleet_comp["2026"]
    fleet_comp["Change %"] = ((fleet_comp["2030"] - fleet_comp["2026"]) / fleet_comp["2026"] * 100)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Fleet Composition Shift**")
        fig_fleet = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]],
                                   subplot_titles=["2026 Fleet", "2030 Fleet (projected)"])
        fig_fleet.add_trace(go.Pie(
            labels=fleet_comp["Vehicle Type"], values=fleet_comp["2026"],
            textinfo="label+percent", textposition="inside",
            hole=0.3, showlegend=False), row=1, col=1)
        fig_fleet.add_trace(go.Pie(
            labels=fleet_comp["Vehicle Type"], values=fleet_comp["2030"],
            textinfo="label+percent", textposition="inside",
            hole=0.3, showlegend=False), row=1, col=2)
        fig_fleet.update_layout(height=400, margin=dict(t=40))
        st.plotly_chart(fig_fleet, use_container_width=True)

    with col2:
        st.markdown("**Key Changes to 2030**")
        st.dataframe(
            fleet_comp.style.format({
                "2026": "{:,.0f}",
                "2030": "{:,.0f}",
                "Change": "{:+,.0f}",
                "Change %": "{:+.0f}%",
            }).background_gradient(subset=["Change %"], cmap="RdYlGn"),
            use_container_width=True, hide_index=True,
        )

    st.markdown("---")

    # Side-by-side simulation comparison
    st.subheader("Regime Performance: 2026 vs 2030")
    st.markdown("Run the simulation with the **2030 fleet** (sidebar) to see how each regime's "
                "outcomes shift as the fleet electrifies.")

    if fleet_year == "2030":
        df_2026 = run_sim("2026", demand_response,
                          flat_rate, cong_base, cong_peak_mult, cong_shoulder_mult,
                          cordon_charge, cordon_peak_only,
                          wd_base, carbon_price, congestion_vot,
                          hybrid_base, hybrid_peak, hybrid_weight)

        compare_metric = st.selectbox("Metric to compare",
                                       ["revenue_bn", "congestion_cost_bn", "co2_mt",
                                        "vkt_change_pct", "avg_passenger_charge_per_km"])
        nice_names = {"revenue_bn": "Revenue ($B)", "congestion_cost_bn": "Congestion Cost ($B)",
                      "co2_mt": "CO₂ (Mt)", "vkt_change_pct": "VKT Change (%)",
                      "avg_passenger_charge_per_km": "Avg Car Charge ($/km)"}

        fig_compare = go.Figure()
        fig_compare.add_trace(go.Bar(
            x=df_2026["regime"], y=df_2026[compare_metric],
            name="2026 Fleet", marker_color="rgba(52,152,219,0.6)",
        ))
        fig_compare.add_trace(go.Bar(
            x=df["regime"], y=df[compare_metric],
            name="2030 Fleet", marker_color="rgba(231,76,60,0.6)",
        ))
        fig_compare.update_layout(
            barmode="group", height=450, template="plotly_white",
            yaxis_title=nice_names.get(compare_metric, compare_metric),
            margin=dict(t=30))
        st.plotly_chart(fig_compare, use_container_width=True)
    else:
        st.warning("Select **2030** in the sidebar Fleet Year to enable the comparison view.")

    st.markdown("---")
    st.markdown("""
    **The cost of inaction compounds.** Every year that passes:
    - Fuel excise revenue falls ~$0.5-0.8B as EV share grows
    - Road maintenance costs rise with traffic growth and asset aging
    - Congestion worsens — BITRE projects costs reaching $40B by 2040
    - The political difficulty of reform increases as more EVs are on the road
      and more voters expect to continue paying zero road-use charges

    A regime that looks only marginally better today may represent **billions
    in cumulative benefit** over a decade.
    """)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 6: RAW DATA
# ═══════════════════════════════════════════════════════════════════════════
with tab_data:
    st.subheader("Simulation Parameters")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Fleet Data**")
        fleet_df = pd.DataFrame([
            {"Type": v["label"], "Count": v["count"],
             "Avg Mass (t)": v["avg_mass_t"],
             "Avg VKT/yr": v["avg_vkt_pa"],
             "Fuel (L/100km)": v["fuel_l_per_100km"],
             "CO₂ (g/km)": v["co2_g_per_km"],
             "Elasticity": v["elasticity_price"]}
            for v in FLEET.values()
        ])
        st.dataframe(fleet_df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**Road Network**")
        road_df = pd.DataFrame([
            {"Type": v["label"],
             "Lane-km": v["total_lane_km"],
             "Free-flow (km/h)": v["free_flow_speed_kmh"],
             "VKT Share": f"{v['share_national_vkt']:.0%}",
             "Congestion": v["congestion_profile"]}
            for v in ROAD_NETWORK.values()
        ])
        st.dataframe(road_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**Externality Cost Parameters**")
    ext_df = pd.DataFrame([
        {"Parameter": k.replace("_", " ").title(), "Value": f"${v:.2f}"}
        for k, v in EXTERNALITY_COSTS.items()
    ])
    st.dataframe(ext_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Full Simulation Results")
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False)
    st.download_button("Download results as CSV", csv, "simulation_results.csv", "text/csv")

    st.markdown("---")
    st.subheader("Hourly Demand Profile")
    fig_demand = go.Figure()
    hours = list(range(24))
    fig_demand.add_trace(go.Bar(
        x=hours, y=HOURLY_DEMAND_PROFILE,
        marker_color=["#e74c3c" if h in [7, 8, 16, 17] else
                       "#e67e22" if h in [6, 9, 10, 15, 18, 19] else
                       "#3498db" for h in hours],
    ))
    fig_demand.update_layout(
        height=300, template="plotly_white",
        xaxis_title="Hour of Day", yaxis_title="Share of Daily VKT",
        xaxis=dict(tickmode="linear", dtick=1),
        annotations=[
            dict(x=7.5, y=max(HOURLY_DEMAND_PROFILE) * 1.05,
                 text="AM Peak", showarrow=False, font=dict(color="#e74c3c")),
            dict(x=16.5, y=max(HOURLY_DEMAND_PROFILE) * 1.05,
                 text="PM Peak", showarrow=False, font=dict(color="#e74c3c")),
        ],
        margin=dict(t=30))
    st.plotly_chart(fig_demand, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #7f8c8d; font-size: 0.9em;'>"
    "Australian Road Pricing Simulation | "
    "Data: ABS, BITRE, ATAP, NTC, DCCEEW | "
    "Theory: Pigou, Vickrey, Ramsey, Lipsey & Lancaster, Henry Review | "
    "Values in 2024 AUD"
    "</div>",
    unsafe_allow_html=True,
)
