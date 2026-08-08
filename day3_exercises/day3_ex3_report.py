"""
AutoFinance Bank — Daily Shipment Operations Report
FDE Academy Day 3 Exercise 3

Usage:
    python day3_ex3_report.py

Outputs:
    - Console: formatted KPI report
    - shipments_summary.csv: per-carrier aggregated KPIs
    - route_report.csv: top routes by volume
"""

import pandas as pd
from pathlib import Path
from datetime import date

INPUT_FILE = "shipments_clean.csv"
SUMMARY_CSV = "shipments_summary.csv"
ROUTES_CSV = "route_report.csv"


def compute_carrier_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-carrier KPIs from the cleaned shipments DataFrame.
    Sorted by total_shipments descending.
    """
    records = []
    for carrier, group in df.groupby("carrier"):
        total = len(group)
        delivered = int((group["status"] == "delivered").sum())
        in_transit = int((group["status"] == "in_transit").sum())
        otif_rows = group[(group["delay_days"] == 0) & (group["status"] == "delivered")]
        otif_pct = round(len(otif_rows) / total * 100, 1) if total else 0.0
        avg_delay = round(group["delay_days"].mean(), 1)
        max_delay = int(group["delay_days"].max())
        total_revenue = round(group["cost_usd"].sum(), 2)
        avg_cost = round(group["cost_usd"].mean(), 2)

        records.append(
            {
                "carrier": carrier,
                "total_shipments": total,
                "delivered": delivered,
                "in_transit": in_transit,
                "otif_pct": otif_pct,
                "avg_delay_days": avg_delay,
                "max_delay_days": max_delay,
                "total_revenue": total_revenue,
                "avg_cost_per_ship": avg_cost,
            }
        )

    result = pd.DataFrame(records)
    return result.sort_values("total_shipments", ascending=False).reset_index(drop=True)


def compute_route_report(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """
    Compute a route-level report grouped by (origin, destination) pair.
    Returns only the top_n routes by shipment_count.
    """
    records = []
    for (origin, destination), group in df.groupby(["origin", "destination"]):
        route = f"{origin} -> {destination}"
        shipment_count = len(group)
        avg_delay = round(group["delay_days"].mean(), 1)
        total_revenue = round(group["cost_usd"].sum(), 2)
        most_used_carrier = group["carrier"].value_counts().idxmax()

        records.append(
            {
                "route": route,
                "shipment_count": shipment_count,
                "avg_delay_days": avg_delay,
                "total_revenue": total_revenue,
                "most_used_carrier": most_used_carrier,
            }
        )

    result = pd.DataFrame(records)
    result = result.sort_values("shipment_count", ascending=False).reset_index(
        drop=True
    )
    return result.head(top_n)


def print_console_report(
    df: pd.DataFrame,
    carrier_kpis: pd.DataFrame,
    route_report: pd.DataFrame,
) -> None:
    """Print a formatted operations report to the console."""
    today = date.today().isoformat()
    total_shipments = len(df)
    total_revenue = round(df["cost_usd"].sum(), 2)

    otif_rows = df[(df["delay_days"] == 0) & (df["status"] == "delivered")]
    overall_otif = (
        round(len(otif_rows) / total_shipments * 100, 1) if total_shipments else 0.0
    )
    avg_delay = round(df["delay_days"].mean(), 1)

    print(f"\n=== AutoFinance Bank — Daily Shipment Report [{today}] ===\n")
    print(
        f"Total Shipments: {total_shipments} | "
        f"Total Revenue: ${total_revenue:,.2f} | "
        f"Overall OTIF: {overall_otif}% | "
        f"Avg Delay: {avg_delay} days"
    )

    print("\n=== Carrier KPIs ===")
    print(
        f"{'Carrier':<10}{'Shipments':<12}{'Delivered':<12}{'OTIF%':<10}{'AvgDelay':<10}{'Revenue':<10}"
    )
    for _, row in carrier_kpis.iterrows():
        print(
            f"{row['carrier']:<10}{row['total_shipments']:<12}{row['delivered']:<12}"
            f"{row['otif_pct']:<10}{row['avg_delay_days']:<10}${row['total_revenue']:,.2f}"
        )

    print("\n=== Top Routes ===")
    print(f"{'Route':<25}{'Count':<8}{'AvgDelay':<10}{'Revenue':<10}")
    for _, row in route_report.iterrows():
        print(
            f"{row['route']:<25}{row['shipment_count']:<8}"
            f"{row['avg_delay_days']:<10}${row['total_revenue']:,.2f}"
        )

    flagged = df[df["delay_days"] > 3]
    print("\nFlagged Shipments (delay > 3 days):")
    if flagged.empty:
        print("  None")
    else:
        for _, row in flagged.iterrows():
            print(
                f"  {row['shipment_id']} {row['carrier']} {row['status']} "
                f"delay={row['delay_days']} cost=${row['cost_usd']}"
            )


def main() -> None:
    """Run the full report generation pipeline."""
    if not Path(INPUT_FILE).exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)

    required_cols = {"shipment_id", "carrier", "status", "delay_days", "cost_usd"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"ERROR: Missing required columns: {missing}")
        return

    if len(df) == 0:
        print("ERROR: Input file contains no data rows")
        return

    carrier_kpis = compute_carrier_kpis(df)
    route_report = compute_route_report(df, top_n=5)

    carrier_kpis.to_csv(SUMMARY_CSV, index=False)
    route_report.to_csv(ROUTES_CSV, index=False)

    print_console_report(df, carrier_kpis, route_report)
    print(f"\nSaved: {SUMMARY_CSV} | {ROUTES_CSV}")


if __name__ == "__main__":
    main()
