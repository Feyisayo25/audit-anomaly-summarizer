"""
Step 1: Generate a synthetic vendor-payment transaction dataset.

This simulates ~150 "normal" transactions for a fictitious company, then
deliberately injects four classic audit red flags so the detector in
detect_anomalies.py has something realistic to find:

  1. Structuring        - amounts just under a round approval threshold (e.g. 9,950
                           when approval is required above 10,000)
  2. Duplicate payments  - same vendor + same amount within a few days
  3. Weekend processing  - transactions posted outside normal business days
  4. Statistical outliers- amounts far outside the normal range for their category

Run: python generate_data.py
Output: transactions.csv
"""

import random
from datetime import datetime, timedelta

import pandas as pd

random.seed(42)

VENDORS_TO_CATEGORY = {
    "Staples Office Supply": "Office Supplies",
    "CloudHost Services": "IT & Software",
    "Greenfield Logistics": "Logistics",
    "Apex IT Consulting": "Professional Services",
    "Bright Catering Co": "Catering",
    "Metro Office Cleaning": "Facilities",
    "Falcon Security Systems": "Facilities",
    "Nova Marketing Agency": "Marketing",
    "Summit Legal Services": "Professional Services",
    "Riverbank Equipment Hire": "Equipment",
}
VENDORS = list(VENDORS_TO_CATEGORY.keys())

CATEGORY_AMOUNT_RANGE = {
    "Office Supplies": (50, 800),
    "IT & Software": (200, 4000),
    "Logistics": (300, 6000),
    "Professional Services": (500, 8000),
    "Catering": (100, 1500),
    "Facilities": (150, 3000),
    "Marketing": (300, 7000),
    "Equipment": (200, 5000),
}

DEPARTMENTS = ["Operations", "Finance", "Marketing", "IT", "HR", "Facilities"]
APPROVERS = ["J. Connolly", "A. Murphy", "S. Byrne", "R. Walsh"]


def random_business_datetime(start, end):
    delta = end - start
    dt = start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))
    return dt.replace(hour=random.randint(8, 18), minute=random.randint(0, 59))


def generate_normal_transactions(n, start, end, next_id=1):
    rows = []
    for i in range(n):
        vendor = random.choice(VENDORS)
        category = VENDORS_TO_CATEGORY[vendor]
        amount = round(random.uniform(*CATEGORY_AMOUNT_RANGE[category]), 2)
        dt = random_business_datetime(start, end)
        while dt.weekday() >= 5:  # keep "normal" transactions on weekdays
            dt = random_business_datetime(start, end)
        rows.append(
            {
                "transaction_id": f"TXN{next_id + i:05d}",
                "date": dt.strftime("%Y-%m-%d %H:%M"),
                "vendor": vendor,
                "category": category,
                "department": random.choice(DEPARTMENTS),
                "amount": amount,
                "approver": random.choice(APPROVERS),
            }
        )
    return rows


def inject_anomalies(start, end, next_id):
    rows = []

    # 1. Structuring: amounts just under a 10,000 approval threshold
    for _ in range(4):
        vendor = random.choice(VENDORS)
        dt = random_business_datetime(start, end)
        rows.append(
            {
                "transaction_id": f"TXN{next_id:05d}",
                "date": dt.strftime("%Y-%m-%d %H:%M"),
                "vendor": vendor,
                "category": VENDORS_TO_CATEGORY[vendor],
                "department": random.choice(DEPARTMENTS),
                "amount": round(random.uniform(9500, 9999), 2),
                "approver": random.choice(APPROVERS),
            }
        )
        next_id += 1

    # 2. Duplicate payments: same vendor + same amount within 1-2 days
    for _ in range(3):
        vendor = random.choice(VENDORS)
        amount = round(random.uniform(800, 3000), 2)
        dt1 = random_business_datetime(start, end)
        dt2 = dt1 + timedelta(days=random.choice([1, 2]))
        for dt in (dt1, dt2):
            rows.append(
                {
                    "transaction_id": f"TXN{next_id:05d}",
                    "date": dt.strftime("%Y-%m-%d %H:%M"),
                    "vendor": vendor,
                    "category": VENDORS_TO_CATEGORY[vendor],
                    "department": random.choice(DEPARTMENTS),
                    "amount": amount,
                    "approver": random.choice(APPROVERS),
                }
            )
            next_id += 1

    # 3. Weekend processing
    for _ in range(3):
        vendor = random.choice(VENDORS)
        dt = random_business_datetime(start, end)
        while dt.weekday() < 5:
            dt += timedelta(days=1)
        rows.append(
            {
                "transaction_id": f"TXN{next_id:05d}",
                "date": dt.strftime("%Y-%m-%d %H:%M"),
                "vendor": vendor,
                "category": VENDORS_TO_CATEGORY[vendor],
                "department": random.choice(DEPARTMENTS),
                "amount": round(random.uniform(500, 4000), 2),
                "approver": random.choice(APPROVERS),
            }
        )
        next_id += 1

    # 4. Statistical outliers: amount far outside the normal range for category
    for _ in range(3):
        vendor = random.choice(VENDORS)
        dt = random_business_datetime(start, end)
        rows.append(
            {
                "transaction_id": f"TXN{next_id:05d}",
                "date": dt.strftime("%Y-%m-%d %H:%M"),
                "vendor": vendor,
                "category": VENDORS_TO_CATEGORY[vendor],
                "department": random.choice(DEPARTMENTS),
                "amount": round(random.uniform(15000, 30000), 2),
                "approver": random.choice(APPROVERS),
            }
        )
        next_id += 1

    return rows


def main():
    start = datetime(2026, 1, 1)
    end = datetime(2026, 5, 31)

    normal = generate_normal_transactions(150, start, end, next_id=1)
    anomalies = inject_anomalies(start, end, next_id=len(normal) + 1)

    df = pd.DataFrame(normal + anomalies).sort_values("date").reset_index(drop=True)
    df.to_csv("transactions.csv", index=False)
    print(f"Generated {len(df)} transactions -> transactions.csv")


if __name__ == "__main__":
    main()
