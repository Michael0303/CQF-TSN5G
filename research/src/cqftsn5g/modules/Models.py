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
    def name(self) -> str:
        return self.point1.name + "-" + self.point2.name


@dataclass
class Path:
    src: Node
    dst: Node
    links: list[Link]
    cqi: int
    direction: str

    @property
    def hops(self) -> int:
        return len(self.links)


@dataclass
class Flow:
    id: str
    period: int  # us
    payload: int  # bytes
    priority: int
    latency: int  # us
    jitter: int  # us
    bandwidth: float  # Mbps
    flowType: str  # "TT" or "AVB"
    path: str


@dataclass
class Network:
    nodes: list[Node]
    links: list[Link]
    flows: list[Flow]


@dataclass
class Flow_assignment:
    flow: Flow
    rb_usage: int
    serve_time: list[int]
    fiveG_link_serve_time: list[int]
    direction: str
