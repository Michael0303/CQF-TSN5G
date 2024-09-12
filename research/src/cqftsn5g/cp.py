from cqftsn5g.modules.UserTxParams import TxMode, UserTxParams
from cqftsn5g.modules.Models import Flow, Link
from cqftsn5g.modules.NRAmc import CarrierInfo, SlotFormat
from ortools.sat.python import cp_model
from cqftsn5g.calculate_rbs import req_rbs


def cp_sat_scheduling(
    f_tt: list[Flow],
    f_avb: list[Flow],
    l_TSN: list[Link],
    l_5G: list[Link],
    HYPER_CYCLE: float,
    INTERVAL_TIME: float,
    TTI: float,
    mu: int,
    U_TSN: float,
    B_TSN: float,
    U_5G: float,
    NUM_BANDS: int,
    sf: SlotFormat,
):
    model = cp_model.CpModel()
    N = HYPER_CYCLE / INTERVAL_TIME
    flows = f_tt + f_avb
    links = l_TSN + l_5G

    # C1: Scheduling variable
    phi = {}
    for i, flow in enumerate(flows):
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            phi[i, m] = model.NewIntVar(0, N, f"phi_{i}_{m}")

    # C2: Flow scheduling constraint
    for i, flow in enumerate(flows):
        is_scheduled = model.NewBoolVar(f"is_scheduled_{i}")
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            model.Add(phi[i, m] > 0).OnlyEnforceIf(is_scheduled)
            model.Add(phi[i, m] == 0).OnlyEnforceIf(is_scheduled.Not())

    # C3: Interval constraint
    for i, flow in enumerate(flows):
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            model.Add((m - 1) * flow.period / INTERVAL_TIME < phi[i, m]).OnlyEnforceIf(
                phi[i, m] != 0
            )
            model.Add(phi[i, m] <= m * flow.period / INTERVAL_TIME).OnlyEnforceIf(phi[i, m] != 0)

    # C4: Decision variable
    chi = {}
    for i, flow in enumerate(flows):
        for k in range(1, N + 1):
            for link in links:
                chi[i, link, k] = 0

    for i, flow in enumerate(flows):
        for k in range(0, flow.hops):
            chi[i, flow.path[k], k + 1] = 1

    # C5: Latency requirement
    for i, flow in enumerate(flows):
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            if phi[i, m] != 0:
                model.Add(
                    (phi[i, m] - 1) * INTERVAL_TIME
                    - (m - 1) * flow.period
                    + INTERVAL_TIME * (flow.hops + 1)
                    <= flow.latency
                )

    # C6: Throughput requirement
    for i in f_avb:
        for link in l_5G:
            model.Add(
                sum(1 for k in range(1, N + 1) if chi[i, link, k] == 1)
                >= flow.bandwidth / flow.payload
            )

    # C7: TSN capacity limit
    def overhead(payload):
        header = 33
        return payload + header

    for k in range(1, N + 1):
        for link in l_TSN:
            model.Add(
                sum(overhead(flow.payload) for flow in flows if chi[i, link, k] == 1)
                <= U_TSN * B_TSN * INTERVAL_TIME
            )

    # slotFormat = SlotFormat(
    #     tdd=True,
    #     numDlSymbols=6,
    #     numUlSymbols=6,
    #     numFlexSymbols=2,
    # )

    carrierInfo = CarrierInfo(
        carrierFrequency=5.9,
        numBands=NUM_BANDS,
        firstBand=0,
        lastBand=NUM_BANDS - 1,
        bandLimit=[],
        numerologyIndex=mu,
        slotFormat=sf,
    )

    # C9: 5G capacity limit
    for k in range(1, N + 1):
        for link in l_5G:
            model.Add(
                sum(
                    req_rbs(flow.path.cqi, carrierInfo, flow.payload)
                    for i, flow in enumerate(flows)
                    if chi[i, link, k] == 1
                )
                <= U_5G * NUM_BANDS * INTERVAL_TIME / TTI
            )

    # Objective 1: Maximize schedulable flows
    scheduled_flows = sum(phi[i, 1] >= 0 for i, flow in enumerate(flows))
    # Objective 2: Load balance
    load = []
    for k in range(1, N + 1):
        load[k] = sum(flow.payload for flow in flows if chi[i, l_5G[0], k] == 1)
    max_load = max(load)

    weight_1 = 0.5
    weight_2 = 0.5
    model.Maximize(weight_1 * scheduled_flows - weight_2 * max_load)

    # Create and solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Solution found:")
        for i, flow in enumerate(flows):
            for m in range(1, HYPER_CYCLE // flow.period + 1):
                print(f"phi({i}, {m}) = {solver.Value(phi[i, m])}")

    else:
        print("No solution found.")
