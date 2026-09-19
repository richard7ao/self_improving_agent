#!/usr/bin/env python3
"""Route a structured HLE problem specification to included offline helpers."""

from __future__ import annotations

import argparse
import json
import unittest
from pathlib import Path
from typing import Any


DOMAINS = {
    "computer_science_ai", "chemistry", "engineering_physics", "image",
    "factual_recall", "mathematics_statistics", "biology_medicine",
    "earth_space_science", "social_science", "humanities_law", "mixed",
    "uncertain", "other",
}
DOMAIN_ALIASES = {
    "computer_science": "computer_science_ai", "cs": "computer_science_ai",
    "engineering": "engineering_physics", "physics": "engineering_physics",
    "factual": "factual_recall", "image_semantics": "image",
    "mixed_or_uncertain": "mixed",
    "mathematics": "mathematics_statistics", "statistics": "mathematics_statistics",
    "biology": "biology_medicine", "medicine": "biology_medicine",
    "earth_science": "earth_space_science", "astronomy": "earth_space_science",
    "social_sciences": "social_science", "humanities": "humanities_law", "law": "humanities_law",
}
TASK_TYPES = {
    "factual", "numerical", "symbolic", "code_trace", "algorithm", "proof",
    "existence", "sufficiency", "necessity", "minimum", "maximum", "uniqueness",
    "transformation", "image_interpretation", "multiple_choice",
}
TASK_ALIASES = {
    "factual_recall": "factual", "factual_identification": "factual",
    "logical_reasoning": "proof", "conceptual": "proof",
    "multiple_choice_conceptual": "multiple_choice", "minimum/maximum": "minimum",
    "image": "image_interpretation", "cipher": "transformation",
}
ANSWER_TYPES = {
    "exactMatch", "multipleChoice", "number", "expression", "string", "entity",
    "formula", "shortExplanation",
}
FEATURES = {
    "arithmetic", "fractions", "combinatorics", "finite_search", "equations",
    "matrix", "rank", "units", "dimensions", "code", "graph", "truth_table",
    "recurrence", "encoding", "cipher", "tensor_shape", "complexity",
    "chemical_formula", "reaction", "stoichiometry", "oxidation", "concentration",
    "force_balance", "circuit", "conservation", "error_propagation", "residual",
    "boundary", "image_labels", "plot", "geometry", "minimum", "uniqueness",
    "symmetry", "precision", "formatting", "significant_figures",
}


def tool(name: str, priority: int, status: str, reason: str, uncertainty: str,
         when: str, inputs: list[str], stop: str, contraindications: str,
         entry_point: str) -> dict[str, Any]:
    return {
        "tool": name, "entry_point": entry_point, "priority": priority,
        "status": status, "required": status == "required", "reason": reason,
        "uncertainty_reduced": uncertainty, "when": when, "inputs": inputs,
        "stopping_condition": stop, "contraindications": contraindications,
    }


def _response_guard() -> dict[str, Any]:
    return tool(
        "response_guard", 10, "required", "Protect response delivery and validate the saved contract.",
        "Whether a gradeable non-empty answer exists.", "As soon as a defensible candidate exists and once after final revision.",
        ["answer", "explanation", "confidence", "output contract"],
        "The response is atomically saved, non-empty, and schema-valid.",
        "Use raw mode when the task requires a schema other than the default three fields.",
        "scripts/response_guard.py",
    )


def _format_validator(required: bool) -> dict[str, Any]:
    return tool(
        "format_validator", 90, "required" if required else "recommended",
        "Check exact answer representation before submission.",
        "Capitalization, label, units, precision, ordering, or alternative-answer errors.",
        "After the answer is settled and before final response validation.",
        ["answer", "answer type", "required pattern/options/units/precision"],
        "Exactly one answer satisfies the declared contract.",
        "It validates form, not semantic correctness.", "scripts/hle_review.py:answer_format",
    )


