from dataclasses import dataclass
@dataclass
class Node:
    name: str
    is_endpoint: bool

@dataclass
class Link:
    point1: Node
    point2: Node
    bandwidth: int
    linkType: str

    @property
    def name(self):
        return self.point1.name + "-" + self.point2.name
@dataclass
class Path:
    src: Node
    dst: Node
    links: list[Link]
    cqi: int

@dataclass
class Flow:
    period: float  # us
    payload: int  # bytes
    priority: int
    latency: float  # us
    jitter: float  # us
    bandwidth: float  # MB/s
    flowType: str  # "TT" or "AVB"
    path: Path

    @property
    def hops(self):
        return len(self.path.links)

@dataclass
class Network:
    nodes: list[Node]
    links: list[Link]
    flows: list[Flow]

