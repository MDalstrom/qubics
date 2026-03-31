import os
import re
import subprocess
import tempfile
from pathlib import Path

import pycparser
from pycparser import c_ast

from _epk.manifest import dump_from_pyproject

_FAKE_HEADERS: dict[str, str] = {
    "stddef.h":  "typedef unsigned long size_t; typedef long ptrdiff_t; typedef void* nullptr_t;",
    "stdint.h":  "typedef signed char int8_t; typedef short int16_t; typedef int int32_t; typedef long int64_t;"
                 "typedef unsigned char uint8_t; typedef unsigned short uint16_t; typedef unsigned int uint32_t; typedef unsigned long uint64_t;",
    "stdbool.h": "typedef int bool; static const int true = 1; static const int false = 0;",
    "stdlib.h":  "",
    "stdio.h":   "",
    "string.h":  "",
}

_C_TO_PY: dict[str, str] = {
    "void": "None",
    "bool": "ctypes.c_bool",
    "char": "ctypes.c_char",
    "int": "ctypes.c_int",
    "short": "ctypes.c_short",
    "long": "ctypes.c_long",
    "unsigned": "ctypes.c_uint",
    "size_t": "ctypes.c_size_t",
    "float": "ctypes.c_float",
    "double": "ctypes.c_double",
    "uint8_t": "ctypes.c_uint8",  "uint16_t": "ctypes.c_uint16",  "uint32_t": "ctypes.c_uint32",  "uint64_t": "ctypes.c_uint64",
    "int8_t":  "ctypes.c_int8",   "int16_t":  "ctypes.c_int16",   "int32_t":  "ctypes.c_int32",   "int64_t":  "ctypes.c_int64",
}

_C_TO_CTYPES: dict[str, str] = {
    "void": "None",
    "bool": "ctypes.c_bool",
    "char": "ctypes.c_char",
    "int": "ctypes.c_int",
    "short": "ctypes.c_short",
    "long": "ctypes.c_long",
    "unsigned": "ctypes.c_uint",
    "size_t": "ctypes.c_size_t",
    "float": "ctypes.c_float",
    "double": "ctypes.c_double",
    "uint8_t": "ctypes.c_uint8",   "uint16_t": "ctypes.c_uint16",  "uint32_t": "ctypes.c_uint32",  "uint64_t": "ctypes.c_uint64",
    "int8_t":  "ctypes.c_int8",    "int16_t":  "ctypes.c_int16",   "int32_t":  "ctypes.c_int32",   "int64_t":  "ctypes.c_int64",
}


def _type_to_py(node, funcptr_names: set[str] = set(), foreign: dict[str, str] = {}) -> str:
    if isinstance(node, c_ast.PtrDecl):
        inner = node.type
        if isinstance(inner, c_ast.TypeDecl):
            if isinstance(inner.type, c_ast.IdentifierType):
                names = [n for n in inner.type.names if n not in ("const", "volatile")]
                if names == ["char"]:
                    return "str"
                if names == ["void"]:
                    return "Any"
            if isinstance(inner.type, c_ast.Struct) and inner.type.name:
                name = inner.type.name
                prefix = f"{foreign[name]}." if name in foreign else ""
                return f"_Pointer[{prefix}{name}]"
        return f"_Pointer[{_type_to_py(inner, funcptr_names, foreign)}]"
    if isinstance(node, c_ast.TypeDecl):
        inner = node.type
        if isinstance(inner, c_ast.IdentifierType):
            names = [n for n in inner.names if n not in ("const", "volatile")]
            name = " ".join(names)
            if name in funcptr_names:
                return "ctypes._CFunctionType"
            if name not in _C_TO_PY and name in foreign:
                return f"{foreign[name]}.{name}"
            return _C_TO_PY.get(name, name)
        if isinstance(inner, c_ast.Struct):
            name = inner.name or "Any"
            if name != "Any" and name in foreign:
                return f"{foreign[name]}.{name}"
            return name
    return "Any"


def _type_to_ctypes(node, foreign: dict[str, str] = {}) -> str:
    if isinstance(node, c_ast.PtrDecl):
        inner = node.type
        if isinstance(inner, c_ast.TypeDecl):
            if isinstance(inner.type, c_ast.IdentifierType):
                names = [n for n in inner.type.names if n not in ("const", "volatile")]
                if names == ["char"]:
                    return "ctypes.c_char_p"
                if names == ["void"]:
                    return "ctypes.c_void_p"
            if isinstance(inner.type, c_ast.Struct) and inner.type.name:
                name = inner.type.name
                prefix = f"{foreign[name]}." if name in foreign else ""
                return f"ctypes.POINTER({prefix}{name})"
        return f"ctypes.POINTER({_type_to_ctypes(inner, foreign)})"
    if isinstance(node, c_ast.TypeDecl):
        inner = node.type
        if isinstance(inner, c_ast.IdentifierType):
            names = [n for n in inner.names if n not in ("const", "volatile")]
            name = " ".join(names)
            if name not in _C_TO_CTYPES and name in foreign:
                return f"{foreign[name]}.{name}"
            return _C_TO_CTYPES.get(name, name)
        if isinstance(inner, c_ast.Struct):
            name = inner.name or "ctypes.c_void_p"
            if name != "ctypes.c_void_p" and name in foreign:
                return f"{foreign[name]}.{name}"
            return name
    return "ctypes.c_void_p"


def _parse(header: Path) -> list[c_ast.Node]:
    with tempfile.TemporaryDirectory() as fake_dir:
        for name, content in _FAKE_HEADERS.items():
            (Path(fake_dir) / name).write_text(content)
        result = subprocess.run(
            ["cpp", "-nostdinc", f"-I{fake_dir}", str(header)],
            capture_output=True, text=True, check=True
        )
    ast = pycparser.CParser().parse(result.stdout, filename=str(header))
    return [n for n in ast.ext if n.coord and n.coord.file == str(header)]


