import pandas as pd
import numpy as np

df = pd.read_csv("portfolio_with_pd.csv")
print(f"Loaded {len(df):,} rows (500 loans × 3 scenarios)\n")

def get_ecl_horizon(stage, tenor_years):
    """
    Returns the ECL measurement horizon in years.
    Stage 1: capped at 1 year (12-month ECL)
    Stage 2 & 3: full remaining tenor (lifetime ECL)
    """
    if stage == 1:
        return 1.0
    else:
        return tenor_years   

df["ecl_horizon"] = df.apply(
    lambda row: get_ecl_horizon(row["stage"], row["tenor_years"]), axis=1
)

df["ecl_gross"] = (
    df["scenario_pd"]   
    * df["lgd"]         
    * df["ead"]         
    * df["ecl_horizon"] 
).round(4)

df["ecl_weighted"] = (df["ecl_gross"] * df["scenario_probability"]).round(4)

ecl_final = df.groupby("loan_id").agg(
    sector          = ("sector", "first"),
    stage           = ("stage", "first"),
    ead             = ("ead", "first"),
    lgd             = ("lgd", "first"),
    tenor_years     = ("tenor_years", "first"),
    ecl_horizon     = ("ecl_horizon", "first"),
    rating_grade    = ("rating_grade", "first"),

    ecl_optimistic  = ("ecl_gross",
                       lambda x: x[df.loc[x.index, "scenario"] == "Optimistic"].sum()),
    ecl_base        = ("ecl_gross",
                       lambda x: x[df.loc[x.index, "scenario"] == "Base"].sum()),
    ecl_adverse     = ("ecl_gross",
                       lambda x: x[df.loc[x.index, "scenario"] == "Adverse"].sum()),

    ecl_weighted    = ("ecl_weighted", "sum"),
).reset_index()

ecl_final["ecl_coverage_pct"] = (
    ecl_final["ecl_weighted"] / ecl_final["ead"] * 100
).round(2)

total_ead          = ecl_final["ead"].sum()
total_ecl_base     = ecl_final["ecl_base"].sum()
total_ecl_adverse  = ecl_final["ecl_adverse"].sum()
total_ecl_weighted = ecl_final["ecl_weighted"].sum()

print("=" * 60)
print("PORTFOLIO ECL SUMMARY (RM '000)")
print("=" * 60)
print(f"Total EAD:                    RM {total_ead:>12,.1f}k")
print(f"ECL — Base Scenario:          RM {total_ecl_base:>12,.1f}k")
print(f"ECL — Adverse Scenario:       RM {total_ecl_adverse:>12,.1f}k")
print(f"ECL — Probability Weighted:   RM {total_ecl_weighted:>12,.1f}k")
print(f"ECL Coverage Ratio:           {total_ecl_weighted/total_ead*100:>11.2f}%")

print("\n\n" + "=" * 60)
print("ECL BREAKDOWN BY STAGE (Probability-Weighted, RM '000)")
print("=" * 60)

stage_summary = ecl_final.groupby("stage").agg(
    num_loans       = ("loan_id", "count"),
    total_ead       = ("ead", "sum"),
    total_ecl       = ("ecl_weighted", "sum"),
).round(1)

stage_summary["coverage_pct"] = (
    stage_summary["total_ecl"] / stage_summary["total_ead"] * 100
).round(2)

stage_summary.index = ["Stage 1 (Performing)",
                        "Stage 2 (Watch)",
                        "Stage 3 (Default)"]
stage_summary.columns = ["# Loans", "EAD (RM'000)", "ECL (RM'000)", "Coverage %"]
print(stage_summary.to_string())

print("\n\n" + "=" * 60)
print("ECL BREAKDOWN BY SECTOR (Probability-Weighted, RM '000)")
print("=" * 60)

sector_summary = ecl_final.groupby("sector").agg(
    num_loans   = ("loan_id", "count"),
    total_ead   = ("ead", "sum"),
    total_ecl   = ("ecl_weighted", "sum"),
).round(1)

sector_summary["coverage_pct"] = (
    sector_summary["total_ecl"] / sector_summary["total_ead"] * 100
).round(2)

sector_summary.columns = ["# Loans", "EAD (RM'000)", "ECL (RM'000)", "Coverage %"]
sector_summary = sector_summary.sort_values("ECL (RM'000)", ascending=False)
print(sector_summary.to_string())

print("\n\n" + "=" * 60)
print("SCENARIO SENSITIVITY ANALYSIS")
print("=" * 60)

stress_uplift    = total_ecl_adverse - total_ecl_base
stress_uplift_pct = stress_uplift / total_ecl_base * 100

print(f"Base Scenario ECL:            RM {total_ecl_base:>10,.1f}k")
print(f"Adverse Scenario ECL:         RM {total_ecl_adverse:>10,.1f}k")
print(f"Stress Uplift (absolute):     RM {stress_uplift:>10,.1f}k")
print(f"Stress Uplift (%):            {stress_uplift_pct:>10.1f}%")
print(f"\nInterpretation: In an adverse scenario, portfolio ECL")
print(f"would increase by {stress_uplift_pct:.1f}% relative to base — representing")
print(f"RM {stress_uplift:,.1f}k of additional expected losses.")

ecl_final.to_csv("ecl_results.csv", index=False)
df.to_csv("ecl_by_scenario.csv", index=False)  

print("\n\nSaved:")
print("  ecl_results.csv      — 500 loans with weighted ECL (for dashboard)")
print("  ecl_by_scenario.csv  — 1,500 rows with scenario detail (for drill-down)")
print("\nReady for Step 4: Power BI Dashboard.")