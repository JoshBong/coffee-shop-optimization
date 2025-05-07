from get_neighborhood import get_neighborhoods
import gurobipy as gp
from gurobipy import GRB
import pandas as pd

# ======================================
# 1. Data Preparation
# ======================================

def prepare_data(pedestrian_url, neighborhoods_url):
    """Load and preprocess the data"""
    df = get_neighborhoods(pedestrian_url, neighborhoods_url)
    
    # Calculate daily totals
    prefixes = set(col.split('_')[0] for col in df.columns if any(x in col for x in ['AM', 'MD', 'PM']))
    for prefix in prefixes:
        try:
            df[f"{prefix}_total"] = df[f"{prefix}_AM"] + df[f"{prefix}_MD"] + df[f"{prefix}_PM"]
        except KeyError:
            continue
    
    # Clean data
    daily_total_cols = [col for col in df.columns if col.endswith("_total")]
    df_cleaned = df.dropna(subset=daily_total_cols)
    df_cleaned['daily_avg'] = df_cleaned[daily_total_cols].mean(axis=1)
    
    # Filter outliers
    lower_bound = df_cleaned['daily_avg'].quantile(0.05)
    upper_bound = df_cleaned['daily_avg'].quantile(0.95)
    filtered_df = df_cleaned[(df_cleaned['daily_avg'] >= lower_bound) & 
                           (df_cleaned['daily_avg'] <= upper_bound)]
    
    # Convert monthly rent to daily (critical fix)
    filtered_df['rent_per_sqft_daily'] = filtered_df['rent_per_sqft'] / 30
    
    return filtered_df

# ======================================
# 2. Optimization Model
# ======================================

def optimize_coffee_shops(df, day='May07'):
    """Optimize coffee shop locations for maximum daily profit"""
    
    # Parameters (using your specified values)
    shop_size = 800  # sqft
    profit_per_customer = 5  # $ per customer (after COGS)
    staff_cost_per_shift = 80  # $ per shift
    electricity_cost = 0.125  # $ per sqft per day
    
    # Time-specific conversion rates (using your 10% for all periods)
    conversion_rates = {'AM': 0.08, 'MD': 0.08, 'PM': 0.08}
    
    # Select top 20 locations for optimization
    time_cols = [f'{day}_{t}' for t in ['AM', 'MD', 'PM']]
    candidate_locs = df.groupby('Loc')[time_cols + ['rent_per_sqft_daily']].mean()
    candidate_locs = candidate_locs.nlargest(20, time_cols).copy()
    
    # Create model
    model = gp.Model("CoffeeShopOptimization")
    
    # Decision variables
    x = model.addVars(candidate_locs.index, vtype=GRB.BINARY, name="open_shop")
    y = model.addVars(candidate_locs.index, ['AM', 'MD', 'PM'], 
                     vtype=GRB.BINARY, name="operate_time")
    
    # Objective function: Maximize daily profit
    profit = gp.QuadExpr()
    for loc in candidate_locs.index:
        # Costs (now using daily rent)
        rent_cost = x[loc] * candidate_locs.loc[loc, 'rent_per_sqft_daily'] * shop_size
        utility_cost = electricity_cost * shop_size * gp.quicksum(y[loc,t] for t in ['AM', 'MD', 'PM'])
        staff_cost = staff_cost_per_shift * gp.quicksum(y[loc,t] for t in ['AM', 'MD', 'PM'])
        
        # Revenue
        revenue = gp.quicksum(
            y[loc,t] * conversion_rates[t] * candidate_locs.loc[loc, f'{day}_{t}'] * profit_per_customer
            for t in ['AM', 'MD', 'PM']
        )
        
        profit += (revenue - rent_cost - utility_cost - staff_cost)
    
    model.setObjective(profit, GRB.MAXIMIZE)
    
    # Constraints
    # 1. Can only operate if shop is open
    model.addConstrs((y[loc,t] <= x[loc] for loc in candidate_locs.index for t in ['AM', 'MD', 'PM']), 
                    name="operation_requires_open")
    
    # 2. Must open at least one shop
    model.addConstr(gp.quicksum(x[loc] for loc in candidate_locs.index) >= 1, 
                   name="open_at_least_one")
    
    # 3. Must operate during at least two time periods if open
    for loc in candidate_locs.index:
        model.addConstr(gp.quicksum(y[loc,t] for t in ['AM', 'MD', 'PM']) >= 2 * x[loc],
                       name=f"min_operating_hours_{loc}")
    
    # Solve
    model.optimize()
    
    # Process and return results
    if model.status == GRB.OPTIMAL:
        results = []
        for loc in candidate_locs.index:
            if x[loc].X > 0.5:
                operating_times = [t for t in ['AM', 'MD', 'PM'] if y[loc,t].X > 0.5]
                
                # Calculate components
                traffic = {t: candidate_locs.loc[loc, f'{day}_{t}'] for t in ['AM', 'MD', 'PM']}
                customers = sum(conversion_rates[t] * traffic[t] for t in operating_times)
                revenue = customers * profit_per_customer
                rent_cost = candidate_locs.loc[loc, 'rent_per_sqft_daily'] * shop_size
                staff_cost = staff_cost_per_shift * len(operating_times)
                utility_cost = electricity_cost * shop_size * len(operating_times)
                
                results.append({
                    'Location': loc,
                    'Rent ($/sqft monthly)': candidate_locs.loc[loc, 'rent_per_sqft_daily'] * 30,
                    'Daily Rent': rent_cost,
                    'Daily Staff': staff_cost,
                    'Daily Utilities': utility_cost,
                    'Operating Times': ', '.join(operating_times),
                    'Daily Customers': int(customers),
                    'Daily Revenue': revenue,
                    'Daily Profit': revenue - rent_cost - staff_cost - utility_cost,
                    'AM Traffic': int(traffic['AM']),
                    'MD Traffic': int(traffic['MD']),
                    'PM Traffic': int(traffic['PM'])
                })
        
        results_df = pd.DataFrame(results).sort_values('Daily Profit', ascending=False)
        return results_df.round(2)
    else:
        print("No optimal solution found")
        return None

