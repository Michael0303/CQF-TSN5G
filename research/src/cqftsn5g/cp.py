import math
from cqftsn5g.modules.Models import Flow, Flow_assignment, Link, Path
from cqftsn5g.modules.NRAmc import CarrierInfo, Direction, SlotFormat
from ortools.sat.python import cp_model
from cqftsn5g.calculate_rbs import req_rbs
from assignment_plot import result_plot


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
    only_fiveG: bool = False,
) -> list[Flow_assignment]:
    model = cp_model.CpModel()
    N = HYPER_CYCLE // INTERVAL_TIME
    flows = f_tt + f_avb
    links = l_5G if only_fiveG else l_TSN + l_5G
    TTI = 1000 / 2**mu
    print(f"N = {N}")
    print(f"TTI = {TTI}")

    UL_flows = [flow for flow in flows if Paths[flow.path].direction == "UL"]
    DL_flows = [flow for flow in flows if Paths[flow.path].direction == "DL"]

    # print(f"UL_flows: {UL_flows}")
    # print(f"DL_flows: {DL_flows}")

    scheduled = {
        flow.id: {
            m: {
                link.name: {
                    k: model.NewBoolVar(f"schedule_{flow.id}_{m}_{link.name}_{k}")
                    for k in range(1, N + 1)
                }
                for link in links
            }
            for m in range(1, HYPER_CYCLE // flow.period + 1)
        }
        for flow in flows
    }

    # C1: Scheduling variable
    phi = {
        (flow.id, m): model.NewIntVar(0, N, f"phi_tt_{flow.id}_{m}")
        for flow in flows
        for m in range(1, HYPER_CYCLE // flow.period + 1)
    }

    # C4: Decision variable
    for flow in flows:
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            for hop in range(Paths[flow.path].hops):
                link = Paths[flow.path].links[hop]
                if only_fiveG and link not in l_5G:
                    continue
                for time in range(1, N + 1 - hop):
                    model.Add(phi[flow.id, m] == time).OnlyEnforceIf(
                        scheduled[flow.id][m][link.name][time + hop]
                    )
                    model.Add(phi[flow.id, m] != time).OnlyEnforceIf(
                        scheduled[flow.id][m][link.name][time + hop].Not()
                    )
                for time in range(N + 1 - hop, N + 1):
                    model.Add(phi[flow.id, m] != time)

    is_scheduled_tt = {flow.id: model.NewBoolVar(f"is_scheduled_tt_{flow.id}") for flow in f_tt}
    # C2: Flow scheduling constraint, C3: Interval constraint for TT flows
    for flow in f_tt:
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            model.Add(phi[flow.id, m] > 0).OnlyEnforceIf(is_scheduled_tt[flow.id])
            model.Add((m - 1) * flow.period // INTERVAL_TIME < phi[flow.id, m]).OnlyEnforceIf(
                is_scheduled_tt[flow.id]
            )
            model.Add(phi[flow.id, m] <= m * flow.period // INTERVAL_TIME).OnlyEnforceIf(
                is_scheduled_tt[flow.id]
            )
        model.Add(
            sum(phi[flow.id, m] for m in range(1, HYPER_CYCLE // flow.period + 1)) == 0
        ).OnlyEnforceIf(is_scheduled_tt[flow.id].Not())

    is_scheduled_avb_flow = {
        flow.id: model.NewBoolVar(f"is_scheduled_avb_flow_{flow.id}") for flow in f_avb
    }
    is_scheduled_avb_frame = {
        (flow.id, m): model.NewBoolVar(f"is_scheduled_avb_{flow.id}_{m}")
        for flow in f_avb
        for m in range(1, HYPER_CYCLE // flow.period + 1)
    }
    # C2: Flow scheduling constraint, C3: Interval constraint for AVB flows
    for flow in f_avb:
        model.Add(
            sum(
                is_scheduled_avb_frame[flow.id, m] for m in range(1, HYPER_CYCLE // flow.period + 1)
            )
            > 0
        ).OnlyEnforceIf(is_scheduled_avb_flow[flow.id])
        model.Add(
            sum(
                is_scheduled_avb_frame[flow.id, m] for m in range(1, HYPER_CYCLE // flow.period + 1)
            )
            == 0
        ).OnlyEnforceIf(is_scheduled_avb_flow[flow.id].Not())
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            model.Add(phi[flow.id, m] > 0).OnlyEnforceIf(is_scheduled_avb_frame[flow.id, m])
            model.Add(phi[flow.id, m] == 0).OnlyEnforceIf(is_scheduled_avb_frame[flow.id, m].Not())
            model.Add((m - 1) * flow.period // INTERVAL_TIME < phi[flow.id, m]).OnlyEnforceIf(
                is_scheduled_avb_frame[flow.id, m]
            )
            model.Add(phi[flow.id, m] <= m * flow.period // INTERVAL_TIME).OnlyEnforceIf(
                is_scheduled_avb_frame[flow.id, m]
            )

    # C5: Latency requirement
    for flow in f_tt:
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            model.Add(
                (phi[flow.id, m] - 1) * INTERVAL_TIME + INTERVAL_TIME * (Paths[flow.path].hops + 1)
                <= min((m - 1) * flow.period + flow.latency, HYPER_CYCLE)
            ).OnlyEnforceIf(is_scheduled_tt[flow.id])

    for flow in f_avb:
        for m in range(1, HYPER_CYCLE // flow.period + 1):
            model.Add(
                (phi[flow.id, m] - 1) * INTERVAL_TIME + INTERVAL_TIME * (Paths[flow.path].hops + 1)
                <= min((m - 1) * flow.period + flow.latency, HYPER_CYCLE)
            ).OnlyEnforceIf(is_scheduled_avb_frame[flow.id, m])

    def Mbps_to_bytes(Mbps: float):
        return Mbps * 1000000 / 8

    # C6: Throughput requirement
    for flow in f_avb:
        link = l_5G[0]
        model.Add(
            sum(
                is_scheduled_avb_frame[flow.id, m] for m in range(1, HYPER_CYCLE // flow.period + 1)
            )
            >= math.ceil(Mbps_to_bytes(flow.bandwidth) / flow.payload * HYPER_CYCLE / 1000000)
        ).OnlyEnforceIf(is_scheduled_avb_flow[flow.id])

    # C7: TSN capacity limit
    TSN_OVERHEAD = 59
    TSN_CAPACITY = math.floor(U_TSN * Mbps_to_bytes(B_TSN) * INTERVAL_TIME / 1000000)
    print(f"TSN capacity: {TSN_CAPACITY}")
    if not only_fiveG:
        for k in range(1, N + 1):
            for link in l_TSN:
                # UL
                model.Add(
                    sum(
                        (flow.payload + TSN_OVERHEAD) * scheduled[flow.id][m][link.name][k]
                        for flow in UL_flows
                        for m in range(1, HYPER_CYCLE // flow.period + 1)
                    )
                    <= TSN_CAPACITY
                )
                # DL
                model.Add(
                    sum(
                        (flow.payload + TSN_OVERHEAD) * scheduled[flow.id][m][link.name][k]
                        for flow in DL_flows
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

        model.Add(
            load_ul[k]
            == sum(
                flow.payload * scheduled[flow.id][m][link.name][k]
                for flow in UL_flows
                for m in range(1, HYPER_CYCLE // flow.period + 1)
            )
        )
        model.Add(
            load_dl[k]
            == sum(
                flow.payload * scheduled[flow.id][m][link.name][k]
                for flow in DL_flows
                for m in range(1, HYPER_CYCLE // flow.period + 1)
            )
        )

        model.Add(
            rb_load_ul[k]
            == sum(
                required_rbs[flow.id] * scheduled[flow.id][m][link.name][k]
                for flow in UL_flows
                for m in range(1, HYPER_CYCLE // flow.period + 1)
            )
        )
        model.Add(
            rb_load_dl[k]
            == sum(
                required_rbs[flow.id] * scheduled[flow.id][m][link.name][k]
                for flow in DL_flows
                for m in range(1, HYPER_CYCLE // flow.period + 1)
            )
        )

        model.Add(rb_load_ul[k] <= FIVEG_CAPACITY)
        model.Add(rb_load_dl[k] <= FIVEG_CAPACITY)

    # # All need to be scheduled
    # for i, flow in enumerate(flows):
    #     model.Add(is_scheduled_tt[i] == 1)

    # Objective 1: Maximize schedulable flows
    scheduled_flows = sum(is_scheduled_tt[flow.id] for flow in f_tt) + sum(
        is_scheduled_avb_flow[flow.id] for flow in f_avb
    )
    # scheduled_flows = sum(is_scheduled_tt[flow.id] for flow in f_tt)
    # Objective 2: Load balance

    max_load_ul = model.NewIntVar(0, payload_sum_ul, "max_load_ul")
    max_load_dl = model.NewIntVar(0, payload_sum_dl, "max_load_dl")
    max_rb_load_ul = model.NewIntVar(0, rb_sum_ul, "max_rb_load_ul")
    max_rb_load_dl = model.NewIntVar(0, rb_sum_dl, "max_rb_load_ul")

    model.AddMaxEquality(max_load_ul, [load_ul[k] for k in range(1, N + 1)])
    model.AddMaxEquality(max_load_dl, [load_dl[k] for k in range(1, N + 1)])
    model.AddMaxEquality(max_rb_load_ul, [rb_load_ul[k] for k in range(1, N + 1)])
    model.AddMaxEquality(max_rb_load_dl, [rb_load_dl[k] for k in range(1, N + 1)])

    # objective 3: priority

    priority_sum = sum((8 - flow.priority) * is_scheduled_tt[flow.id] for flow in f_tt) + sum(
        (8 - flow.priority) * is_scheduled_avb_flow[flow.id] for flow in f_avb
    )

    weight_1 = 1
    # weight_2_ul = 1 / payload_sum_ul if payload_sum_ul > 0 else 0
    # weight_2_dl = 1 / payload_sum_dl if payload_sum_dl > 0 else 0
    weight_2_ul = 0.0001
    weight_2_dl = 0.0001
    weight_3 = 1 / 7
    model.Maximize(
        weight_1 * scheduled_flows
        - (max_load_ul * weight_2_ul + max_load_dl * weight_2_dl)
        + weight_3 * priority_sum
    )

    # Create and solve the model
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        print("Solution found:")
        for flow in f_tt:
            if solver.Value(is_scheduled_tt[flow.id]) > 0:
                print(f"{flow.id} is scheduled")
                # # print out flow info
                print(
                    f"ID: {flow.id}, period = {flow.period}, payload = {flow.payload}, priority = {flow.priority}, deadline = {flow.latency}, jitter = {flow.jitter}, bandwidth = {flow.bandwidth}, path = {flow.path}"
                )
                for m in range(1, HYPER_CYCLE // flow.period + 1):
                    if solver.Value(phi[flow.id, m]) > 0:
                        print(f"{m}-th at interval {solver.Value(phi[flow.id, m])}")

        for flow in f_avb:
            if solver.Value(is_scheduled_avb_flow[flow.id]) > 0:
                print(f"{flow.id} is scheduled")
                print(
                    f"ID: {flow.id}, period = {flow.period}, payload = {flow.payload}, priority = {flow.priority}, deadline = {flow.latency}, jitter = {flow.jitter}, bandwidth = {flow.bandwidth}, path = {flow.path}"
                )
                for m in range(1, HYPER_CYCLE // flow.period + 1):
                    print(f"scheuled {m} = {solver.Value(is_scheduled_avb_frame[flow.id, m])}")
                    if solver.Value(phi[flow.id, m]) > 0:
                        print(f"{m}-th at interval {solver.Value(phi[flow.id, m])}")

        # print out unscheduled flows
        for flow in flows:
            if flow.flowType == "TT" and solver.Value(is_scheduled_tt[flow.id]) == 0:
                print(f"{flow.id} is not scheduled")
                print(
                    f"ID: {flow.id}, period = {flow.period}, payload = {flow.payload}, priority = {flow.priority}, deadline = {flow.latency}, jitter = {flow.jitter}, bandwidth = {flow.bandwidth}, path = {flow.path}"
                )
            if flow.flowType == "AVB" and solver.Value(is_scheduled_avb_flow[flow.id]) == 0:
                print(f"{flow.id} is not scheduled")
                print(
                    f"ID: {flow.id}, period = {flow.period}, payload = {flow.payload}, priority = {flow.priority}, deadline = {flow.latency}, jitter = {flow.jitter}, bandwidth = {flow.bandwidth}, path = {flow.path}"
                )

        # print out schedule[i][m][link.name][k]
        for flow in flows:
            for m in range(1, HYPER_CYCLE // flow.period + 1):
                for link in links:
                    for k in range(1, N + 1):
                        if solver.Value(scheduled[flow.id][m][link.name][k]) > 0:
                            print(f"{flow.id}-{m}: <{link.name}> at {k}-th interval")

        # print out phi
        for flow in flows:
            for m in range(1, HYPER_CYCLE // flow.period + 1):
                print(f"phi_{flow.id}_{m}: {solver.Value(phi[flow.id, m])}")

        print(f"max_load_ul: {solver.Value(max_load_ul)}")
        print(f"max_load_dl: {solver.Value(max_load_dl)}")
        print(f"max_rb_load_ul: {solver.Value(max_rb_load_ul)}")
        print(f"max_rb_load_dl: {solver.Value(max_rb_load_dl)}")
        for k in range(1, N + 1):
            # print out load/rbs of link 5G
            link = l_5G[0]
            if solver.Value(load_ul[k]) > 0 or solver.Value(load_dl[k]) > 0:
                print(
                    f"load/RBs at {k}-th interval: {solver.Value(load_ul[k])} / {solver.Value(rb_load_ul[k])} (UL), {solver.Value(load_dl[k])} / {solver.Value(rb_load_dl[k])} (DL)"
                )
                # print out scheduled flows
                scheduled_flows = [
                    flow.id
                    for flow in flows
                    for m in range(1, HYPER_CYCLE // flow.period + 1)
                    if solver.Value(scheduled[flow.id][m][link.name][k]) > 0
                ]
                print("Scheduled flows:" + ", ".join(scheduled_flows))

        # print out the bandwidth requirement of avbflows and the exact bandwidth
        for flow in f_avb:
            if solver.Value(is_scheduled_avb_flow[flow.id]) > 0:
                print(f"Flow {flow.id} is scheduled")
                count = 0
                for m in range(1, HYPER_CYCLE // flow.period + 1):
                    if solver.Value(phi[flow.id, m]) > 0:
                        count += 1
                print(
                    f"{flow.id} is transmitted {count * flow.payload} bytes > required {Mbps_to_bytes(flow.bandwidth) * HYPER_CYCLE / 1000000} bytes"
                )
        flow_assignments = []
        for flow in flows:
            if (flow.flowType == "TT" and solver.Value(is_scheduled_tt[flow.id]) > 0) or (
                flow.flowType == "AVB" and solver.Value(is_scheduled_avb_flow[flow.id]) > 0
            ):
                flow_assignments.append(
                    Flow_assignment(
                        flow,
                        required_rbs[flow.id],
                        [
                            solver.Value(phi[flow.id, m])
                            for m in range(1, HYPER_CYCLE // flow.period + 1)
                        ],
                        [
                            solver.Value(phi[flow.id, m]) + Paths[flow.path].links.index(l_5G[0])
                            if solver.Value(phi[flow.id, m]) > 0
                            else -1
                            for m in range(1, HYPER_CYCLE // flow.period + 1)
                        ],
                        Paths[flow.path].direction,
                    )
                )
        for flow_assignment in flow_assignments:
            print(
                f"Flow {flow_assignment.flow.id}: RB usage = {flow_assignment.rb_usage}, serve time = {flow_assignment.serve_time}"
            )

        result_plot(N, flow_assignments, FIVEG_CAPACITY)
        return flow_assignments

    else:
        print("No solution found.")
