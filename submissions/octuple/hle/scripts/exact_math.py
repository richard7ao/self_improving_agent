#!/usr/bin/env python3
"""Evaluate or compare bounded arithmetic expressions without Python eval."""

from __future__ import annotations

import argparse
import ast
import json
import math
import operator
import unittest
from fractions import Fraction


BINARY = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}
UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
FUNCTIONS = {
    "abs": abs, "ceil": math.ceil, "comb": math.comb, "factorial": math.factorial,
    "floor": math.floor, "gcd": math.gcd, "lcm": math.lcm, "perm": math.perm,
    "sqrt": math.sqrt,
}
CONSTANTS = {"pi": math.pi, "e": math.e}


def calculate(expression: str):
    tree = ast.parse(expression, mode="eval")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name) and node.id in CONSTANTS:
            return CONSTANTS[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(float(right)) > 10000:
                raise ValueError("exponent is too large")
            if isinstance(node.op, ast.Div) and isinstance(left, int) and isinstance(right, int):
                return Fraction(left, right)
            return BINARY[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
            return UNARY[type(node.op)](visit(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS:
            if node.keywords:
                raise ValueError("keyword arguments are not supported")
            return FUNCTIONS[node.func.id](*(visit(argument) for argument in node.args))
        raise ValueError(f"unsupported expression element: {type(node).__name__}")

    return visit(tree)


def serializable(value):
    if isinstance(value, Fraction):
        return {"exact": f"{value.numerator}/{value.denominator}", "decimal": float(value)}
    return value


class SelfTests(unittest.TestCase):
    def test_fraction(self) -> None:
        self.assertEqual(calculate("1/3 + 1/6"), Fraction(1, 2))

    def test_rejects_attribute(self) -> None:
        with self.assertRaises(ValueError):
            calculate("object.method()")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("expression", nargs="?")
    parser.add_argument("--expected")
    parser.add_argument("--rel-tol", type=float, default=1e-9)
    parser.add_argument("--abs-tol", type=float, default=0.0)
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)
        )
        return 0 if result.wasSuccessful() else 1
    if not args.expression:
        parser.error("expression is required")
    value = calculate(args.expression)
    output = {"expression": args.expression, "value": serializable(value)}
    if args.expected is not None:
        expected = calculate(args.expected)
        output["expected"] = serializable(expected)
        output["matches"] = math.isclose(float(value), float(expected),
                                         rel_tol=args.rel_tol, abs_tol=args.abs_tol)
    print(json.dumps(output, indent=2))
    return 0 if output.get("matches", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
