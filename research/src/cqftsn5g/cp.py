from ortools.sat.python import cp_model

model = cp_model.CpModel()

# Define the constants and parameters
# Flows
F_TT = [...]
F_AVB = [...]
F = F_TT + F_AVB
H_c = 
T_i = {f: ... for f in F}  # Period of each flow
N = 10
T_c = 
Path_i = [{
    'src': 'E1',
    'links': [1, 2, 3],
    'dst': 'E2'
}]
hops = {f: ... for f in F}  # Number of hops for each flow
D_i = {f: ... for f in F}  # Deadline for each flow
J_i = {f: ... for f in F}  # Jitter for each flow
R_i = {f: ... for f in F}  # Rate for each AVB flow
S_i = {f: ... for f in F}  # Size of each flow
U_TSN = 0.8  # Utilization limit for TSN
B_TSN = 1000  # Bandwidth for TSN
U_5G = 0.8  # Utilization limit for 5G
numBands = 50  # Number of bands per TTI
REQ_RB = lambda S, CQI: ...  # Resource block requirement function
CQI_i = {f: ... for f in F}  # Channel Quality Indicator for each flow

# Links
L_TSN = [...]  # List of TSN links
L_5G = [...]  # List of 5G links
L = L_TSN + L_5G  # All links


# C1: Scheduling variable
phi = {}
for i in F:
    for m in range(1, H_c // T_i[i] + 1):
        phi[i, m] = model.NewIntVar(-1, N, f"phi_{i}_{m}")

# C2: Flow scheduling constraint
for i in F:
    is_scheduled = model.NewBoolVar(f'is_scheduled_{i}')
    for m in range(1, H_c // T_i[i] + 1):
        model.Add(phi[i, m] > 0).OnlyEnforceIf(is_scheduled)
        model.Add(phi[i, m] == -1).OnlyEnforceIf(is_scheduled.Not())
      
# C3: Interval constraint
for i in F:
    for m in range(1, H_c // T_i[i] + 1):
        model.Add((m - 1) * T_i[i] / T_c < phi[i, m]).OnlyEnforceIf(phi[i, m] != -1)
        model.Add(phi[i, m] <= m * T_i[i] / T_c).OnlyEnforceIf(phi[i, m] != -1)

# C4: Decision variable
chi = {}
for i in F:
    for k in range(1, N + 1):
        for l in L:
            chi[i, l, k] = 0
            
for i in F:
    for k in range(1, hops[i] + 1):
        chi[i, Path_i[i]['link'][k] , k] = 1

# C5: Latency requirement
for i in F:
    for m in range(1, H_c // T_i[i] + 1):
        if phi[i, m] != -1:
            model.Add((phi[i, m] - 1) * T_c - (m - 1) * T_i[i] + T_c * (hops[i] + 1) <= D_i[i])

# # C6: Jitter requirement
# for i in F_TT:
#     model.Add(2 * T_c <= J_i[i])

# C7: Throughput requirement
for i in F_AVB:
    for l in L_5G:
        model.Add(sum(1 for k in range(1, N + 1) if chi[i, l, k] == 1) >= R_i[i] / S_i[i])

# # C8: TSN capacity limit
# for k in range(1, N + 1):
#     for l in L_TSN:
#         model.Add(sum(S_i[i] for i in F if chi[i, l, k] == 1) <= U_TSN * B_TSN * T_c)

# C9: 5G capacity limit
for k in range(1, N + 1):
    for l in L_5G:
        model.Add(sum(REQ_RB(S_i[i], CQI_i[i]) for i in F if chi[i, l, k] == 1) <= U_5G * numBands * T_c)

# Objective 1: Maximize schedulable flows
scheduled_flows = sum(phi[i, 1] >= 0 for i in F)
# Objective 2: Load balance 
load = []
for k in range(1, N + 1):
    load[k] = sum(S_i[i] for i in F if chi[i, L_5G, k] == 1)
max_load = max(load)

weight_1 = 0.5
weight_2 = 0.5
model.Maximize(weight_1 * scheduled_flows - weight_2 * max_load)

# Create and solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print('Solution found:')
    for i in F:
        for m in range(1, H_c // T_i[i] + 1):
            print(f'phi({i}, {m}) = {solver.Value(phi[i, m])}')
    
    # Calculate chi from phi
    chi = {}
    for i in F:
        for k in range(1, N + 1):
            for l in L:
                chi[i, l, k] = 0
                if any(solver.Value(phi[i, m]) == k for m in range(1, H_c // T_i[i] + 1)):
                    chi[i, l, k] = 1
                if chi[i, l, k] == 1:
                    print(f'chi({i}, {l}, {k}) = 1')
else:
    print('No solution found.')
