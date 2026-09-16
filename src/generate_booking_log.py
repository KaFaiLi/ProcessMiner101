"""Generate a deterministic fictional investment-banking booking event log."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


CASE_ID = "case:concept:name"
ACTIVITY = "concept:name"
TIMESTAMP = "time:timestamp"

RESOURCE_POOLS = {
    "Trade Captured": ("trader_01", "trader_02", "trader_03"),
    "Validate Economics": ("ops_analyst_01", "ops_analyst_02", "ops_analyst_03"),
    "Amend Booking": ("ops_analyst_01", "ops_analyst_02", "ops_analyst_03"),
    "Enrich Counterparty": ("static_data_01", "static_data_02"),
    "Compliance Check": ("compliance_01", "compliance_02"),
    "Credit Check": ("credit_01", "credit_02"),
    "Supervisor Approval": ("supervisor_01", "supervisor_02"),
    "Manual Override": ("override_user_99",),
    "Confirm Booking": ("confirmations_01", "confirmations_02"),
    "Post to Ledger": ("ledger_bot_01",),
    "Booking Complete": ("workflow_bot_01",),
}

TYPICAL_MINUTES = {
    "Trade Captured": 0,
    "Validate Economics": 12,
    "Amend Booking": 18,
    "Enrich Counterparty": 10,
    "Compliance Check": 15,
    "Credit Check": 14,
    "Supervisor Approval": 35,
    "Manual Override": 5,
    "Confirm Booking": 20,
    "Post to Ledger": 8,
    "Booking Complete": 3,
}

ANOMALY_TYPES = (
    "skipped_compliance",
    "premature_ledger_posting",
    "excessive_rework",
    "extreme_delay",
    "unauthorized_manual_override",
)


def _normal_path(high_value: bool, rework: bool) -> list[str]:
    path = ["Trade Captured", "Validate Economics"]
    if rework:
        path.extend(["Amend Booking", "Validate Economics"])
    path.extend(["Enrich Counterparty", "Compliance Check", "Credit Check"])
    if high_value:
        path.append("Supervisor Approval")
    path.extend(["Confirm Booking", "Post to Ledger", "Booking Complete"])
    return path


def _anomalous_path(kind: str) -> list[str]:
    if kind == "skipped_compliance":
        return [
            "Trade Captured", "Validate Economics", "Enrich Counterparty",
            "Credit Check", "Supervisor Approval", "Confirm Booking",
            "Post to Ledger", "Booking Complete",
        ]
    if kind == "premature_ledger_posting":
        return [
            "Trade Captured", "Validate Economics", "Enrich Counterparty",
            "Compliance Check", "Credit Check", "Post to Ledger",
            "Supervisor Approval", "Confirm Booking", "Booking Complete",
        ]
    if kind == "excessive_rework":
        return [
            "Trade Captured", "Validate Economics",
            "Amend Booking", "Validate Economics",
            "Amend Booking", "Validate Economics",
            "Amend Booking", "Validate Economics",
            "Amend Booking", "Validate Economics",
            "Enrich Counterparty", "Compliance Check", "Credit Check",
            "Confirm Booking", "Post to Ledger", "Booking Complete",
        ]
    if kind == "extreme_delay":
        return _normal_path(high_value=False, rework=False)
    if kind == "unauthorized_manual_override":
        return [
            "Trade Captured", "Validate Economics", "Enrich Counterparty",
            "Compliance Check", "Manual Override", "Credit Check",
            "Confirm Booking", "Post to Ledger", "Booking Complete",
        ]
    raise ValueError(f"Unknown anomaly kind: {kind}")


def _business_start(start: pd.Timestamp, case_number: int) -> pd.Timestamp:
    candidate = start + pd.Timedelta(days=case_number // 4, hours=(case_number % 4) * 2)
    while candidate.dayofweek >= 5:
        candidate += pd.Timedelta(days=1)
    return candidate


def generate_event_log(
    seed: int = 42,
    baseline_cases: int = 120,
    monitoring_cases: int = 40,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the event log and a separate planted-anomaly answer key.

    Fifteen anomalies are planted when ``monitoring_cases`` is at least 15:
    three cases for each of five anomaly types. No anomaly label is included in
    the event-log DataFrame.
    """
    if baseline_cases < 1:
        raise ValueError("baseline_cases must be positive")
    if monitoring_cases < 15:
        raise ValueError("monitoring_cases must be at least 15")

    rng = np.random.default_rng(seed)
    products = np.array(["FX Forward", "Interest Rate Swap", "Equity Option"])
    desks = {"FX Forward": "FX", "Interest Rate Swap": "Rates", "Equity Option": "Equities"}
    currencies = np.array(["USD", "EUR", "GBP", "JPY"])
    tiers = np.array(["Tier 1", "Tier 2", "Tier 3"])

    anomaly_schedule: list[str | None] = [None] * monitoring_cases
    anomaly_slots = rng.choice(monitoring_cases, size=15, replace=False)
    for kind, slots in zip(ANOMALY_TYPES, np.array_split(anomaly_slots, 5), strict=True):
        for slot in slots:
            anomaly_schedule[int(slot)] = kind

    events: list[dict[str, object]] = []
    answers: list[dict[str, str]] = []
    total_cases = baseline_cases + monitoring_cases

    for case_index in range(total_cases):
        is_baseline = case_index < baseline_cases
        period = "baseline" if is_baseline else "monitoring"
        monitor_index = case_index - baseline_cases
        anomaly = None if is_baseline else anomaly_schedule[monitor_index]
        case_id = f"BK-{case_index + 1:04d}"

        product = str(rng.choice(products, p=[0.45, 0.35, 0.20]))
        currency = str(rng.choice(currencies, p=[0.48, 0.24, 0.18, 0.10]))
        tier = str(rng.choice(tiers, p=[0.55, 0.30, 0.15]))
        notional = float(np.round(rng.lognormal(mean=16.9, sigma=0.75), -3))

        # Structural anomaly paths are fixed to make the planted pattern teachable.
        if anomaly in {"skipped_compliance", "premature_ledger_posting"}:
            notional = 80_000_000.0
        elif anomaly in {"excessive_rework", "extreme_delay", "unauthorized_manual_override"}:
            notional = 12_000_000.0

        high_value = notional >= 50_000_000
        rework = bool(rng.random() < 0.14)
        path = _normal_path(high_value, rework) if anomaly is None else _anomalous_path(anomaly)

        base_date = pd.Timestamp("2026-01-05 08:00:00", tz="UTC")
        if not is_baseline:
            base_date = pd.Timestamp("2026-05-04 08:00:00", tz="UTC")
        current = _business_start(base_date, case_index if is_baseline else monitor_index)

        for event_index, activity in enumerate(path):
            if event_index:
                typical = TYPICAL_MINUTES[activity]
                elapsed = max(1, int(round(rng.lognormal(np.log(max(typical, 1)), 0.28))))
                if anomaly == "extreme_delay" and activity == "Confirm Booking":
                    elapsed += 72 * 60
                current += pd.Timedelta(minutes=elapsed)

            events.append(
                {
                    CASE_ID: case_id,
                    ACTIVITY: activity,
                    TIMESTAMP: current,
                    "org:resource": str(rng.choice(RESOURCE_POOLS[activity])),
                    "booking_period": period,
                    "desk": desks[product],
                    "product": product,
                    "currency": currency,
                    "counterparty_tier": tier,
                    "notional_usd": notional,
                }
            )

        if anomaly is not None:
            explanations = {
                "skipped_compliance": "The mandatory Compliance Check activity is absent.",
                "premature_ledger_posting": "The trade is posted before supervisor approval and confirmation.",
                "excessive_rework": "The booking cycles through amendment and validation four times.",
                "extreme_delay": "A 72-hour delay occurs before confirmation.",
                "unauthorized_manual_override": "An unapproved Manual Override activity appears in the trace.",
            }
            answers.append(
                {
                    CASE_ID: case_id,
                    "planted_anomaly": anomaly,
                    "rationale": explanations[anomaly],
                }
            )

    event_log = pd.DataFrame(events).sort_values([CASE_ID, TIMESTAMP], kind="stable").reset_index(drop=True)
    answer_key = pd.DataFrame(answers).sort_values(CASE_ID).reset_index(drop=True)
    return event_log, answer_key


def write_dataset(output_dir: Path, seed: int = 42) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    event_log, answer_key = generate_event_log(seed=seed)
    log_path = output_dir / "investment_banking_booking_log.csv"
    answer_path = output_dir / "instructor_outlier_answer_key.csv"
    event_log.to_csv(log_path, index=False, date_format="%Y-%m-%dT%H:%M:%SZ")
    answer_key.to_csv(answer_path, index=False)
    return log_path, answer_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    log_path, answer_path = write_dataset(args.output_dir, seed=args.seed)
    print(f"Wrote {log_path}")
    print(f"Wrote {answer_path}")


if __name__ == "__main__":
    main()

