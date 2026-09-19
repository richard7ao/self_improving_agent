#!/usr/bin/env python3
"""Bounded deterministic checks for explicit computer-science models."""

from __future__ import annotations

import argparse
import collections
import json
import math
import unittest
from pathlib import Path

import finite_search


def run(operation: str, data: dict) -> dict:
    if operation == "graph_path":
        graph = {str(k): [str(v) for v in values] for k, values in data["graph"].items()}
        start, target = str(data["start"]), str(data["target"])
        queue = collections.deque([(start, [start])])
        seen = {start}
        while queue:
            node, path = queue.popleft()
            if node == target:
                return {"reachable": True, "path": path}
            for neighbor in graph.get(node, []):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return {"reachable": False, "path": None}
    if operation == "state_trace":
        state, trace = str(data["start"]), [str(data["start"])]
        transitions = {str(k): str(v) for k, v in data["transitions"].items()}
        for _ in range(int(data.get("max_steps", 100))):
            if state not in transitions:
                return {"trace": trace, "halted": True, "cycle": False}
            state = transitions[state]
            if state in trace:
                trace.append(state)
                return {"trace": trace, "halted": False, "cycle": True}
            trace.append(state)
        return {"trace": trace, "halted": False, "cycle": False, "bounded": True}
    if operation == "truth_table":
        names = sorted(data["variables"])
        search = finite_search.search({name: [False, True] for name in names}, data["expression"], 2 ** len(names))
        return search
    if operation == "recurrence":
        values = list(data["initial"])
        coefficients = list(data["coefficients"])
        count = int(data["count"])
        if not coefficients or len(values) < len(coefficients) or count > 100000:
            raise ValueError("invalid or excessive recurrence")
        constant = data.get("constant", 0)
        while len(values) < count:
            window = values[-len(coefficients):]
            values.append(sum(c * v for c, v in zip(coefficients, reversed(window))) + constant)
        return {"values": values[:count]}
    if operation == "shape":
        left, right = list(data["left"]), list(data["right"])
        if len(left) < 2 or len(right) < 2 or left[-1] != right[-2]:
            return {"compatible": False, "result": None}
        return {"compatible": True, "result": left[:-1] + right[-1:]}
    if operation == "complexity":
        n = int(data["n"])
        if not 1 <= n <= 100000:
            raise ValueError("n out of bounds")
        functions = {
            "1": lambda x: 1, "log2n": lambda x: math.log2(x), "n": lambda x: x,
            "nlog2n": lambda x: x * math.log2(x), "n2": lambda x: x * x,
            "2n": lambda x: 2 ** x, "factorial": math.factorial,
        }
        names = data["functions"]
        if any(name not in functions for name in names):
            raise ValueError("unsupported complexity function")
        values = {name: functions[name](n) for name in names}
        return {"values": values, "ascending": sorted(names, key=values.get)}
    raise ValueError(f"unsupported operation: {operation}")


class SelfTests(unittest.TestCase):
    def test_graph_recurrence_shape(self) -> None:
        self.assertEqual(run("graph_path", {"graph": {"a": ["b"], "b": ["c"]}, "start": "a", "target": "c"})["path"], ["a", "b", "c"])
        self.assertEqual(run("recurrence", {"initial": [0, 1], "coefficients": [1, 1], "count": 7})["values"], [0, 1, 1, 2, 3, 5, 8])
        self.assertEqual(run("shape", {"left": [2, 3], "right": [3, 4]})["result"], [2, 4])


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
