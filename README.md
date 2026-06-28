# AI Audit Anomaly Summarizer

A beginner-friendly GenAI project that combines internal audit logic with the
Claude API: it scans a set of vendor transactions for classic audit red
flags, then asks Claude to write up each one as a short, professional audit
observation — the kind of write-up you'd normally do by hand in a findings
report.

**Why this is a good portfolio piece:** it's not just "call an LLM API." It
shows you can (1) reason like an auditor about what counts as risky, (2)
implement that logic in Python/pandas, and (3) use an LLM to turn structured
findings into the kind of narrative a senior auditor or audit committee
actually reads. That combination — audit judgement + data skills + applied
GenAI — is hard to fake and worth calling out explicitly on your CV/LinkedIn.

## How it works

```
transactions.csv          generate_data.py
       |                  (synthetic data with
       v                   4 planted red flags)
detect_anomalies.py
  - structuring (amount just under approval threshold)
  - weekend processing
  - statistical outlier (z-score by category)
  - duplicate payment (same vendor + amount, close dates)
       |
       v
anomalies_detected.csv
       |
       v
summarize_with_claude.py  --> Claude API writes an audit observation
       |                      per flagged transaction + an executive summary
       v
audit_report.md   (the final deliverable)
```

## 1. Set up your environment

```bash
# (optional but recommended) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## 2. Get a Claude API key

1. Go to https://console.anthropic.com and create an account if you don't
   have one.
2. Create an API key under **API Keys**.
3. Set it as an environment variable so the script can read it:

```bash
# Mac/Linux
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows (Command Prompt)
setx ANTHROPIC_API_KEY "sk-ant-..."
```

Check current pricing/rate limits on the docs before running large batches:
https://docs.claude.com

## 3. Generate the sample data

```bash
python generate_data.py
```

This creates `transactions.csv` — 150 normal vendor payments plus 13
transactions with deliberately planted red flags, so you have something
realistic to detect. (Swap this out for real/anonymised data later — see
"Extending this project" below.)

## 4. Detect anomalies

```bash
python detect_anomalies.py
```

This applies four checks and writes everything with `risk_score > 0` to
`anomalies_detected.csv`, sorted by how many checks each transaction
triggered. Open the CSV and you'll see exactly which rule(s) fired for each
row — this is the audit logic, and it's worth understanding before you let
an LLM write about it.

## 5. Generate the audit narrative with Claude

```bash
python summarize_with_claude.py
```

This reads `anomalies_detected.csv`, sends each flagged transaction (plus
the reason it was flagged) to Claude with a prompt asking for a short,
neutral audit observation, and asks for an executive summary across all of
them. Everything is compiled into `audit_report.md`.

**Testing without spending API credits:** run with `DRY_RUN=true` to fill in
placeholder text instead of calling the API, so you can check the report
structure first:

```bash
DRY_RUN=true python summarize_with_claude.py
```

## 6. Or just run everything at once

```bash
python run_pipeline.py
```

## Sample output

This repo includes `sample_output/` with a dry-run version of the report so
you can see the structure without needing an API key. Once you add your key
and run for real, the `[DRY RUN]` placeholder text is replaced by Claude's
actual audit observations.

## Extending this project (good next steps for a portfolio)

- **Use real data**: anonymised bank statement exports, or the Citi Yoyo Card
  transaction data from your Forage simulation, work well here — just match
  the column names or adjust `detect_anomalies.py`.
- **More audit checks**: round-number bias, transactions just under multiple
  approval tiers, unusual approver/department combinations, vendor changes
  in bank details.
- **Turn it into a dashboard**: wrap this in Streamlit so reviewers can
  upload their own CSV and see flagged transactions + narratives live.
- **Export to Word**: generate a polished `.docx` audit report instead of
  markdown (Claude can help you build this with the docx skill if you ask).
- **Put it on GitHub**: a clean README (this one, adapted), a sample dataset,
  and a `sample_output/audit_report.md` is exactly what a hiring manager
  skims in 30 seconds. Link it from your CV/LinkedIn under a "Projects"
  section, with a one-line summary like: *"Built an AI-assisted audit
  anomaly detection pipeline combining rule-based/statistical flagging
  (Python/pandas) with LLM-generated audit narratives (Claude API)."*

## Files

| File | Purpose |
|---|---|
| `generate_data.py` | Creates the synthetic transaction dataset |
| `detect_anomalies.py` | Rule-based + statistical anomaly detection |
| `summarize_with_claude.py` | Calls Claude to write the audit report |
| `run_pipeline.py` | Runs all three steps in order |
| `requirements.txt` | Python dependencies |
| `sample_output/` | Pre-generated example output (dry run) |
