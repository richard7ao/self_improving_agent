#!/usr/bin/env python3
"""Validate explicit chemical formulas, reactions, and quantity calculations."""

from __future__ import annotations

import argparse
import json
import re
import unittest
from collections import Counter
from pathlib import Path


MASSES = {"H": 1.008, "He": 4.0026, "Li": 6.94, "B": 10.81, "C": 12.011,
          "N": 14.007, "O": 15.999, "F": 18.998, "Na": 22.990, "Mg": 24.305,
          "Al": 26.982, "Si": 28.085, "P": 30.974, "S": 32.06, "Cl": 35.45,
          "K": 39.098, "Ca": 40.078, "Cr": 51.996, "Mn": 54.938, "Fe": 55.845,
          "Co": 58.933, "Ni": 58.693, "Cu": 63.546, "Zn": 65.38, "Br": 79.904,
          "Ag": 107.868, "I": 126.904, "Ba": 137.327, "Pt": 195.084, "Au": 196.967,
          "Hg": 200.592, "Pb": 207.2}
TOKEN = re.compile(r"([A-Z][a-z]?|\(|\)|\d+)")


def formula_counts(formula: str) -> Counter[str]:
    tokens = TOKEN.findall(formula)
    if "".join(tokens) != formula or not tokens:
        raise ValueError("unsupported formula syntax")
    stack = [Counter()]
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "(":
            stack.append(Counter())
        elif token == ")":
            if len(stack) == 1:
                raise ValueError("unmatched parenthesis")
            group = stack.pop()
            has_multiplier = index + 1 < len(tokens) and tokens[index + 1].isdigit()
            multiplier = int(tokens[index + 1]) if has_multiplier else 1
            if has_multiplier:
                index += 1
            for element, count in group.items():
                stack[-1][element] += count * multiplier
        elif token.isdigit():
            raise ValueError("unexpected coefficient")
        else:
            has_multiplier = index + 1 < len(tokens) and tokens[index + 1].isdigit()
            multiplier = int(tokens[index + 1]) if has_multiplier else 1
            if has_multiplier:
                index += 1
            stack[-1][token] += multiplier
        index += 1
    if len(stack) != 1:
        raise ValueError("unmatched parenthesis")
    return stack[0]


def side_totals(items: list[dict]) -> tuple[Counter[str], float]:
    atoms: Counter[str] = Counter()
    charge = 0.0
    for item in items:
        coefficient = float(item.get("coefficient", 1))
        for element, count in formula_counts(item["formula"]).items():
            atoms[element] += coefficient * count
        charge += coefficient * float(item.get("charge", 0))
    return atoms, charge


def run(operation: str, data: dict) -> dict:
    if operation == "formula":
        return {"atoms": dict(sorted(formula_counts(data["formula"]).items()))}
    if operation == "molar_mass":
        counts = formula_counts(data["formula"])
        missing = sorted(set(counts) - set(MASSES))
        if missing:
            raise ValueError("unknown masses: " + ", ".join(missing))
        return {"grams_per_mole": sum(MASSES[element] * count for element, count in counts.items())}
    if operation == "balance":
        left_atoms, left_charge = side_totals(data["reactants"])
        right_atoms, right_charge = side_totals(data["products"])
        return {"balanced": left_atoms == right_atoms and left_charge == right_charge,
                "left_atoms": dict(left_atoms), "right_atoms": dict(right_atoms),
                "left_charge": left_charge, "right_charge": right_charge}
    if operation == "limiting_reagent":
        ratios = {item["name"]: float(item["moles"]) / float(item["coefficient"]) for item in data["reactants"]}
        limiting = min(ratios, key=ratios.get)
        return {"limiting": limiting, "reaction_extent": ratios[limiting], "ratios": ratios}
    if operation == "stoichiometry":
        extent = float(data["known_moles"]) / float(data["known_coefficient"])
        return {"target_moles": extent * float(data["target_coefficient"]), "reaction_extent": extent}
    if operation == "concentration":
        return {"moles_per_litre": float(data["moles"]) / float(data["litres"])}
    if operation == "oxidation":
        counts = formula_counts(data["formula"])
        total = sum(float(data["states"][element]) * count for element, count in counts.items())
        charge = float(data.get("charge", 0))
        return {"sum": total, "charge": charge, "consistent": total == charge}
    if operation == "significant_figures":
        text = str(data["value"]).strip().lower()
        mantissa = text.split("e", 1)[0].lstrip("+-")
        digits = mantissa.replace(".", "").lstrip("0")
        if "." not in mantissa:
            digits = digits.rstrip("0")
        return {"significant_figures": len(digits)}
    raise ValueError(f"unsupported operation: {operation}")


class SelfTests(unittest.TestCase):
    def test_formula_balance_and_limiting(self) -> None:
        self.assertEqual(formula_counts("Ca(OH)2"), Counter({"O": 2, "H": 2, "Ca": 1}))
        self.assertEqual(formula_counts("H1Cl1"), Counter({"H": 1, "Cl": 1}))
        balanced = run("balance", {"reactants": [{"formula": "H2", "coefficient": 2}, {"formula": "O2"}], "products": [{"formula": "H2O", "coefficient": 2}]})
        self.assertTrue(balanced["balanced"])
        self.assertEqual(run("limiting_reagent", {"reactants": [{"name": "A", "moles": 2, "coefficient": 2}, {"name": "B", "moles": 3, "coefficient": 1}]})["limiting"], "A")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("operation", nargs="?")
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)).wasSuccessful() else 1
    if not args.operation or not args.input:
        parser.error("operation and --input are required")
    print(json.dumps(run(args.operation, json.loads(args.input.read_text())), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
