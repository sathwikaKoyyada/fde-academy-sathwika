"""
AutoFinance Bank — Shipments CSV Cleaner
FDE Academy Day 3 Exercise 1
"""

import pandas as pd
from pathlib import Path

VALID_STATUSES = {"in_transit", "delivered", "pending", "exception"}
VALID_CARRIERS = {"DHL", "FEDEX", "BLUEDART"}


def load_shipments(file_path: str) -> pd.DataFrame:
    """
    Load a shipments CSV file into a pandas DataFrame.
    Drop completely empty rows after loading.
    """
    df = pd.read_csv(file_path)
    df = df.dropna(how="all")
    return df.reset_index(drop=True)


def normalise_row(row: pd.Series) -> pd.Series:
    """
    Normalise string fields in a single row and return a fresh Series
    (avoids dtype conflicts when mixing strings, ints, and floats).
    """
    shipment_id = (
        str(row["shipment_id"]).strip() if pd.notna(row.get("shipment_id")) else None
    )
    carrier = (
        str(row["carrier"]).strip().upper() if pd.notna(row.get("carrier")) else None
    )
    status = str(row["status"]).strip().lower() if pd.notna(row.get("status")) else None
    origin = str(row["origin"]).strip().title() if pd.notna(row.get("origin")) else None
    destination = (
        str(row["destination"]).strip().title()
        if pd.notna(row.get("destination"))
        else None
    )
    delay = pd.to_numeric(str(row.get("delay_days", "")), errors="coerce")
    delay_days = None if pd.isna(delay) else int(delay)

    cost = pd.to_numeric(str(row.get("cost_usd", "")), errors="coerce")
    cost_usd = None if pd.isna(cost) else float(cost)

    return pd.Series(
        {
            "shipment_id": shipment_id,
            "carrier": carrier,
            "status": status,
            "origin": origin,
            "destination": destination,
            "delay_days": delay_days,
            "cost_usd": cost_usd,
        }
    )


def validate_row(row: pd.Series) -> list[str]:
    """
    Validate a (already normalised) row against business rules.
    """
    errors: list[str] = []

    shipment_id = row.get("shipment_id")
    if pd.isna(shipment_id) or str(shipment_id).strip() == "":
        errors.append("shipment_id must not be empty")

    if row.get("carrier") not in VALID_CARRIERS:
        errors.append("carrier must be in VALID_CARRIERS")

    if row.get("status") not in VALID_STATUSES:
        errors.append("status must be in VALID_STATUSES")

    delay = row.get("delay_days")
    if pd.isna(delay) or delay < 0:
        errors.append("delay_days must be >= 0")

    cost = row.get("cost_usd")
    if pd.isna(cost) or cost <= 0:
        errors.append("cost_usd must not be None and must be > 0")

    return errors


def clean_shipments(
    input_path: str,
    clean_output_path: str,
    rejected_output_path: str,
) -> dict:
    """
    Run the full cleaning pipeline.
    """
    df = load_shipments(input_path)

    normalised_rows = [normalise_row(row) for _, row in df.iterrows()]
    norm_df = pd.DataFrame(normalised_rows).reset_index(drop=True)

    all_errors = [validate_row(row) for _, row in norm_df.iterrows()]
    clean_mask = [len(e) == 0 for e in all_errors]
    rejected_mask = [not m for m in clean_mask]

    clean_df = norm_df[clean_mask].reset_index(drop=True)
    rejected_df = norm_df[rejected_mask].reset_index(drop=True)
    rejected_df["rejection_reasons"] = [", ".join(e) for e in all_errors if len(e) > 0]

    clean_df.to_csv(clean_output_path, index=False)
    rejected_df.to_csv(rejected_output_path, index=False)

    total_input = len(norm_df)
    clean_count = len(clean_df)
    rejected_count = len(rejected_df)
    rejection_rate_pct = (
        round(rejected_count / total_input * 100, 1) if total_input else 0.0
    )
    unique_reasons = sorted({r for e in all_errors for r in e})

    return {
        "total_input": total_input,
        "clean_count": clean_count,
        "rejected_count": rejected_count,
        "rejection_rate_pct": rejection_rate_pct,
        "rejection_reasons": unique_reasons,
    }


if __name__ == "__main__":
    summary = clean_shipments(
        input_path="shipments_raw.csv",
        clean_output_path="shipments_clean.csv",
        rejected_output_path="shipments_rejected.csv",
    )
    print("\n=== Data Quality Report ===")
    for key, value in summary.items():
        print(f"{key:<25} {value}")
