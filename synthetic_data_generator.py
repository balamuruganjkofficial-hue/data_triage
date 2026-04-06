import pandas as pd
import numpy as np
import random

# Set random seeds so the output is consistent
np.random.seed(42)
random.seed(42)

num_rows = 500

# 1. Generate Base Data (Normal, clean transactions)
names = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Heidi', 'Ivan', 'Judy']
data = {
    'Transaction_ID': list(range(1, num_rows + 1)),
    'Customer_Name': [random.choice(names) for _ in range(num_rows)],
    'Age': np.random.randint(18, 70, size=num_rows).astype(float),
    'Purchase_Amount': np.round(np.random.uniform(10.0, 300.0, size=num_rows), 2),
    'Class': [0] * num_rows  # <--- NEW: The Answer Key. Everything starts as Normal (0)
}

df = pd.DataFrame(data)

# 2. INJECT POISON: Messy Text (Extra spaces, weird capitalization)
for idx in random.sample(range(num_rows), 50): 
    messy_names = [
        f"  {df.loc[idx, 'Customer_Name'].upper()}  ", 
        f"{df.loc[idx, 'Customer_Name'].lower()}   ", 
        f"   {df.loc[idx, 'Customer_Name']}"
    ]
    df.loc[idx, 'Customer_Name'] = random.choice(messy_names)

# 3. INJECT POISON: Missing Data (Nulls)
for idx in random.sample(range(num_rows), 25): 
    df.loc[idx, 'Age'] = np.nan

# 4. INJECT POISON: Data Type Mismatches (Text in a number column)
df['Purchase_Amount'] = df['Purchase_Amount'].astype(object) 
for idx in random.sample(range(num_rows), 15): 
    df.loc[idx, 'Purchase_Amount'] = random.choice(['Error', 'N/A', 'Pending', 'Failed'])

# 5. INJECT POISON: AI Anomalies (Massive outliers) -> THESE BECOME CLASS 1
valid_indices = df[pd.to_numeric(df['Purchase_Amount'], errors='coerce').notnull()].index.tolist()
outlier_indices = random.sample(valid_indices, 15) 
for idx in outlier_indices:
    df.loc[idx, 'Purchase_Amount'] = np.round(random.uniform(50000.0, 99999.0), 2)
    df.loc[idx, 'Class'] = 1  # <--- NEW: We tell the answer key this is actual fraud

# 6. INJECT POISON: Exact Duplicates
duplicates = df.sample(10) 
df = pd.concat([df, duplicates], ignore_index=True)

# Shuffle the deck so the errors are scattered everywhere
df = df.sample(frac=1).reset_index(drop=True)

# Save the final labeled dataset
filename = "labeled_poisoned_data.csv"
df.to_csv(filename, index=False)
print(f"☢️ Labeled Poisoned Dataset created: {filename}")
print(f"Total Rows: {len(df)}")
print("Check your final output files! Your anomalies folder should be full of Class 1s!")