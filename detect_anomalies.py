"""
Step 2: Detect anomalies in transactions.csv using four audit-style checks.

Each check mirrors a real internal-audit red flag:

  - flag_structuring          amount sits just under a round approval threshold
  - flag_weekend               transaction posted outside normal business days
  - flag_statistical_outlier   amount is a statistical outlier vs. its category
  - flag_duplicate              same vendor + same amount within a short window

A transaction's risk_score is the count of checks it triggers (0-4).
Anything with risk_score > 0 is written to anomalies_detected.csv for the
next step (Claude-generated narratives).

Run: python detect_anomalies.py
Output: anomalies_detected.csv
"""

import numpy as np
import pandas as pd


def load_data(path="transactions.csv"):
    return pd.read_csv(path, parse_dates=["date"])


def flag_threshold_structuring(df, low=9000, high=9999.99):
    return df["amount"].between(low, high)


def flag_weekend(df):
    return df["date"].dt.weekday >= 5


def flag_statistical_outliers(df, z_thresh=2.5):
    flags = pd.Series(False, index=df.index)
    for _, group in df.groupby("category"):
        mean, std = group["amount"].mean(), group["amount"].std(ddof=0)
        if not std or np.isnan(std):
            continue
        z_scores = (group["amount"] - mean) / std
        flags.loc[group.index] = z_scores.abs() > z_thresh
    return flags


def flag_duplicate_payments(df, day_window=3):
    """Flag transactions that share a vendor + amount with another transaction
    posted within `day_window` days."""
    flags = pd.Series(False, index=df.index)
    for _, group in df.groupby(["vendor", "amount"]):
        if len(group) < 2:
            continue
        dates = group["date"]
        for idx_a, date_a in dates.items():
            for idx_b, date_b in dates.items():
                if idx_a != idx_b and abs((date_a - date_b).days) <= day_window:
                    flags.loc[idx_a] = True
    return flags


def main():
    df = load_data()

    df["flag_structuring"] = flag_threshold_structuring(df)
    df["flag_weekend"] = flag_weekend(df)
    df["flag_statistical_outlier"] = flag_statistical_outliers(df)
    df["flag_duplicate"] = flag_duplicate_payments(df)

    flag_cols = [
        "flag_structuring",
        "flag_weekend",
        "flag_statistical_outlier",
        "flag_duplicate",
    ]
    df["risk_score"] = df[flag_cols].sum(axis=1)

    labels = {
        "flag_structuring": "Amount near approval threshold",
        "flag_weekend": "Processed on a weekend",
        "flag_statistical_outlier": "Statistical outlier for category",
        "flag_duplicate": "Possible duplicate payment",
    }
    df["flag_reasons"] = df.apply(
        lambda row: "; ".join(labels[c] for c in flag_cols if row[c]), axis=1
    )

    anomalies = df[df["risk_score"] > 0].sort_values("risk_score", ascending=False)
    anomalies.to_csv("anomalies_detected.csv", index=False)
    print(
        f"Flagged {len(anomalies)} of {len(df)} transactions as anomalies "
        f"-> anomalies_detected.csv"
    )


if __name__ == "__main__":
    main()
