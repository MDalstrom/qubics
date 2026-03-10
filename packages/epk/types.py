from dataclasses import dataclass

type PackageReference = str

@dataclass
class Package:
    name: str
    version: str
    deps: list[PackageReference]
    artifacts: dict