def _review_tools() -> list[dict[str, Any]]:
    return [
        tool(
            "adversarial_reviewer", 70, "required",
            "Attack the first unsupported inference and strongest competing answer.",
            "Necessity/sufficiency confusion, hidden assumptions, counterexamples, and unused variables.",
            "After deriving a candidate and before confidence calibration.",
            ["interpreted question", "candidate", "competitor", "variable ledger", "proof statuses"],
            "No material counterexample survives, or the candidate is revised.",
            "This is an internal learner protocol, not an external LLM or correctness oracle.",
            "references/reviewer_protocol.md",
        ),
        tool(
            "confidence_calibrator", 80, "required",
            "Apply evidence-based confidence caps and expose unresolved objections.",
            "Unjustified confidence caused by missing proof obligations or evidence.",
            "After adversarial review and deterministic checks.",
            ["review statuses", "unused variables", "unit/sign/image uncertainty", "requested confidence"],
            "All mandatory caps are applied and unresolved assumptions are reported.",
            "A calibrated percentage does not make a wrong premise correct.",
            "scripts/hle_review.py",
        ),
    ]


def _add(destination: dict[str, dict[str, Any]], recommendation: dict[str, Any]) -> None:
    current = destination.get(recommendation["tool"])
    if current is None or recommendation["priority"] < current["priority"]:
        destination[recommendation["tool"]] = recommendation


