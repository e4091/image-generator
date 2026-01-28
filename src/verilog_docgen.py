#!/usr/bin/env python3
"""Generate diagrams and documentation from Verilog source."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable


@dataclass
class Port:
    name: str
    direction: str | None = None
    data_type: str | None = None
    width: str | None = None


@dataclass
class Instance:
    module_name: str
    instance_name: str
    connections: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Module:
    name: str
    parameters: list[str] = field(default_factory=list)
    ports: list[Port] = field(default_factory=list)
    instances: list[Instance] = field(default_factory=list)


KEYWORDS = {
    "if",
    "for",
    "case",
    "always",
    "assign",
    "generate",
    "endmodule",
}


def strip_comments(text: str) -> str:
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)


def parse_parameters(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    cleaned = []
    for part in parts:
        cleaned.append(part.replace("parameter", "").strip())
    return cleaned


def parse_ports_from_header(raw: str) -> list[str]:
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    names = []
    for part in parts:
        tokens = part.replace("\n", " ").split()
        if tokens:
            names.append(tokens[-1].strip(")"))
    return names


def parse_port_declarations(body: str) -> list[Port]:
    ports: list[Port] = []
    port_decl = re.compile(
        r"\b(input|output|inout)\b\s*(reg|wire|logic)?\s*(\[[^\]]+\])?\s*([^;]+);"
    )
    for match in port_decl.finditer(body):
        direction, data_type, width, names = match.groups()
        for name in names.split(","):
            clean_name = name.strip()
            if not clean_name:
                continue
            if "=" in clean_name:
                clean_name = clean_name.split("=")[0].strip()
            ports.append(
                Port(
                    name=clean_name,
                    direction=direction,
                    data_type=data_type,
                    width=width,
                )
            )
    return ports


def parse_instances(body: str) -> list[Instance]:
    instances: list[Instance] = []
    instance_pattern = re.compile(r"\b(\w+)\s+(\w+)\s*\((.*?)\)\s*;", re.DOTALL)
    for match in instance_pattern.finditer(body):
        module_name, instance_name, raw_connections = match.groups()
        if module_name in KEYWORDS:
            continue
        connections: list[tuple[str, str]] = []
        for conn in re.findall(r"\.(\w+)\s*\(\s*([^)]+)\s*\)", raw_connections):
            connections.append((conn[0], conn[1].strip()))
        instances.append(
            Instance(
                module_name=module_name,
                instance_name=instance_name,
                connections=connections,
            )
        )
    return instances


def parse_modules(text: str) -> list[Module]:
    clean = strip_comments(text)
    module_pattern = re.compile(
        r"\bmodule\s+(\w+)\s*(#\s*\((?P<params>.*?)\))?\s*\((?P<ports>.*?)\)\s*;"
        r"(?P<body>.*?)\bendmodule",
        re.DOTALL,
    )
    modules: list[Module] = []
    for match in module_pattern.finditer(clean):
        name = match.group(1)
        params = parse_parameters(match.group("params"))
        header_ports = parse_ports_from_header(match.group("ports"))
        body = match.group("body")
        ports = parse_port_declarations(body)
        if not ports:
            ports = [Port(name=p) for p in header_ports]
        instances = parse_instances(body)
        modules.append(Module(name=name, parameters=params, ports=ports, instances=instances))
    return modules


def format_port_table(ports: Iterable[Port]) -> str:
    rows = ["| Name | Direction | Type | Width |", "| --- | --- | --- | --- |"]
    for port in ports:
        rows.append(
            f"| {port.name} | {port.direction or '-'} | {port.data_type or '-'} | {port.width or '-'} |"
        )
    return "\n".join(rows)


def make_mermaid(modules: Iterable[Module]) -> str:
    lines = ["flowchart LR"]
    for module in modules:
        module_id = f"{module.name}_self"
        lines.append(f"  subgraph {module.name}")
        lines.append(f"    {module_id}[\"{module.name}\"]")
        for idx, instance in enumerate(module.instances, start=1):
            instance_id = f"{module.name}_inst_{idx}"
            label = f"{instance.module_name} {instance.instance_name}"
            lines.append(f"    {instance_id}[\"{label}\"]")
            lines.append(f"    {module_id} --> {instance_id}")
        lines.append("  end")
    return "\n".join(lines)


def build_documentation(modules: Iterable[Module]) -> str:
    lines = ["# Verilog Design Documentation", ""]
    lines.append("## Module Diagram")
    lines.append("")
    lines.append("```mermaid")
    lines.append(make_mermaid(modules))
    lines.append("```")
    lines.append("")
    lines.append("## Modules")
    for module in modules:
        lines.append("")
        lines.append(f"### {module.name}")
        if module.parameters:
            lines.append("")
            lines.append("**Parameters**")
            for param in module.parameters:
                lines.append(f"- {param}")
        lines.append("")
        lines.append("**Ports**")
        lines.append(format_port_table(module.ports))
        lines.append("")
        lines.append("**Instances**")
        if module.instances:
            for instance in module.instances:
                lines.append(f"- `{instance.module_name}` `{instance.instance_name}`")
                if instance.connections:
                    for port, signal in instance.connections:
                        lines.append(f"  - .{port}({signal})")
        else:
            lines.append("- None")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate documentation for Verilog source.")
    parser.add_argument("--input", required=True, type=Path, help="Path to Verilog file.")
    parser.add_argument(
        "--output-dir",
        default=Path("output/verilog_docs"),
        type=Path,
        help="Directory for generated documentation.",
    )
    parser.add_argument(
        "--output-name",
        default="verilog_design.md",
        help="Markdown filename for documentation.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    content = args.input.read_text(encoding="utf-8")
    modules = parse_modules(content)
    if not modules:
        raise ValueError("No modules found in input.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / args.output_name
    output_path.write_text(build_documentation(modules), encoding="utf-8")


if __name__ == "__main__":
    main()
