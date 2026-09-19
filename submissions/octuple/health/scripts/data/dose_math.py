#!/usr/bin/env python3
"""Perform transparent dimensional dose arithmetic from explicit supplied inputs."""

from __future__ import annotations

from _common import number, run


WARNING = "Arithmetic only. This output does not select, validate, or prescribe a dose. Verify every input and clinical decision with a qualified clinician or pharmacist."


def dose(payload: dict) -> dict:
    weight = number(payload.get("weight_kg"), "weight_kg", nonnegative=True)
    rate = number(payload.get("amount_per_kg"), "amount_per_kg", nonnegative=True)
    amount_unit = payload.get("amount_unit", "mg")
    if amount_unit not in ("mg", "mcg", "g"):
        raise ValueError("amount_unit must be one of: mg, mcg, g")
    amount = weight * rate
    results = {"amount_per_administration": {"value": amount, "unit": amount_unit}}
    formulas = [f"{weight} kg * {rate} {amount_unit}/kg = {amount} {amount_unit}"]

    concentration = payload.get("concentration_amount_per_ml")
    if concentration is not None:
        concentration = number(concentration, "concentration_amount_per_ml", nonnegative=True)
        if concentration == 0:
            raise ValueError("concentration_amount_per_ml must be greater than zero")
        volume = amount / concentration
        results["volume_per_administration"] = {"value": volume, "unit": "mL"}
        formulas.append(f"{amount} {amount_unit} / {concentration} {amount_unit}/mL = {volume} mL")

    frequency = payload.get("administrations_per_day")
    if frequency is not None:
        frequency = number(frequency, "administrations_per_day", nonnegative=True)
        daily = amount * frequency
        results["daily_amount"] = {"value": daily, "unit": amount_unit}
        formulas.append(f"{amount} {amount_unit} * {frequency}/day = {daily} {amount_unit}/day")
        if concentration is not None:
            daily_volume = amount / concentration * frequency
            results["daily_volume"] = {"value": daily_volume, "unit": "mL"}
            formulas.append(f"{amount / concentration} mL * {frequency}/day = {daily_volume} mL/day")

    return {"inputs": payload, "results": results, "formulas": formulas, "warning": WARNING}


def self_test() -> None:
    result = dose({"weight_kg": 20, "amount_per_kg": 5, "amount_unit": "mg",
                   "concentration_amount_per_ml": 10, "administrations_per_day": 2})
    assert result["results"]["amount_per_administration"]["value"] == 100
    assert result["results"]["volume_per_administration"]["value"] == 10
    assert result["results"]["daily_amount"]["value"] == 200
    assert "does not" in result["warning"]


if __name__ == "__main__":
    run(dose, self_test, __doc__)
