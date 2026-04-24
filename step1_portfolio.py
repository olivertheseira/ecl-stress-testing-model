import pandas as pd
import numpy as np

np.random.seed(42)

NUM_LOANS = 500

sectors = [
    "Oil & Gas", "Real Estate", "Manufacturing",
    "Retail", "Construction", "Financial Services", "Healthcare"
]

stages = [1, 2, 3]
stage_weights = [0.70, 0.20, 0.10]  # 70% performing, 20% watch, 10% defaulted

# --- Internal rating grades (1=best, 8=worst, mimics Basel scale) ---
rating_grades = [1, 2, 3, 4, 5, 6, 7, 8]

portfolio = pd.DataFrame({
    "loan_id": [f"LN{str(i).zfill(4)}" for i in range(1, NUM_LOANS + 1)],

    "sector": np.random.choice(sectors, NUM_LOANS),

    "stage": np.random.choice(stages, NUM_LOANS, p=stage_weights),

    # Exposure at Default (EAD): loan outstanding balance in RM thousands
    # Skewed right — most loans are smaller, a few are large
    "ead": np.round(np.random.lognormal(mean=6.5, sigma=1.2, size=NUM_LOANS), 2),

    # Rating grade — worse ratings more common in Stage 2/3
    "rating_grade": np.random.choice(rating_grades, NUM_LOANS,
                                      p=[0.05, 0.10, 0.20, 0.25, 0.20, 0.10, 0.07, 0.03]),

    # Remaining tenor in years
    "tenor_years": np.round(np.random.uniform(0.5, 7.0, NUM_LOANS), 1),

    # Collateral coverage ratio (1.0 = fully covered, 0.0 = unsecured)
    "collateral_ratio": np.round(np.random.uniform(0.0, 1.5, NUM_LOANS), 2),
})

portfolio["lgd"] = np.clip(0.45 - (portfolio["collateral_ratio"] * 0.25), 0.10, 0.90)
portfolio["lgd"] = portfolio["lgd"].round(4)

print("=" * 60)
print("PORTFOLIO GENERATED SUCCESSFULLY")
print("=" * 60)
print(f"Total loans:          {len(portfolio)}")
print(f"Total EAD (RM '000):  {portfolio['ead'].sum():,.0f}")
print()
print("Stage Distribution:")
print(portfolio["stage"].value_counts().sort_index()
      .rename({1: "Stage 1 (Performing)", 2: "Stage 2 (Watch)", 3: "Stage 3 (Default)"}))
print()
print("Sector Distribution:")
print(portfolio["sector"].value_counts())
print()
print("Sample rows:")
print(portfolio.head(10).to_string(index=False))

portfolio.to_csv("portfolio.csv", index=False)
print()
print("Saved to portfolio.csv — ready for Step 2.")
