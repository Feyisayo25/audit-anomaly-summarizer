"""
Runs the full pipeline: generate data -> detect anomalies -> summarize with Claude.

Run: python run_pipeline.py
(Set DRY_RUN=true beforehand to skip real API calls while testing.)
"""

import subprocess
import sys

STEPS = [
    ("Generating synthetic transaction data", "generate_data.py"),
    ("Detecting anomalies", "detect_anomalies.py"),
    ("Summarizing anomalies with Claude", "summarize_with_claude.py"),
]

for label, script in STEPS:
    print(f"\n--- {label} ---")
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print(f"Step failed: {script}")
        sys.exit(1)

print("\nPipeline complete. Open audit_report.md to see the final report.")
