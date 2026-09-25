import pandas as pd
import json

def transform_bronze_to_silver(api_payload):
    """
    Ingests raw JSON API payload (Bronze), flattens nested objects/lists,
    cleans anomalies, standardizes formats, and returns a clean Silver DataFrame.
    """
    print("--- Starting Bronze-to-Silver Transformation ---")
    
    # 1. Normalize root-level dictionaries (like shipping_address)
    df_orders = pd.json_normalize(api_payload['data'])
    
    # 2. Explode the nested 'items' list so each purchased product gets its own row
    df_exploded = df_orders.explode('items').reset_index(drop=True)
    
    # 3. Normalize the individual item dictionaries into a flat table
    df_items_only = pd.json_normalize(df_exploded['items'])
    
    # 4. Concatenate order-level data and item-level data side-by-side
    df_silver = pd.concat(
        [df_exploded.drop(columns='items'), df_items_only], 
        axis=1
    )
    
    print(f"Successfully flattened data. Total rows at item-level: {len(df_silver)}")
    
    # 5. Data Cleaning & Standardization
    # Capitalize text columns for consistency
    cols_to_capitalize = ['status', 'shipping_address.city']
    for col in cols_to_capitalize:
        if col in df_silver.columns:
            df_silver[col] = df_silver[col].str.capitalize()
            
    # Handle missing or null zip codes (assigning 'Unknown')
    if 'shipping_address.zip_code' in df_silver.columns:
        df_silver['shipping_address.zip_code'] = (
            df_silver['shipping_address.zip_code'].fillna('Unknown')
        )
        
    print("--- Transformation & Standardization Complete ---")
    return df_silver


# ==========================================
# EXECUTION & QUALITY AUDIT
# ==========================================

# Assuming 'api_payload' is already loaded in your environment:
df_final_silver_orders = transform_bronze_to_silver(api_payload)

# 6. Data Quality & Auditing: Check Order Frequencies per Customer
print("\n--- Auditing Customer Order Counts ---")
customer_order_count = df_final_silver_orders.groupby('customer_id')['order_id'].nunique()
print(customer_order_count.head())

# 7. Data Quality & Auditing: Filter/Flag Anomalies (e.g., 'invalid_zip')
print("\n--- Auditing Invalid Zip Code Records ---")
if 'shipping_address.zip_code' in df_final_silver_orders.columns:
    invalid_zips = df_final_silver_orders[
        df_final_silver_orders['shipping_address.zip_code'].str.contains('invalid', case=False, na=False)
    ]
    
    print(f"Found {len(invalid_zips)} rows with invalid zip codes.")
    display(invalid_zips[['order_id', 'customer_id', 'shipping_address.zip_code']].head())
