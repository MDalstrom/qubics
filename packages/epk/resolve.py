from epk.types import Package
import json


def resolve(origin: Package) -> list[Package]:
    visited = set()
    result = []

    def dfs(package: Package):
        if package.name in visited:
            return
        visited.add(package.name)
        for path in package.deps:
            next = Package(**json.loads(path))
            dfs(next)
        result.append(package)

    return result
