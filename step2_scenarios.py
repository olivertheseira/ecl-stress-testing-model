# ============================================================
# ECL STRESS TESTING MODEL
# Step 2: Define Macroeconomic Scenarios & Map to PD
# ============================================================

import pandas as pd
import numpy as np

# --- Load portfolio from Step 1 ---
portfolio = pd.read_csv("portfolio.csv")
print(f"Portfolio loaded: {len(portfolio)} loans\n")

# ============================================================
# PART A: DEFINE MACROECONOMIC SCENARIOS
# GDP Growth Rate (%) and Unemployment Rate (%) are used as the MEVs
# ============================================================

scenarios = {
    "Optimistic": {
        "probability":    0.25,   # 25% chance this scenario plays out
        "gdp_growth":     4.5,    # Strong growth
        "unemployment":   3.2,    # Low unemployment
        "description":   "Benign economic conditions, above-trend growth"
    },
    "Base": {
        "probability":    0.55,   # Most likely scenario (55%)
        "gdp_growth":     2.8,
        "unemployment":   4.1,
        "description":   "Moderate growth, stable labour market"
    },
    "Adverse": {
        "probability":    0.20,   # Tail risk scenario (20%)
        "gdp_growth":    -1.5,    # Mild recession
        "unemployment":   7.0,    # Rising unemployment
        "description":   "Economic contraction, stress in labour market"
    }
}

# Verify probabilities sum to 1 (this is a model integrity check)
total_prob = sum(s["probability"] for s in scenarios.values())
assert abs(total_prob - 1.0) < 0.001, "Scenario probabilities must sum to 1.0"
print("Scenario probabilities validated (sum to 1.0) ✓\n")

# Preview scenarios
print("=" * 60)
print("MACROECONOMIC SCENARIOS")
print("=" * 60)
for name, params in scenarios.items():
    print(f"\n{name} (Probability: {params['probability']*100:.0f}%)")
    print(f"  GDP Growth:    {params['gdp_growth']}%")
    print(f"  Unemployment:  {params['unemployment']}%")
    print(f"  Description:   {params['description']}")

# ============================================================
# PART B: BASE PD BY RATING GRADE
# ============================================================
# These are the through-the-cycle (TTC) PDs assigned to each
# internal rating grade.
# ============================================================

base_pd = {
    1: 0.0010,   # AAA equivalent — near-zero default risk
    2: 0.0025,
    3: 0.0060,
    4: 0.0130,
    5: 0.0280,
    6: 0.0550,
    7: 0.1100,
    8: 0.2000    # CCC equivalent — high default risk
}

# ============================================================
# PART C: SCENARIO PD MULTIPLIERS
# ============================================================
# Adjust base PDs upward or downward depending on the
# macroeconomic scenario. This is the MEV linkage —
# the core of forward-looking IFRS 9 ECL modelling.
#
# Multiplier > 1.0 = worse conditions → higher PD
# Multiplier < 1.0 = better conditions → lower PD
#
# In a real model, these multipliers come from regression
# analysis linking MEVs to historical default rates.
# Here it is derived from the GDP and unemployment inputs
# using a simplified but directionally correct approach.
# ============================================================

def calculate_pd_multiplier(gdp_growth, unemployment,
                             base_gdp=2.8, base_unemp=4.1):
    """
    Calculate a PD scalar based on deviation of MEVs from base.
    
    Logic:
    - Each 1% drop in GDP below base → PD increases ~15%
    - Each 1% rise in unemployment above base → PD increases ~10%
    - Effects are additive and then exponentiated for realism
    """
    gdp_effect   = (base_gdp - gdp_growth) * 0.15
    unemp_effect = (unemployment - base_unemp) * 0.10
    multiplier   = np.exp(gdp_effect + unemp_effect)
    return round(multiplier, 4)

# Calculate multipliers for each scenario
print("\n\n" + "=" * 60)
print("PD MULTIPLIERS BY SCENARIO")
print("=" * 60)

scenario_multipliers = {}
for name, params in scenarios.items():
    mult = calculate_pd_multiplier(params["gdp_growth"],
                                   params["unemployment"])
    scenario_multipliers[name] = mult
    print(f"{name:12}: {mult:.4f}x  "
          f"({'↑ higher PD' if mult > 1 else '↓ lower PD' if mult < 1 else 'unchanged'})")

# ============================================================
# PART D: APPLY SCENARIO PDs TO PORTFOLIO
# ============================================================

results = []

for scenario_name, params in scenarios.items():
    multiplier = scenario_multipliers[scenario_name]

    df = portfolio.copy()
    df["scenario"] = scenario_name
    df["scenario_probability"] = params["probability"]
    df["pd_multiplier"] = multiplier

    # Apply scenario adjustment to base PD
    # Cap PD at 99% (Stage 3 loans approaching certain default)
    df["base_pd"]     = df["rating_grade"].map(base_pd)
    df["scenario_pd"] = (df["base_pd"] * multiplier).clip(upper=0.99).round(6)

    results.append(df)

# Combine all scenarios
all_scenarios = pd.concat(results, ignore_index=True)

# ============================================================
# PART E: SUMMARY OUTPUT
# ============================================================

print("\n\n" + "=" * 60)
print("PORTFOLIO AVERAGE PD BY SCENARIO")
print("=" * 60)

summary = all_scenarios.groupby("scenario").agg(
    avg_base_pd    = ("base_pd", "mean"),
    avg_scenario_pd= ("scenario_pd", "mean"),
    total_ead      = ("ead", "sum")
).round(4)

# Sort logically
summary = summary.loc[["Optimistic", "Base", "Adverse"]]
print(summary.to_string())

print("\n\n" + "=" * 60)
print("AVERAGE SCENARIO PD BY STAGE")
print("=" * 60)

stage_summary = all_scenarios.groupby(
    ["scenario", "stage"])["scenario_pd"].mean().round(4).unstack("scenario")
stage_summary = stage_summary[["Optimistic", "Base", "Adverse"]]
stage_summary.index = ["Stage 1 (Performing)",
                        "Stage 2 (Watch)",
                        "Stage 3 (Default)"]
print(stage_summary.to_string())

# --- Save for Step 3 ---
all_scenarios.to_csv("portfolio_with_pd.csv", index=False)
print("\n\nSaved to portfolio_with_pd.csv — ready for Step 3.")
print("(This file contains all 500 loans × 3 scenarios = 1,500 rows)")
