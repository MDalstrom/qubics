from epk.reference import Reference, parse as parse_reference, serialize as serialize_reference
from typing import NamedTuple
from pathlib import Path
import tomllib


class LockedPackage(NamedTuple):
    name: str
    version: str
    reference: Reference


def parse(path: Path) -> list[LockedPackage]:
    with open(path, "rb") as f:
        data = tomllib.load(f)


    return [LockedPackage(
        name=entry["name"],
        version=entry["version"],
        reference=parse_reference(entry["reference"])
    ) for entry in data["packages"]]


def serialize(path: Path, packages: list[LockedPackage]) -> None:
    with open(path, "w") as f:
        for package in packages:
            f.write("[[packages]]\n")
            f.write(f'name = "{package.name}"\n')
            f.write(f'version = "{package.version}"\n')
            f.write(f'reference = "{serialize_reference(package.reference)}"\n')
            f.write("\n")
