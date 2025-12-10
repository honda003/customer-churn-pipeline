import boto3
import os
import pandas as pd

BUCKET = "churn-project1"
BASE = "/home/ubuntu/churn_project/data"

s3 = boto3.client("s3")

for file in os.listdir(BASE):
    if file.startswith("Telco_part") and file.endswith(".xlsx"):

        local_xlsx = os.path.join(BASE, file)
        csv_file = file.replace(".xlsx", ".csv")
        local_csv = os.path.join(BASE, csv_file)

        # Load Excel
        df = pd.read_excel(local_xlsx)

        # Save as CSV
        df.to_csv(local_csv, index=False)
        print(f"Converted {local_xlsx} → {local_csv}")

        # Upload CSV to S3
        s3_key = f"raw/{csv_file}"
        s3.upload_file(local_csv, BUCKET, s3_key)
        print(f"Uploaded {local_csv} → s3://{BUCKET}/{s3_key}")
