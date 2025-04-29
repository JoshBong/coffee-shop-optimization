import gurobipy as gp
from gurobipy import GRB

def hw4():

    #intitializing vars
    time = [8, 12, 13, 11, 9, 7, 8, 8]
    labor = [6, 5, 4, 7, 8, 3, 4, 5]
    cranes = [1, 0, 1, 0, 0, 1, 1, 1]
    #diff profits for q2
    profit1 = [80, 110, 100, 90, 70, 80, 90, 60]
    profit2 = [70, 140, 50, 30, 80, 90, 60, 40]
    profit3 = [100, 80, 80, 70, 100, 110, 80, 50]

    #initializing model
    model = gp.Model('hw4')

    #binary variable to pick projects
    x = model.addVars(8, vtype=GRB.BINARY, name='projects')
    #placeholder for variable for min profit
    y = model.addVar(name='min_profit')

    #constraints for each scenario
    model.addConstr(y <= sum(profit1[i] * x[i] for i in range(8)), name='scenario_1')
    model.addConstr(y <= sum(profit2[i] * x[i] for i in range(8)), name='scenario_2')
    model.addConstr(y <= sum(profit3[i] * x[i] for i in range(8)), name='scenario_3')

    #overall constraints
    model.addConstr(sum(time[i] * x[i] for i in range(8)) <= 50, name = 'c1')
    model.addConstr(sum(labor[i] * x[i] for i in range(8)) <= 30, name = 'c2')
    model.addConstr(sum(cranes[i] * x[i] for i in range(8)) <= 3, name = 'c3')

    #finding best of the worst case profits
    model.setObjective(y, GRB.MAXIMIZE)
    #optimize model
    model.optimize()

    #print results
    if model.status == GRB.OPTIMAL:
        print("Selected Projects:")
        for i in range(8):
            if x[i].X > 0.5:
                print(f"Project {i+1}")

        profit_s1 = sum(profit1[i] * x[i].X for i in range(8))
        profit_s2 = sum(profit2[i] * x[i].X for i in range(8))
        profit_s3 = sum(profit3[i] * x[i].X for i in range(8))

        print(f"\nScenario 1 Profit: ${profit_s1 * 1000:,.0f}")
        print(f"Scenario 2 Profit: ${profit_s2 * 1000:,.0f}")
        print(f"Scenario 3 Profit: ${profit_s3 * 1000:,.0f}")
        print(f"\nWorst Case Scenario Profit (Maximin): ${y.X * 1000:,.0f}")

    elif model.status == GRB.UNBOUNDED:
        print("The problem is unbounded; no optimal solution exists.")
    else:
        print(f"Optimization terminated with status: {model.status}")


hw4()
