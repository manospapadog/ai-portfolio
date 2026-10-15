# Data

This project uses the **CRM Sales Opportunities** sample dataset from Maven Analytics
(a fictitious B2B hardware company): https://mavenanalytics.io/data-playground/crm-sales-opportunities

The data files are not included in this repository. To rebuild the database:

1. Download the dataset from the link above and unzip it.
2. Put the CSV files in a folder called `data/` inside `project-1-copilot`:
   `sales_pipeline.csv`, `accounts.csv`, `products.csv`, `sales_teams.csv`
   (the data dictionary is optional).
3. Run `python3 build_db.py` to create `crm.db`.

Known data quirk: the sector value "technolgy" is misspelled in the source data.