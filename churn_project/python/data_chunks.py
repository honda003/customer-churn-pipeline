import pandas as pd

BASE = "/home/ubuntu/churn_project"

df = pd.read_excel(f"{BASE}/data/Telco_customer_churn.xlsx")

df1 = df.iloc[:29]
df2 = df.iloc[29:29+570]
df3 = df.iloc[29+570:]

df1.to_excel(f"{BASE}/data/Telco_part1.xlsx", index=False)
df2.to_excel(f"{BASE}/data/Telco_part2.xlsx", index=False)
df3.to_excel(f"{BASE}/data/Telco_part3.xlsx", index=False)

print("Files created successfully!")
