"""
Step 3: Use the Claude API to turn flagged anomalies into a written audit report.

For each row in anomalies_detected.csv, this asks Claude to write a short,
professional audit observation: why it was flagged, the risk it represents,
and a recommended follow-up. It also asks Claude for a one-paragraph
executive summary across all flagged items. Everything is compiled into
audit_report.md.

Setup:
  1. pip install anthropic
  2. Get an API key from https://console.anthropic.com
  3. export ANTHROPIC_API_KEY="sk-ant-..."   (Mac/Linux)
     setx ANTHROPIC_API_KEY "sk-ant-..."     (Windows)

Run: python summarize_with_claude.py

Tip: set DRY_RUN=true to test the pipeline end-to-end without calling the
API or spending any credits, e.g.  DRY_RUN=true python summarize_with_claude.py
"""

import os
from datetime import datetime

import pandas as pd

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
MODEL = "claude-sonnet-4-6"


def build_prompt(row):
    return f"""You are assisting an internal auditor reviewing flagged transactions.

Transaction details:
- ID: {row['transaction_id']}
- Date: {row['date']}
- Vendor: {row['vendor']}
- Category: {row['category']}
- Department: {row['department']}
- Amount: EUR {row['amount']:.2f}
- Approver: {row['approver']}
- Flags triggered: {row['flag_reasons']}

Write a short, professional audit observation (3-4 sentences) covering:
1. Why this transaction was flagged
2. The potential risk it represents
3. A recommended follow-up action for the audit team

Use a neutral, factual tone appropriate for an internal audit report.
Do not assume fraud has occurred - frame it as something requiring
further verification."""


def get_dry_run_text(row):
    return (
        f"[DRY RUN] Flagged for: {row['flag_reasons']}. In a live run, Claude "
        f"would write a 3-4 sentence audit observation here explaining the risk "
        f"and a recommended follow-up step. Set DRY_RUN=false and add your "
        f"ANTHROPIC_API_KEY to generate the real narrative."
    )


def summarize_anomaly(client, row):
    if client is None:
        return get_dry_run_text(row)
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": build_prompt(row)}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def build_executive_summary(client, anomalies_df):
    if client is None:
        return (
            "[DRY RUN] In a live run, Claude would write a 4-6 sentence executive "
            "summary here covering how many anomalies were found, the most common "
            "flag types, and an overall risk assessment for senior audit management."
        )
    table = anomalies_df[["transaction_id", "vendor", "amount", "flag_reasons"]].to_string(
        index=False
    )
    prompt = f"""Below is a table of flagged transactions from an internal audit anomaly review.

{table}

Write a concise executive summary (4-6 sentences) for senior audit management, covering:
- How many transactions were flagged
- The most common types of risk flags
- An overall risk assessment
- A high-level recommendation for next steps

Use a professional, neutral audit-report tone."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def get_client():
    if DRY_RUN:
        print("DRY_RUN=true -> skipping API calls, using placeholder text.")
        return None
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("No ANTHROPIC_API_KEY found in environment -> falling back to DRY RUN.")
        return None
    if Anthropic is None:
        print("`anthropic` package not installed -> falling back to DRY RUN.")
        return None
    return Anthropic(api_key=api_key)


def main():
    anomalies = pd.read_csv("anomalies_detected.csv")
    if anomalies.empty:
        print("No anomalies found - nothing to summarize.")
        return

    client = get_client()

    lines = [
        "# Audit Anomaly Summary Report",
        f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
        "## Executive Summary",
        "",
        build_executive_summary(client, anomalies),
        "",
        "## Flagged Transactions",
        "",
        "| ID | Date | Vendor | Amount | Risk Score | Flags |",
        "|---|---|---|---|---|---|",
    ]
    for _, row in anomalies.iterrows():
        lines.append(
            f"| {row['transaction_id']} | {row['date']} | {row['vendor']} | "
            f"EUR {row['amount']:.2f} | {row['risk_score']} | {row['flag_reasons']} |"
        )

    lines += ["", "## Detailed Observations", ""]
    for _, row in anomalies.iterrows():
        lines.append(f"### {row['transaction_id']} — {row['vendor']} (EUR {row['amount']:.2f})")
        lines.append("")
        lines.append(summarize_anomaly(client, row))
        lines.append("")

    with open("audit_report.md", "w") as f:
        f.write("\n".join(lines))

    print("Report written to audit_report.md")


if __name__ == "__main__":
    main()