def route(spec: dict[str, Any]) -> dict[str, Any]:
    domain = DOMAIN_ALIASES.get(str(spec.get("domain", "")), str(spec.get("domain", "")))
    raw_types = spec.get("task_types", spec.get("task_type", []))
    if isinstance(raw_types, str):
        raw_types = [item.strip() for item in raw_types.split(",") if item.strip()]
    task_types = {TASK_ALIASES.get(str(item), str(item)) for item in raw_types}
    answer_type = str(spec.get("answer_type", ""))
    raw_features = spec.get("features", [])
    if isinstance(raw_features, str):
        raw_features = [item.strip() for item in raw_features.split(",") if item.strip()]
    features = set(raw_features)
    has_image = spec.get("has_image", False)
    if isinstance(has_image, str):
        if has_image.lower() not in {"true", "false"}:
            raise ValueError("has_image must be true or false")
        has_image = has_image.lower() == "true"

    if domain not in DOMAINS:
        raise ValueError(f"invalid domain: {domain}")
    if not task_types or not task_types <= TASK_TYPES:
        raise ValueError(f"invalid task type(s): {sorted(task_types - TASK_TYPES)}")
    if answer_type not in ANSWER_TYPES:
        raise ValueError(f"invalid answer type: {answer_type}")
    unmapped_features = sorted(features - FEATURES)
    features &= FEATURES

    general: dict[str, dict[str, Any]] = {}
    domain_tools: dict[str, dict[str, Any]] = {}
    warnings = [
        "Tools validate the learner's selected model; they do not choose the governing model or answer the expert question.",
        "Stop tool use once the discriminating uncertainty is resolved.",
    ]
    if unmapped_features:
        warnings.append("Unmapped feature flags were retained only as semantic notes: " + ", ".join(unmapped_features))
    image_plan: list[str] = []
    review_checks: list[str] = []
    _add(general, _response_guard())

    exact_contract = answer_type in {"exactMatch", "multipleChoice"} or bool(
        task_types & {"multiple_choice"}
    )
    if exact_contract or features & {"formatting", "precision", "significant_figures", "units"}:
        _add(general, _format_validator(exact_contract))

    if features & {"arithmetic", "fractions", "combinatorics", "precision"} or (
        "numerical" in task_types and domain != "factual_recall"
    ):
        _add(general, tool(
            "exact_math", 35, "recommended", "Recompute material arithmetic exactly or at controlled precision.",
            "Arithmetic, fraction, power, root, combinatoric, or rounding error.",
            "After deriving the governing expression.", ["expression", "optional independent expression/tolerance"],
            "The values agree or the discrepancy is explained.",
            "Do not use it to choose a formula, scientific model, or semantic interpretation.",
            "scripts/exact_math.py",
        ))
    if features & {"finite_search", "combinatorics", "truth_table"}:
        _add(general, tool(
            "finite_search", 40, "recommended", "Exhaust bounded cases or seek a small counterexample.",
            "Incomplete finite case coverage.", "After defining complete finite domains and an exact constraint.",
            ["finite domains JSON", "Boolean constraint", "maximum case count"],
            "All bounded cases are exhausted or one decisive counterexample is found.",
            "Do not use for unbounded, huge, approximate, or semantically underspecified spaces.",
            "scripts/finite_search.py",
        ))
    if features & {"matrix", "rank", "equations"}:
        _add(general, tool(
            "matrix_check", 40, "recommended", "Check a justified linear system, determinant, or rank.",
            "Algebraic solution, singularity, rank, or affine-independence error.",
            "After the learner constructs and justifies the equations.", ["matrix JSON", "optional vector JSON", "operation"],
            "The exact result is obtained and substituted into the original model.",
            "Do not infer that the matrix represents the problem merely because it is solvable.",
            "scripts/matrix_check.py",
        ))
    if features & {"encoding", "cipher"} or "transformation" in task_types:
        _add(general, tool(
            "text_transform", 40, "recommended", "Apply and round-trip a reversible transformation.",
            "Direction, shift, capitalization, punctuation, or encoding errors.",
            "After the mapping and direction have been inferred.", ["operation", "text", "optional shift"],
            "The inverse transform reproduces the original exactly.",
            "Do not use for ordinary factual or semantic questions or to infer an unknown cipher family.",
            "scripts/text_transform.py",
        ))

    if domain == "computer_science_ai":
        review_checks += ["off-by-one", "empty or zero input", "indexing convention",
                          "mutation and hidden state", "integer versus floating point",
                          "overflow or truncation", "worst versus average case",
                          "complexity versus output size", "encoding direction", "base/log convention"]
        cs_features = features & {"code", "graph", "truth_table", "recurrence", "tensor_shape", "complexity"}
        if cs_features or task_types & {"code_trace", "algorithm"}:
            _add(domain_tools, tool(
                "cs_check", 45, "recommended", "Run a bounded CS trace, recurrence, graph, truth-table, shape, or complexity comparison.",
                "State-transition, reachability, recurrence, shape, or asymptotic comparison errors.",
                "After formal semantics, inputs, and indexing conventions are stated.",
                ["operation", "structured inputs", "bounds/initial state as applicable"],
                "The bounded trace/check reaches the claimed output or exposes a mismatch.",
                "It cannot verify conceptual or factual AI knowledge or unspecified language semantics.",
                "scripts/cs_check.py",
            ))
    elif domain == "chemistry":
        review_checks += ["atom conservation", "charge conservation", "limiting reagent",
                          "oxidation state", "kinetic versus thermodynamic product",
                          "stereochemistry", "solvent/catalyst/temperature", "phase", "isomers", "unit conversion"]
        if features & {"chemical_formula", "reaction", "stoichiometry", "oxidation", "concentration", "significant_figures"}:
            _add(domain_tools, tool(
                "chem_check", 45, "recommended", "Validate formula, balance, charge, molar mass, stoichiometry, oxidation, concentration, or significant figures.",
                "Composition, conservation, reagent, oxidation, quantity, or rounding errors.",
                "After the learner selects and justifies the species, reaction, and governing model.",
                ["operation", "formulas/reaction", "coefficients", "charges or quantities as applicable"],
                "Atoms/charge/quantities balance and the result respects declared conditions.",
                "It validates a chosen reaction; it does not select a mechanism, product, phase, or stereochemistry.",
                "scripts/chem_check.py",
            ))
        warnings.append("Chemistry helpers validate a selected reaction or model; they do not reliably choose the reaction mechanism.")
    elif domain == "engineering_physics":
        review_checks += ["RMS versus peak", "degrees versus radians", "gauge versus absolute",
                          "sign convention", "series versus parallel", "steady state versus transient",
                          "boundary conditions", "singularity", "physical scale", "conservation"]
        if features & {"units", "dimensions", "force_balance", "circuit", "conservation",
                       "error_propagation", "residual", "boundary"}:
            _add(domain_tools, tool(
                "engineering_check", 45, "recommended", "Check units, dimensions, balances, conservation, residuals, uncertainty, or boundary behavior.",
                "Dimensional, sign, conservation, scale, residual, or limiting-case errors.",
                "After the physical system, boundary, conventions, and governing laws are justified.",
                ["operation", "equations/terms", "units", "values and boundary cases as applicable"],
                "The stated model is dimensionally and numerically consistent within tolerance.",
                "It cannot choose the governing physical model or repair wrong boundary conditions.",
                "scripts/engineering_check.py",
            ))
        warnings.append("The learner must select and justify the governing physical model before using engineering helpers.")
    elif domain == "factual_recall":
        review_checks += ["requested entity", "qualifiers", "dates", "terminology", "scope"]
        warnings.append("No deterministic helper may reduce the central factual uncertainty; avoid irrelevant calculations.")
    elif domain == "mathematics_statistics":
        review_checks += ["definitions and quantifiers", "necessity versus sufficiency",
                          "boundary and degenerate cases", "exact versus asymptotic claim",
                          "sampling assumptions"]
        warnings.append("Choose and justify the theorem or probabilistic model; general tools only verify its consequences.")
    elif domain == "biology_medicine":
        review_checks += ["level of organization", "causal versus associative claim",
                          "species/population/context qualifier", "mechanism assumptions",
                          "measurement and statistical uncertainty"]
        warnings.append("No included tool selects a biological mechanism or clinical interpretation; use deterministic checks only for supplied quantities.")
    elif domain == "earth_space_science":
        review_checks += ["reference frame", "spatial and temporal scale", "sign/unit convention",
                          "model regime", "observational versus inferred claim"]
        warnings.append("Select the physical/geoscientific model from domain knowledge before routing calculations.")
    elif domain == "social_science":
        review_checks += ["construct definition", "causal versus correlational claim",
                          "population and period", "measurement validity", "alternative explanation"]
        warnings.append("Deterministic tools cannot establish contested interpretation or causal identification from keywords.")
    elif domain == "humanities_law":
        review_checks += ["jurisdiction or canon", "date and scope", "primary concept definition",
                          "competing interpretation", "quotation or attribution uncertainty"]
        warnings.append("Deterministic tools cannot resolve interpretive, legal, historical, or attribution questions without supplied evidence.")
    elif domain == "other":
        review_checks += ["domain definition", "scope and terminology", "alternative interpretation",
                          "which supplied features are mechanically checkable"]
        warnings.append("Unlisted domain: use feature-driven general tools only and state the governing subject model explicitly.")
    elif domain in {"mixed", "uncertain"}:
        review_checks += ["domain boundary", "alternative domain interpretation", "unused conditions"]
        warnings.append("Domain is ambiguous: choose the primary adapter from problem semantics before using a specialized helper.")

    if has_image or domain == "image" or "image_interpretation" in task_types:
        image_plan = [
            "Locate the task image without browsing the network.", "Inspect the complete image and dimensions.",
            "Crop relevant regions without discarding context.", "Enlarge small labels and adjust contrast only when useful.",
            "Record which claims are directly visible and which are inferred.",
            "Route extracted evidence to the appropriate subject adapter.",
        ]
        _add(domain_tools, tool(
            "image_prepare", 20, "recommended", "Discover images and prepare bounded crops/enlargements for human interpretation.",
            "Missed labels, axes, structures, regions, or surrounding context.",
            "Before domain reasoning when the answer depends on the image.",
            ["image path or search root", "optional crop box", "scale/contrast if available"],
            "Relevant regions and full context have been inspected and visible claims recorded.",
            "OCR/preprocessing does not prove semantic meaning; do not infer invisible details.",
            "scripts/image_prepare.py",
        ))
        review_checks += ["axis and scale", "linear versus logarithmic axis", "legend/color mapping",
                          "object-label association", "stereochemical bond direction", "cropped-away context",
                          "diagram not drawn to scale", "visible evidence versus inference"]

    if task_types & {"minimum", "maximum", "necessity", "uniqueness", "proof"} or features & {
        "minimum", "uniqueness", "symmetry", "geometry"
    }:
        review_checks += ["necessity separate from sufficiency", "matching bound directions",
                          "indistinguishable states", "symmetry or coordinate ambiguity", "degenerate cases"]

    for recommendation in _review_tools():
        _add(general, recommendation)

    general_list = sorted(general.values(), key=lambda item: (item["priority"], item["tool"]))
    domain_list = sorted(domain_tools.values(), key=lambda item: (item["priority"], item["tool"]))
    ordered = sorted(general_list + domain_list, key=lambda item: (item["priority"], item["tool"]))
    human_plan = [f"{index + 1}. {item['tool']}: {item['when']} Stop when {item['stopping_condition']}"
                  for index, item in enumerate(ordered)]
    return {
        "domain": domain, "task_types": sorted(task_types), "answer_type": answer_type,
        "has_image": bool(has_image), "features": sorted(features),
        "unmapped_features": unmapped_features,
        "always_use_general_tools": [item for item in general_list if item["status"] == "required"],
        "optional_general_tools": [item for item in general_list if item["status"] != "required"],
        "domain_tools": domain_list, "image_plan": image_plan,
        "review_checks": list(dict.fromkeys(review_checks)), "warnings": list(dict.fromkeys(warnings)),
        "human_plan": human_plan,
    }


