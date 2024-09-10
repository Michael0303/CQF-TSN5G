class Node:
    def __init__(self, name: str, is_endpoint: bool):
        self.name = name
        self.is_endpoint = is_endpoint


class Link:
    def __init__(self, point1: Node, point2: Node, bandwidth: int, linkType: str):
        self.point1 = point1
        self.point2 = point2
        self.name = point1.name + "-" + point2.name
        self.bandwidth = bandwidth
        self.linkType = linkType


class Path:
    def __init__(self, src: Node, dst: Node, links: list[Link], cqi: int):
        self.src = src
        self.dst = dst
        self.links = links
        self.cqi = cqi


class Flow:
    def __init__(
        self,
        period: float,  # ms
        payload: int,  # bytes
        priority: int,
        latency: float,  # ms
        jitter: float,  # ms
        bandwidth: float,  # MB/s
        flowType: str,  # "TT" or "AVB"
        path: Path,
    ):
        self.period = period
        self.payload = payload
        self.priority = priority
        self.latency = latency
        self.jitter = jitter
        self.bandwidth = bandwidth
        self.flowType = flowType
        self.path = path
        self.hops = len(path.links)


class Network:
    def __init__(self, nodes: list[Node], links: list[Link], flows: list[Flow]) -> None:
        self.nodes = nodes
        self.links = links
        self.flows = flows
