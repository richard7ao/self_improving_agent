#!/usr/bin/env python3
"""Apply and verify reversible text encodings and simple deterministic transformations."""

from __future__ import annotations

import argparse
import base64
import codecs
import json
import unittest


def transform(operation: str, text: str, shift: int = 13) -> str:
    if operation == "reverse":
        return text[::-1]
    if operation == "rot13":
        return codecs.decode(text, "rot_13")
    if operation == "caesar":
        result = []
        for char in text:
            if char.isascii() and char.isalpha():
                base = ord("A") if char.isupper() else ord("a")
                result.append(chr(base + (ord(char) - base + shift) % 26))
            else:
                result.append(char)
        return "".join(result)
    if operation == "base64-encode":
        return base64.b64encode(text.encode()).decode()
    if operation == "base64-decode":
        return base64.b64decode(text, validate=True).decode()
    if operation == "hex-encode":
        return text.encode().hex()
    if operation == "hex-decode":
        return bytes.fromhex(text).decode()
    raise ValueError(f"unknown operation: {operation}")


class SelfTests(unittest.TestCase):
    def test_round_trips(self) -> None:
        value = "Abc 123"
        self.assertEqual(transform("reverse", transform("reverse", value)), value)
        self.assertEqual(transform("base64-decode", transform("base64-encode", value)), value)
        self.assertEqual(transform("hex-decode", transform("hex-encode", value)), value)
        self.assertEqual(transform("caesar", transform("caesar", value, 7), -7), value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("operation", nargs="?",
                        choices=("reverse", "rot13", "caesar", "base64-encode",
                                 "base64-decode", "hex-encode", "hex-decode"))
    parser.add_argument("text", nargs="?")
    parser.add_argument("--shift", type=int, default=13)
    parser.add_argument("--round-trip", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)
        )
        return 0 if result.wasSuccessful() else 1
    if args.operation is None or args.text is None:
        parser.error("operation and text are required")
    output = transform(args.operation, args.text, args.shift)
    result = {"operation": args.operation, "output": output}
    if args.round_trip:
        inverse = {"reverse": "reverse", "rot13": "rot13", "caesar": "caesar",
                   "base64-encode": "base64-decode", "hex-encode": "hex-decode"}.get(args.operation)
        if inverse is None:
            raise SystemExit("--round-trip must start from an encoding/forward operation")
        shift = -args.shift if args.operation == "caesar" else args.shift
        result["round_trip"] = transform(inverse, output, shift)
        result["verified"] = result["round_trip"] == args.text
    print(json.dumps(result, indent=2))
    return 0 if result.get("verified", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
