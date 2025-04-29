# https://pure.tue.nl/ws/portalfiles/portal/21167267/1_s2.0_S1878029614001819_main.pdf
# https://ny.eater.com/2024/5/9/24151420/price-of-coffee-nyc-latte-cold-brew
# https://thelocavore.com/article/what-does-it-cost-to-open-and-operate-a-shop
# https://therealdeal.com/magazine/new-york-may-2017/nyc-neighborhoods-by-the-foot/

from get_neighborhood import get_neighborhoods
import gurobipy as gp
from gurobipy import GRB
import pandas as pd

pedestrian_counts_url = "https://gist.githubusercontent.com/JoshBong/d83569f9837962d98b2c16d2312ed2d2/raw"
neighborhoods_url = "https://gist.githubusercontent.com/JoshBong/5e6697ffa29f3db776254188a5aea8fb/raw/6621a3cf7fcde270097be79a1b5fe5c5716ae618/gistfile1.txt"

df = get_neighborhoods(pedestrian_counts_url, neighborhoods_url)

# Extract all unique day identifiers (e.g., May07, Oct07)
prefixes = set(col.split('_')[0] for col in df.columns if any(x in col for x in ['AM', 'MD', 'PM']))

# For each day, sum the AM, MD, and PM counts to get a daily total
for prefix in prefixes:
    try:
        df[f"{prefix}_total"] = df[f"{prefix}_AM"] + df[f"{prefix}_MD"] + df[f"{prefix}_PM"]
    except KeyError:
        # In case a day is missing one of the columns, skip it
        continue

# Collect all daily total columns we just created
daily_total_cols = [col for col in df.columns if col.endswith("_total")]

# Drop rows with missing daily totals (i.e., incomplete days)
df_cleaned = df.dropna(subset=daily_total_cols)

# Now calculate the average daily count per location
df_cleaned['daily_avg'] = df_cleaned[daily_total_cols].mean(axis=1)

# Optional: filter outliers (remove top/bottom 5% of daily averages)
lower_bound = df_cleaned['daily_avg'].quantile(0.05)
upper_bound = df_cleaned['daily_avg'].quantile(0.95)
filtered_df = df_cleaned[(df_cleaned['daily_avg'] >= lower_bound) & (df_cleaned['daily_avg'] <= upper_bound)]

# Group by location and compute the average of daily averages
avg_by_location = filtered_df.groupby('Loc')['daily_avg'].mean().sort_values(ascending=False)

# Print results
print("Average daily pedestrian count per location (after grouping by day and removing outliers):\n")
for loc, avg in avg_by_location.items():
    print(f"Location {loc}: {avg:.2f} pedestrians/day")

# Best location
best_loc = avg_by_location.idxmax()
print(f"\n Best location: Location {best_loc} with average {avg_by_location[best_loc]:.2f} pedestrians/day")







# model = gp.Model("CoffeeShopOptimization")

# # Decision variables
# x = model.addVars(hours, vtype=GRB.BINARY, name="open")          # Whether open
# s = model.addVars(hours, vtype=GRB.INTEGER, lb=0, ub=4, name="staff")  # Staff count

# # Objective: Maximize profit
# revenue = gp.quicksum(r * 0.1 * pt[i] * x[h] for i, h in enumerate(hours))
# labor_cost = gp.quicksum(s[h] * w for h in hours)
# model.setObjective(revenue - labor_cost, GRB.MAXIMIZE)

# # Constraints
# for i, h in enumerate(hours):
#     model.addConstr(s[h] >= x[h], f"min_staff_if_open_{h}")
#     model.addConstr(s[h] >= 0.2 * pt[i] * x[h], f"staffing_ratio_{h}")
# model.addConstr(labor_cost <= budget, "budget")

# # Ensure at least one 8-hour uninterrupted open period
# block_start_hours = hours[:len(hours) - 7]
# model.addConstr(
#     gp.quicksum(
#         gp.min_([x[h + offset] for offset in range(8)])
#         for h in block_start_hours
#     ) >= 1,
#     "8_hour_block"
# )

# model.optimize()

# # Output
# if model.status == GRB.OPTIMAL:
#     print("\nOptimal Solution Found:")
#     print(f"Total Revenue: ${revenue.getValue():.2f}")
#     print(f"Total Labor Cost: ${labor_cost.getValue():.2f}")
#     print(f"Profit: ${model.objVal:.2f}\n")
#     print("Optimal Schedule:")
#     for i, h in enumerate(hours):
#         if x[h].X > 0.5:
#             ampm = "AM" if h < 12 else "PM"
#             hour = h if h < 13 else h - 12
#             print(f"{hour}{ampm}: {int(s[h].X)} staff (Pedestrians: {int(pt[i])})")
# else:
#     print("No optimal solution found.")
