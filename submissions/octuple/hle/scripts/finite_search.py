#!/usr/bin/env python3
"""Enumerate a bounded Cartesian product and test a safe arithmetic/Boolean constraint."""

from __future__ import annotations

import argparse
import ast
import itertools
import json
import math
import operator
import unittest
from pathlib import Path


BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
          ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
          ast.Mod: operator.mod, ast.Pow: operator.pow}
COMPARE = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
           ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge}


def test_constraint(expression: str, values: dict[str, object]) -> bool:
    tree = ast.parse(expression, mode="eval")
    if sum(1 for _ in ast.walk(tree)) > 200:
        raise ValueError("constraint is too complex")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, bool)):
            return node.value
        if isinstance(node, ast.Name) and node.id in values:
            return values[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(float(right)) > 1000:
                raise ValueError("exponent is too large")
            return BINARY[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub, ast.Not)):
            value = visit(node.operand)
            return (+value if isinstance(node.op, ast.UAdd) else
                    -value if isinstance(node.op, ast.USub) else not value)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            items = [bool(visit(item)) for item in node.values]
            return all(items) if isinstance(node.op, ast.And) else any(items)
        if isinstance(node, ast.Compare):
            left = visit(node.left)
            for operation, comparator in zip(node.ops, node.comparators):
                right = visit(comparator)
                if type(operation) not in COMPARE or not COMPARE[type(operation)](left, right):
                    return False
                left = right
            return True
        raise ValueError(f"unsupported constraint element: {type(node).__name__}")

    return bool(visit(tree))


def search(domains: dict[str, list], constraint: str, max_cases: int) -> dict:
    names = sorted(domains)
    total = math.prod(len(domains[name]) for name in names)
    if total > max_cases:
        raise ValueError(f"search has {total} cases, above limit {max_cases}")
    matches = []
    for combination in itertools.product(*(domains[name] for name in names)):
        values = dict(zip(names, combination))
        if test_constraint(constraint, values):
            matches.append(values)
    return {"variables": names, "cases": total, "matches": matches, "n_matches": len(matches)}


class SelfTests(unittest.TestCase):
    def test_search(self) -> None:
        result = search({"x": [0, 1, 2], "y": [0, 1, 2]}, "x + y == 2", 100)
        self.assertEqual(result["n_matches"], 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--domains", type=Path, help="JSON object mapping names to finite arrays")
    parser.add_argument("--constraint")
    parser.add_argument("--max-cases", type=int, default=100000)
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)
        )
        return 0 if result.wasSuccessful() else 1
    if not args.domains or not args.constraint:
        parser.error("--domains and --constraint are required")
    domains = json.loads(args.domains.read_text(encoding="utf-8"))
    print(json.dumps(search(domains, args.constraint, args.max_cases), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
