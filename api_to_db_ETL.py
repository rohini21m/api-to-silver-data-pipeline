import json
import os
import pandas as pd
import numpy as np
import requests 
from sqlalchemy import create_engine

url2 = "https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol=IBM&apikey=demo"
IBM_raw_data = requests.get(url2)
info = IBM_raw_data.json() 


# 2. Save the raw JSON response properly
file_path = os.path.expanduser("/filepath/Raw_API_file/IBM_raw_data.json")

# 2. Open and save your data
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(info, f, indent=4)

print("File saved successfully to your Desktop folder!")

# 4. Display a random sample or head 
raw_df= pd.read_json(file_path)
print(raw_df.head(20)) 

## we have to flatten the json results into a postgres table or a dataframe 

#1) date column must not be the index it has to be row_index 

# 2. Extract Metadata & Time Series components
meta_data = info.get("Meta Data", {})
time_series = info.get("Weekly Time Series", {}) 
if not time_series:
    raise ValueError("Could not find 'Weekly Time Series' in the JSON file. Check your API response.")

# 3. Transform the nested dictionary into a structured DataFrame
# orient="index" forces the dates ("2026-09-18") to become row indexes
df = pd.DataFrame.from_dict(time_series, orient="index")

# 4. Clean and Reset Layout
df = df.reset_index()  # Move dates from the index into a column
df.columns = ["price_date", "open_price", "high_price", "low_price", "close_price", "volume"]

# Add context metadata from the JSON header
df["symbol"] = meta_data.get("2. Symbol", "IBM")
df = df.rename(columns={"close_price": "closing_price"})

# 5. Type Casting (Convert text strings into SQL-friendly numbers and dates)
df["price_date"] = pd.to_datetime(df["price_date"],errors="coerce")
print("Columns in DataFrame:", df.columns.tolist())
print(df.head(2))
df["open_price"] = pd.to_numeric(df["open_price"])
df["high_price"] = pd.to_numeric(df["high_price"])
df["low_price"] = pd.to_numeric(df["low_price"])
df["closing_price"] = pd.to_numeric(df["closing_price"])
df["volume"] = pd.to_numeric(df["volume"]).astype(int)

print("--- Cleaned Table Preview ---")
print(df.head()) 


#Ingest data into postgres table  
#first have to connect to postgreSQL 
# --- DATABASE CONFIGURATION ---
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "C520")
DB_HOST = os.getenv("DB_HOST", "loacalhost")
DB_PORT = os.getenv("DB_PORT", "5435")
DB_NAME = os.getenv("DB_NAME", "rohinisaichandramunnangi")
TARGET_TABLE = "IBM_stock_weekly_prices"

print(f"\nIngesting data into PostgreSQL table: {TARGET_TABLE}...")
try:
    conn_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(conn_string)
    
    df.to_sql(
        name=TARGET_TABLE,
        con=engine,
        if_exists="append",  # Use 'replace' if you want to overwrite the table completely
        index=False,
        method="multi"       # Batches inserts together for higher speed performance
    )
    print("Ingestion completed successfully!")
except Exception as e:
    print(f"Database ingestion failed: {e}") 

df.info() 
df.describe()  


df.info()

print(df) 
print(df.columns) 
df 
print(type(df)) 
