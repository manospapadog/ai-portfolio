import sqlite3
import pandas as pd

conn = sqlite3.connect("crm.db")

tables = {
    "sales_pipeline": "data/sales_pipeline.csv",
    "accounts": "data/accounts.csv",
    "products": "data/products.csv",
    "sales_teams": "data/sales_teams.csv",
}

for table_name, csv_path in tables.items():
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"Loaded {table_name}: {len(df)} rows")

conn.close()
print("Database built: crm.db")