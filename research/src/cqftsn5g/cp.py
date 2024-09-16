import math
from cqftsn5g.modules.Models import Flow, Link, Path
from cqftsn5g.modules.NRAmc import CarrierInfo, Direction, SlotFormat
from ortools.sat.python import cp_model
from cqftsn5g.calculate_rbs import req_rbs


def cp_sat_scheduling(
    f_tt: list[Flow],
    f_avb: list[Flow],
    l_TSN: list[Link],
    l_5G: list[Link],
    Paths: dict[str, Path],
    HYPER_CYCLE: int,
    INTERVAL_TIME: int,
    mu: int,
    U_TSN: float,
    B_TSN: float,
    U_5G: float,
    NUM_BANDS: int,
    sf: SlotFormat,
):
    model = cp_model.CpModel()
    N = HYPER_CYCLE // INTERVAL_TIME
    flows = f_tt + f_avb
    links = l_TSN + l_5G
    TTI = 1000 / 2**mu
    print(f"N = {N}")
    print(f"TTI = {TTI}")

    UL_flows = [flow for flow in flows if Paths[flow.path].direction == "UL"]
    DL_flows = [flow for flow in flows if Paths[flow.path].direction == "DL"]

    scheduled = {
        i: {
            m: {
                link.name: {
                    k: model.NewBoolVar(f"schedule_{i}_{m}_{link.name}_{k}")
                    for k in range(1, N + 1)
                }
                for link in links
            }
            for m in range(1, HYPER_CYCLE // flow.period + 1)
        }
        for i, flow in enumerate(flows)
    }

    # C1: Scheduling variable
    phi = {
        (i, m): model.NewIntVar(0, N, f"phi_{i}_{m}")
        for i, flow in enumerate(flows)
        for m in range(1, HYPER_CYCLE // flow.period + 1)
    }

    # C4: Decision variable
    for i, flow in enumerate(flows):
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            for hop in range(Paths[flow.path].hops):
                link = Paths[flow.path].links[hop]
                for time in range(1, N + 1 - hop):
                    model.Add(phi[i, m] == time).OnlyEnforceIf(
                        scheduled[i][m][link.name][time + hop]
                    )
                    model.Add(phi[i, m] != time).OnlyEnforceIf(
                        scheduled[i][m][link.name][time + hop].Not()
                    )

    is_scheduled_tt = {}
    # C2: Flow scheduling constraint, C3: Interval constraint
    for i, flow in enumerate(f_tt):
        is_scheduled_tt[i] = model.NewBoolVar(f"is_scheduled_tt_{i}")
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            model.Add(phi[i, m] > 0).OnlyEnforceIf(is_scheduled_tt[i])
            model.Add((m - 1) * flow.period // INTERVAL_TIME < phi[i, m]).OnlyEnforceIf(
                is_scheduled_tt[i]
            )
            model.Add(phi[i, m] <= m * flow.period // INTERVAL_TIME).OnlyEnforceIf(
                is_scheduled_tt[i]
            )
        model.Add(
            sum(phi[i, m] for m in range(1, HYPER_CYCLE // flow.period + 1)) == 0
        ).OnlyEnforceIf(is_scheduled_tt[i].Not())

    # C4: Decision variable
    # chi = {}
    # for i, flow in enumerate(flows):
    #     for link in links:
    #         for time in range(1, N + 1):
    #             chi[i, link.name, time] = model.NewBoolVar(f"chi_{i}_{link.name}_{time}")

    # for i, flow in enumerate(flows):
    #     for m in range(1, HYPER_CYCLE // flow.period + 1):
    #         for hop in range(Paths[flow.path].hops):
    #             link = Paths[flow.path].links[hop]
    #             for time in range(1, N + 1 - hop):
    #                 model.Add(chi[i, link.name, time + hop] == 1).OnlyEnforceIf(
    #                     model.NewBoolAnd(
    #                         [phi[i, m] <= time, time < phi[i, m] + Paths[flow.path].hops]
    #                     )
    #                 )

    # C5: Latency requirement
    for i, flow in enumerate(f_tt):
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            model.Add(
                (phi[i, m] - 1) * INTERVAL_TIME
                - (m - 1) * flow.period
                + INTERVAL_TIME * (Paths[flow.path].hops + 1)
                <= flow.latency
            ).OnlyEnforceIf(is_scheduled_tt[i])

    def Mbps_to_bytes(Mbps: float):
        return Mbps * 1000000 / 8

    # # C6: Throughput requirement
    # for i, flow in enumerate(f_avb):
    #     for link in l_5G:
    #         model.Add(
    #             sum(chi[i, link.name, k] for k in range(1, N + 1))
    #             >= math.ceil(Mbps_to_bytes(flow.bandwidth) / flow.payload * HYPER_CYCLE / 1000000)
    #         ).OnlyEnforceIf(is_scheduled[i])

    # C7: TSN capacity limit
    TSN_OVERHEAD = 59
    TSN_CAPACITY = math.floor(U_TSN * Mbps_to_bytes(B_TSN) * INTERVAL_TIME / 1000000)
    print(f"TSN capacity: {TSN_CAPACITY}")
    for k in range(1, N + 1):
        for link in l_TSN:
            # UL
            model.Add(
                sum(
                    (flow.payload + TSN_OVERHEAD) * scheduled[i][m][link.name][k]
                    for i, flow in enumerate(UL_flows)
                    for m in range(1, HYPER_CYCLE // flow.period + 1)
                )
                <= TSN_CAPACITY
            )
            # DL
            model.Add(
                sum(
                    (flow.payload + TSN_OVERHEAD) * scheduled[i][m][link.name][k]
                    for i, flow in enumerate(DL_flows)
                    for m in range(1, HYPER_CYCLE // flow.period + 1)
                )
                <= TSN_CAPACITY
            )

    # load calculation
    FIVEG_OVERHEAD = 33
    FIVEG_CAPACITY = math.floor(U_5G * NUM_BANDS * INTERVAL_TIME / TTI)
    print(f"5G # of RB: {FIVEG_CAPACITY}")

    carrierInfo = CarrierInfo(
        carrierFrequency=5.9,
        numBands=NUM_BANDS,
        firstBand=0,
        lastBand=NUM_BANDS - 1,
        bandLimit=[],
        numerologyIndex=mu,
        slotFormat=sf,
    )

    # calculate required RBs for each flow
    required_rbs = {}
    for flow in flows:
        direction = Paths[flow.path].direction
        required_rbs[flow.id] = req_rbs(
            Paths[flow.path].cqi, carrierInfo, flow.payload + FIVEG_OVERHEAD, direction
        )

    payload_sum_ul = sum(flow.payload for flow in UL_flows)
    payload_sum_dl = sum(flow.payload for flow in DL_flows)
    rb_sum_ul = sum(required_rbs[flow.id] for flow in UL_flows)
    rb_sum_dl = sum(required_rbs[flow.id] for flow in DL_flows)
    print(f"UL payload sum: {payload_sum_ul}, DL payload sum: {payload_sum_dl}")
    print(f"UL RB sum: {rb_sum_ul}, DL RB sum: {rb_sum_dl}")

    load_ul = {}
    load_dl = {}
    rb_load_ul = {}
    rb_load_dl = {}
    for k in range(1, N + 1):
        link = l_5G[0]
        load_ul[k] = model.NewIntVar(0, payload_sum_ul, f"load_ul_{k}")
        load_dl[k] = model.NewIntVar(0, payload_sum_dl, f"load_dl_{k}")
        rb_load_ul[k] = model.NewIntVar(0, rb_sum_ul, f"rb_load_ul_{k}")
        rb_load_dl[k] = model.NewIntVar(0, rb_sum_dl, f"rb_load_dl_{k}")

        load_sum_ul = sum(
            flow.payload * scheduled[i][m][link.name][k]
            for i, flow in enumerate(UL_flows)
            for m in range(1, HYPER_CYCLE // flow.period + 1)
        )
        load_sum_dl = sum(
            flow.payload * scheduled[i][m][link.name][k]
            for i, flow in enumerate(DL_flows)
            for m in range(1, HYPER_CYCLE // flow.period + 1)
        )
        model.Add(load_ul[k] == load_sum_ul)
        model.Add(load_dl[k] == load_sum_dl)

        rb_load_sum_ul = sum(
            required_rbs[flow.id] * scheduled[i][m][link.name][k]
            for i, flow in enumerate(UL_flows)
            for m in range(1, HYPER_CYCLE // flow.period + 1)
        )
        rb_load_sum_dl = sum(
            required_rbs[flow.id] * scheduled[i][m][link.name][k]
            for i, flow in enumerate(DL_flows)
            for m in range(1, HYPER_CYCLE // flow.period + 1)
        )
        model.Add(rb_load_ul[k] == rb_load_sum_ul)
        model.Add(rb_load_dl[k] == rb_load_sum_dl)
        model.Add(rb_load_ul[k] <= FIVEG_CAPACITY)
        model.Add(rb_load_dl[k] <= FIVEG_CAPACITY)

    # # All need to be scheduled
    # for i, flow in enumerate(flows):
    #     model.Add(is_scheduled_tt[i] == 1)

    # Objective 1: Maximize schedulable flows
    scheduled_flows = sum(is_scheduled_tt[i] for i, flow in enumerate(flows))
    # Objective 2: Load balance

    max_load_ul = model.NewIntVar(0, payload_sum_ul, "max_load_ul")
    max_load_dl = model.NewIntVar(0, payload_sum_dl, "max_load_dl")
    max_rb_load_ul = model.NewIntVar(0, rb_sum_ul, "max_rb_load_ul")
    max_rb_load_dl = model.NewIntVar(0, rb_sum_dl, "max_rb_load_ul")

    model.AddMaxEquality(max_load_ul, [load_ul[k] for k in range(1, N + 1)])
    model.AddMaxEquality(max_load_dl, [load_dl[k] for k in range(1, N + 1)])
    model.AddMaxEquality(max_rb_load_ul, [rb_load_ul[k] for k in range(1, N + 1)])
    model.AddMaxEquality(max_rb_load_dl, [rb_load_dl[k] for k in range(1, N + 1)])

    weight_1 = 1
    weight_2 = 0.001
    model.Maximize(weight_1 * scheduled_flows - weight_2 * max_load_ul - weight_2 * max_load_dl)

    # Create and solve the model
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        print("Solution found:")
        for i, flow in enumerate(flows):
            if solver.Value(is_scheduled_tt[i]) > 0:
                print(f"{flow.id} is scheduled")
                # print out flow info
                print(
                    f"ID: {flow.id}, period = {flow.period}, payload = {flow.payload}, priority = {flow.priority}, deadline = {flow.latency}, jitter = {flow.jitter}, bandwidth = {flow.bandwidth}, path = {flow.path}"
                )
                for m in range(1, HYPER_CYCLE // flow.period + 1):
                    if solver.Value(phi[i, m]) > 0:
                        print(f"{m}-th at interval {solver.Value(phi[i, m])}")

        # print out unscheduled flows
        for i, flow in enumerate(flows):
            if solver.Value(is_scheduled_tt[i]) == 0:
                print(f"{flow.id} is not scheduled")

        # # print out schedule[i][m][link.name][k]
        # for i, flow in enumerate(flows):
        #     for m in range(1, HYPER_CYCLE // flow.period + 1):
        #         for link in links:
        #             for k in range(1, N + 1):
        #                 if solver.Value(scheduled[i][m][link.name][k]) > 0:
        #                     print(f"{flow.id}-{m}: <{link.name}> at {k}-th interval")

        print(f"max_load_ul: {solver.Value(max_load_ul)}")
        print(f"max_load_dl: {solver.Value(max_load_dl)}")
        print(f"max_rb_load_ul: {solver.Value(max_rb_load_ul)}")
        print(f"max_rb_load_dl: {solver.Value(max_rb_load_dl)}")
        for k in range(1, N + 1):
            # print out load/rbs of link 5G
            link = l_5G[0]
            print(
                f"load/RBs at {k}-th interval: {solver.Value(load_ul[k])} / {solver.Value(rb_load_ul[k])} (UL), {solver.Value(load_dl[k])} / {solver.Value(rb_load_dl[k])} (DL)"
            )

    else:
        print("No solution found.")