def _spec(domain: str, task_types: list[str], answer_type: str, features: list[str],
          has_image: bool = False) -> dict[str, Any]:
    return {"domain": domain, "task_types": task_types, "answer_type": answer_type,
            "features": features, "has_image": has_image}


class SelfTests(unittest.TestCase):
    def assert_tools(self, result: dict[str, Any], included: set[str], excluded: set[str] = set()) -> None:
        tools = {item["tool"] for key in ("always_use_general_tools", "optional_general_tools", "domain_tools")
                 for item in result[key]}
        self.assertTrue(included <= tools, (included, tools))
        self.assertFalse(excluded & tools, (excluded, tools))
        priorities = [int(line.split(".", 1)[0]) for line in result["human_plan"]]
        self.assertEqual(priorities, list(range(1, len(priorities) + 1)))
        for item in [entry for key in ("always_use_general_tools", "optional_general_tools", "domain_tools")
                     for entry in result[key]]:
            self.assertTrue(item["inputs"] and item["stopping_condition"] and item["contraindications"])

    def test_cs_code_trace(self) -> None:
        self.assert_tools(route(_spec("computer_science_ai", ["code_trace"], "exactMatch", ["code"])),
                          {"response_guard", "cs_check", "format_validator"}, {"chem_check"})

    def test_cs_finite_combinatorial(self) -> None:
        self.assert_tools(route(_spec("computer_science_ai", ["algorithm"], "number", ["finite_search", "combinatorics"])),
                          {"finite_search", "exact_math", "cs_check"})

    def test_chemistry_stoichiometry(self) -> None:
        self.assert_tools(route(_spec("chemistry", ["numerical"], "number", ["stoichiometry", "units"])),
                          {"chem_check", "exact_math"}, {"cs_check"})

    def test_chemistry_reaction_balance(self) -> None:
        self.assert_tools(route(_spec("chemistry", ["sufficiency"], "formula", ["reaction", "chemical_formula"])),
                          {"chem_check"})

    def test_engineering_dimensions(self) -> None:
        self.assert_tools(route(_spec("engineering", ["numerical"], "expression", ["units", "dimensions"])),
                          {"engineering_check", "exact_math"}, {"chem_check"})

    def test_engineering_matrix_circuit(self) -> None:
        self.assert_tools(route(_spec("engineering_physics", ["numerical"], "number", ["matrix", "rank", "circuit"])),
                          {"matrix_check", "engineering_check"})

    def test_image_chemistry(self) -> None:
        result = route(_spec("chemistry", ["image_interpretation"], "multipleChoice", ["image_labels", "reaction"], True))
        self.assert_tools(result, {"image_prepare", "chem_check", "format_validator"})
        self.assertTrue(result["image_plan"])

    def test_image_engineering(self) -> None:
        result = route(_spec("engineering_physics", ["image_interpretation"], "exactMatch", ["plot", "units"], True))
        self.assert_tools(result, {"image_prepare", "engineering_check", "format_validator"})

    def test_factual_exact_match_avoids_calculators(self) -> None:
        self.assert_tools(route(_spec("factual_recall", ["factual"], "exactMatch", [])),
                          {"response_guard", "format_validator"}, {"exact_math", "finite_search", "matrix_check"})

    def test_multiple_choice(self) -> None:
        self.assert_tools(route(_spec("computer_science_ai", ["multiple_choice"], "multipleChoice", [])),
                          {"format_validator", "adversarial_reviewer"})

    def test_minimum_uniqueness(self) -> None:
        result = route(_spec("engineering_physics", ["minimum", "uniqueness"], "expression", ["matrix", "rank", "symmetry"] ))
        self.assert_tools(result, {"matrix_check", "adversarial_reviewer", "confidence_calibrator"})
        self.assertIn("necessity separate from sufficiency", result["review_checks"])

    def test_uncertain_domain_warns(self) -> None:
        result = route(_spec("uncertain", ["proof"], "shortExplanation", []))
        self.assertTrue(any("ambiguous" in warning for warning in result["warnings"]))

    def test_invalid_input(self) -> None:
        with self.assertRaises(ValueError):
            route(_spec("invalid", ["factual"], "entity", []))

    def test_redundant_exact_tools_are_removed_and_json_is_stable(self) -> None:
        spec = _spec("computer_science_ai", ["numerical"], "number", ["arithmetic", "fractions", "combinatorics"])
        result = route(spec)
        names = [item["tool"] for key in ("always_use_general_tools", "optional_general_tools", "domain_tools")
                 for item in result[key]]
        self.assertEqual(names.count("exact_math"), 1)
        self.assertEqual(json.dumps(result, sort_keys=True), json.dumps(route(spec), sort_keys=True))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--self-test", action="store_true")
    sub = root.add_subparsers(dest="command")
    route_parser = sub.add_parser("route")
    route_parser.add_argument("--domain", required=True)
    route_parser.add_argument("--task-type", required=True, help="comma-separated task types")
    route_parser.add_argument("--answer-type")
    route_parser.add_argument("--answer", dest="answer_alias", help=argparse.SUPPRESS)
    route_parser.add_argument("--has-image", default="false")
    route_parser.add_argument("--features", default="")
    suggest = sub.add_parser("suggest")
    suggest.add_argument("--spec", required=True, type=Path)
    return root


def main() -> int:
    args = parser().parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    try:
        if args.command == "route":
            spec = {"domain": args.domain, "task_type": args.task_type,
                    "answer_type": args.answer_alias or args.answer_type, "has_image": args.has_image,
                    "features": args.features}
        elif args.command == "suggest":
            spec = json.loads(args.spec.read_text(encoding="utf-8"))
            if not isinstance(spec, dict):
                raise ValueError("spec must be a JSON object")
        else:
            parser().error("choose route or suggest, or pass --self-test")
        print(json.dumps(route(spec), indent=2, sort_keys=False))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
