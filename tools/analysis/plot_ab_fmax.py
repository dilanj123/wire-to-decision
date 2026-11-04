#!/usr/bin/env python3
"""Render the saved Architecture-A/B nextpnr seed results as a small SVG."""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path


GENERATOR_VERSION = "1.0"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "images" / "architecture_ab_fmax.svg"
TARGET_MHZ = 156.25


def read_results(path: Path, value_column: str) -> tuple[list[int], list[float]]:
    with path.open(newline="") as source:
        rows = list(csv.DictReader(source))
    rows = sorted(rows, key=lambda row: int(row["seed"]))
    if not rows or any(row["routing"] != "PASS" for row in rows):
        raise ValueError(f"missing routed seed result in {path}")
    return ([int(row["seed"]) for row in rows],
            [float(row[value_column]) for row in rows])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    a_path = ROOT / "results/raw/implementation/wire027/five_seed_results_027.csv"
    b_path = ROOT / "results/raw/implementation/arch_b/five_seed_results_028b.csv"
    seeds_a, values_a = read_results(a_path, "achieved_fmax_mhz")
    seeds_b, values_b = read_results(b_path, "achieved_fmax_mhz")
    if seeds_a != seeds_b:
        raise ValueError("Architecture A and B seed sets differ")

    left, right, top, bottom = 82, 790, 72, 382
    y_max = 180.0

    def x_at(index: int) -> float:
        return left + (right - left) * index / (len(seeds_a) - 1)

    def y_at(value: float) -> float:
        return bottom - (bottom - top) * value / y_max

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 470" role="img" aria-labelledby="title desc">',
        '<title id="title">Architecture A and B routed Fmax across five seeds</title>',
        '<desc id="desc">Five routed Fmax values for each architecture, read from the committed WIRE-027 and WIRE-028B CSV files. Every value is below the 156.25 MHz target.</desc>',
        '<rect width="820" height="470" fill="#ffffff"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#17212b}.axis{stroke:#536273;stroke-width:1}.grid{stroke:#d7dee5;stroke-width:1}.target{stroke:#a23b32;stroke-width:2;stroke-dasharray:8 6}.a{stroke:#1769aa;fill:#1769aa}.b{stroke:#bd641b;fill:#bd641b}.series{fill:none;stroke-width:3}</style>',
        '<text x="82" y="34" font-size="21" font-weight="700">Routed Fmax by implementation seed</text>',
    ]

    for tick in (0, 40, 80, 120, TARGET_MHZ, 180):
        y = y_at(tick)
        label = f"{tick:g}"
        lines.append(f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}"/>')
        lines.append(f'<text x="{left-12}" y="{y+5:.2f}" font-size="13" text-anchor="end">{label}</text>')
    y_target = y_at(TARGET_MHZ)
    lines.append(f'<line class="target" x1="{left}" y1="{y_target:.2f}" x2="{right}" y2="{y_target:.2f}"/>')
    lines.append(f'<text x="{right-2}" y="{y_target-8:.2f}" font-size="13" text-anchor="end" fill="#a23b32">156.25 MHz target</text>')
    lines.extend([
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{bottom}"/>',
        f'<line class="axis" x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}"/>',
        f'<text x="24" y="{(top+bottom)/2:.0f}" font-size="14" transform="rotate(-90 24 {(top+bottom)/2:.0f})" text-anchor="middle">Routed Fmax (MHz)</text>',
        f'<text x="{(left+right)/2:.0f}" y="{bottom+40}" font-size="14" text-anchor="middle">nextpnr seed</text>',
    ])
    for index, seed in enumerate(seeds_a):
        x = x_at(index)
        lines.append(f'<text x="{x:.2f}" y="{bottom+23}" font-size="13" text-anchor="middle">{seed}</text>')

    for klass, values in (("a", values_a), ("b", values_b)):
        points = " ".join(f"{x_at(i):.2f},{y_at(v):.2f}" for i, v in enumerate(values))
        lines.append(f'<polyline class="{klass} series" points="{points}"/>')
        for i, value in enumerate(values):
            x, y = x_at(i), y_at(value)
            lines.append(f'<circle class="{klass}" cx="{x:.2f}" cy="{y:.2f}" r="5"/>')
            lines.append(f'<text x="{x:.2f}" y="{y-10:.2f}" font-size="11" text-anchor="middle">{value:.2f}</text>')

    lines.extend([
        '<line x1="610" y1="426" x2="642" y2="426" class="a series"/><circle class="a" cx="626" cy="426" r="4"/><text x="650" y="431" font-size="13">Architecture A</text>',
        '<line x1="610" y1="449" x2="642" y2="449" class="b series"/><circle class="b" cx="626" cy="449" r="4"/><text x="650" y="454" font-size="13">Architecture B (experiment)</text>',
        '<text x="82" y="454" font-size="11" fill="#536273">All five routes completed; every seed missed the target. No timing closure.</text>',
        '</svg>',
    ])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"generator={GENERATOR_VERSION} python={sys.version.split()[0]}")
    print(f"A {a_path.relative_to(ROOT)} sha256={sha256(a_path)} values={values_a}")
    print(f"B {b_path.relative_to(ROOT)} sha256={sha256(b_path)} values={values_b}")
    print(f"output={OUT.relative_to(ROOT)} sha256={sha256(OUT)}")


if __name__ == "__main__":
    main()