def _local_includes(header: Path) -> list[str]:
    return re.findall(r'^\s*#include\s+"([^"]+)"', header.read_text(), re.MULTILINE)


def _exported_types(header: Path) -> set[str]:
    return {node.name for node in _parse(header) if isinstance(node, c_ast.Typedef)}


def _rel_import(include: str, header: Path, pkg_root: Path) -> tuple[str, str] | None:
    target = (header.parent / include).resolve()
    try:
        target.relative_to(pkg_root)
    except ValueError:
        return None
    rel = os.path.relpath(target.parent, header.parent)
    parts = Path(rel).parts
    dots = "."
    module_parts = []
    for part in parts:
        if part == "..":
            dots += "."
        else:
            module_parts.append(part)
    module_name = target.stem
    if module_parts:
        return f"from {dots}{'.'.join(module_parts)} import {module_name}", module_name
    return f"from {dots} import {module_name}", module_name


def _generate_file(header: Path, pkg_root: Path) -> str:
    nodes = _parse(header)
    class_name = "Lib"

    foreign: dict[str, str] = {}
    import_stmts: list[str] = []
    for inc in _local_includes(header):
        result = _rel_import(inc, header, pkg_root)
        if result is None:
            continue
        stmt, alias = result
        import_stmts.append(stmt)
        for type_name in _exported_types((header.parent / inc).resolve()):
            foreign[type_name] = alias

    lines = [
        "import ctypes",
        "from typing import Any",
        "from ctypes import _Pointer",
        "",
        *import_stmts,
        *([""] if import_stmts else []),
    ]

    funcptr_nodes = [
        node for node in nodes
        if isinstance(node, c_ast.Typedef)
        and isinstance(node.type, c_ast.PtrDecl)
        and isinstance(node.type.type, c_ast.FuncDecl)
    ]

    for node in funcptr_nodes:
        func = node.type.type
        ret = _type_to_ctypes(func.type, foreign)
        argtypes = []
        if func.args:
            for param in func.args.params:
                if not isinstance(param, c_ast.EllipsisParam):
                    argtypes.append(_type_to_ctypes(param.type, foreign))
        all_types = ", ".join([ret] + argtypes)
        lines.append(f"{node.name} = ctypes.CFUNCTYPE({all_types})")

    if funcptr_nodes:
        lines.append("")

    struct_nodes = [
        node for node in nodes
        if isinstance(node, c_ast.Typedef)
        and isinstance(node.type, c_ast.TypeDecl)
        and isinstance(node.type.type, c_ast.Struct)
        and node.type.type.decls
    ]

    funcptr_names = {node.name for node in funcptr_nodes}

    for node in struct_nodes:
        lines.append(f"class {node.name}(ctypes.Structure):")
        for field in node.type.type.decls:
            lines.append(f"    {field.name}: \"{_type_to_py(field.type, funcptr_names, foreign)}\"")
        lines.append("")

    for node in struct_nodes:
        lines.append(f"{node.name}._fields_ = [")
        for field in node.type.type.decls:
            lines.append(f"    (\"{field.name}\", {_type_to_ctypes(field.type, foreign)}),")
        lines.append("]")
        lines.append("")

    func_nodes = [n for n in nodes if isinstance(n, c_ast.Decl) and isinstance(n.type, c_ast.FuncDecl)]

    lines.append(f"class {class_name}:")
    lines.append("    def __init__(self, lib: ctypes.CDLL) -> None:")

    for node in func_nodes:
        func = node.type
        argtypes = []
        if func.args:
            for param in func.args.params:
                if not isinstance(param, c_ast.EllipsisParam) and param.name:
                    argtypes.append(_type_to_ctypes(param.type, foreign))
        if argtypes:
            lines.append(f"        lib.{node.name}.argtypes = [{', '.join(argtypes)}]")
        lines.append(f"        lib.{node.name}.restype = {_type_to_ctypes(func.type, foreign)}")

    lines.append("        self._lib = lib")
    lines.append("")

    for node in func_nodes:
        func = node.type
        params, args = ["self"], []
        if func.args:
            for param in func.args.params:
                if isinstance(param, c_ast.EllipsisParam):
                    params.append("*args: Any")
                    args.append("*args")
                elif param.name:
                    params.append(f"{param.name}: \"{_type_to_py(param.type, funcptr_names, foreign)}\"")
                    args.append(param.name)
        ret = _type_to_py(func.type, funcptr_names, foreign)
        lines.append(f"    def {node.name}({', '.join(params)}) -> \"{ret}\":")
        lines.append(f"        return self._lib.{node.name}({', '.join(args)})")
        lines.append("")

    return "\n".join(lines)


def generate(src: str, dest: str):
    src_path = Path(src).resolve()
    dest_path = Path(dest).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        dump_from_pyproject(src_path, tmp_path)

        subprocess.run(["epk", "resolve", tmp_path])

        for pkg_dir in tmp_path.iterdir():
            if not pkg_dir.is_dir():
                continue

            headers = sorted(pkg_dir.glob("**/*.h"))
            if not headers:
                continue

            pkg_out = dest_path / "generated" / pkg_dir.name
            pkg_out.mkdir(parents=True, exist_ok=True)
            (dest_path / "generated" / "__init__.py").touch()
            (pkg_out / "__init__.py").touch()

            for header in headers:
                rel = header.relative_to(pkg_dir)
                out_file = pkg_out / rel.with_suffix(".py")
                out_file.parent.mkdir(parents=True, exist_ok=True)
                (out_file.parent / "__init__.py").touch()
                out_file.write_text(_generate_file(header.resolve(), pkg_dir.resolve()))