# ======================================
# 3. Execute the Analysis
# ======================================

if __name__ == "__main__":
    # Load and prepare data
    pedestrian_url = "https://gist.githubusercontent.com/JoshBong/d83569f9837962d98b2c16d2312ed2d2/raw"
    neighborhoods_url = "https://gist.githubusercontent.com/JoshBong/5e6697ffa29f3db776254188a5aea8fb/raw/6621a3cf7fcde270097be79a1b5fe5c5716ae618/gistfile1.txt"
    
    df_processed = prepare_data(pedestrian_url, neighborhoods_url)
    
    # Print pedestrian statistics
    avg_by_location = df_processed.groupby('Loc')['daily_avg'].mean().sort_values(ascending=False)
    print("Average daily pedestrian count per location (after grouping by day and removing outliers):\n")
    for loc, avg in avg_by_location.items():
        print(f"Location {loc}: {avg:.2f} pedestrians/day")
    
    best_loc = avg_by_location.idxmax()
    print(f"\nBest location by traffic: Location {best_loc} with average {avg_by_location[best_loc]:.2f} pedestrians/day")
    
    # Run optimization
    print("\nRunning optimization...")
    results = optimize_coffee_shops(df_processed)
    
    if results is not None:
        print("\nOptimal Coffee Shop Locations:\n")
        print(results[['Location', 'Rent ($/sqft monthly)', 'Daily Profit', 'Operating Times', 
                      'Daily Customers', 'Daily Revenue', 'Daily Rent', 'Daily Staff']].to_string(index=False))
        
        best_loc = results.iloc[0]
        print(f"\n🌟 Best Location: {best_loc['Location']}")
        print(f"   Daily Profit: ${best_loc['Daily Profit']:,.2f}")
        print(f"   Monthly Rent: ${best_loc['Rent ($/sqft monthly)'] * 800:,.2f} (${best_loc['Rent ($/sqft monthly)']:.2f}/sqft)")
        print(f"   Operating Hours: {best_loc['Operating Times']}")
        print(f"   Daily Customers: {best_loc['Daily Customers']}")
        print(f"   Daily Revenue: ${best_loc['Daily Revenue']:,.2f}")