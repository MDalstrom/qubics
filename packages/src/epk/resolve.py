from typing import Protocol, TypeVar, Callable


class Node(Protocol):
    name: str
    deps: list[str]


N = TypeVar("N", bound=Node)


def traverse(from_name: Callable[[str], N], source: list[str]) -> list[N]:
    visited = set()
    result = []

    def dfs(name: str) -> None:
        if name in visited:
            return
        visited.add(name)

        node = from_name(name)
        for dep in node.deps:
            dfs(dep)
        result.append(node)

    for dep in source:
        dfs(dep)
    return result
