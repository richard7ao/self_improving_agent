#!/usr/bin/env python3
"""Check exact matrix determinants, products, and linear-system solutions."""

from __future__ import annotations

import argparse
import json
import unittest
from fractions import Fraction
from pathlib import Path


def as_fraction(value) -> Fraction:
    return Fraction(str(value))


def determinant(matrix: list[list]) -> Fraction:
    rows = [[as_fraction(value) for value in row] for row in matrix]
    n = len(rows)
    if not n or any(len(row) != n for row in rows):
        raise ValueError("determinant requires a nonempty square matrix")
    sign = 1
    value = Fraction(1)
    for column in range(n):
        pivot = next((row for row in range(column, n) if rows[row][column]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != column:
            rows[column], rows[pivot] = rows[pivot], rows[column]
            sign *= -1
        pivot_value = rows[column][column]
        value *= pivot_value
        for row in range(column + 1, n):
            factor = rows[row][column] / pivot_value
            for index in range(column, n):
                rows[row][index] -= factor * rows[column][index]
    return sign * value


def solve(matrix: list[list], vector: list) -> list[Fraction]:
    rows = [[as_fraction(value) for value in row] + [as_fraction(vector[index])]
            for index, row in enumerate(matrix)]
    n = len(rows)
    if not n or len(vector) != n or any(len(row) != n + 1 for row in rows):
        raise ValueError("solve requires an n-by-n matrix and length-n vector")
    for column in range(n):
        pivot = next((row for row in range(column, n) if rows[row][column]), None)
        if pivot is None:
            raise ValueError("matrix is singular")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        pivot_value = rows[column][column]
        rows[column] = [value / pivot_value for value in rows[column]]
        for row in range(n):
            if row == column:
                continue
            factor = rows[row][column]
            rows[row] = [value - factor * pivot_value
                         for value, pivot_value in zip(rows[row], rows[column])]
    return [row[-1] for row in rows]


def rank(matrix: list[list]) -> int:
    rows = [[as_fraction(value) for value in row] for row in matrix]
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("rank requires a nonempty rectangular matrix")
    result = 0
    for column in range(len(rows[0])):
        pivot = next((row for row in range(result, len(rows)) if rows[row][column]), None)
        if pivot is None:
            continue
        rows[result], rows[pivot] = rows[pivot], rows[result]
        pivot_value = rows[result][column]
        rows[result] = [value / pivot_value for value in rows[result]]
        for row in range(len(rows)):
            if row == result:
                continue
            factor = rows[row][column]
            rows[row] = [value - factor * value_at_pivot
                         for value, value_at_pivot in zip(rows[row], rows[result])]
        result += 1
        if result == len(rows):
            break
    return result


def show(value: Fraction) -> dict:
    return {"exact": str(value), "decimal": float(value)}


class SelfTests(unittest.TestCase):
    def test_determinant(self) -> None:
        self.assertEqual(determinant([[1, 2], [3, 4]]), -2)

    def test_solve(self) -> None:
        self.assertEqual(solve([[2, 1], [1, -1]], [5, 1]), [Fraction(2), Fraction(1)])

    def test_rank(self) -> None:
        self.assertEqual(rank([[1, 2, 3], [2, 4, 6], [0, 1, 0]]), 2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("operation", nargs="?", choices=("determinant", "rank", "solve"))
    parser.add_argument("--matrix", type=Path)
    parser.add_argument("--vector", type=Path)
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)
        )
        return 0 if result.wasSuccessful() else 1
    if not args.operation or not args.matrix:
        parser.error("operation and --matrix are required")
    matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
    if args.operation == "determinant":
        output = {"determinant": show(determinant(matrix))}
    elif args.operation == "rank":
        output = {"rank": rank(matrix)}
    else:
        if not args.vector:
            parser.error("solve requires --vector")
        vector = json.loads(args.vector.read_text(encoding="utf-8"))
        output = {"solution": [show(value) for value in solve(matrix, vector)]}
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
