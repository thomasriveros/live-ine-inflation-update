#!/usr/bin/env python3
"""
Python script to calculate a custom "Core-5" CPI index using 5 specific categories.
Reads cleaned, long-format CSVs, filters for these categories, applies normalized weights,
and exports national and city-level CPI datasets.

Developed by Antigravity.
"""

import os
import pandas as pd

# The 5 Core Spanish Categories and their normalized weights as decimals
CORE_5_WEIGHTS = {
    "alimentos y bebidas no alcohólicas": 0.5508,
    "prendas de vestir y calzado": 0.1539,
    "bienes y servicios diversos": 0.1537,
    "muebles, bienes y servicios domésticos": 0.1238,
    "bebidas alcohólicas y tabaco": 0.0179
}

def calculate_core_5_national(input_path, output_path):
    """
    Calculate the Core-5 CPI index for national level data.
    """
    print(f"Reading national category data from {input_path} ...")
    df = pd.read_csv(input_path)
    
    # 1. Clean the category names for robust matching
    df["category_clean"] = df["category"].astype(str).str.strip().str.lower()
    
    # 2. Filter for only the target categories
    target_keys = list(CORE_5_WEIGHTS.keys())
    df_filtered = df[df["category_clean"].isin(target_keys)].copy()
    
    # 3. Map categories to their normalized weights
    df_filtered["weight"] = df_filtered["category_clean"].map(CORE_5_WEIGHTS)
    
    # 4. Multiply CPI level by its weight
    df_filtered["weighted_value"] = df_filtered["CPI level"] * df_filtered["weight"]
    
    # Validation: ensure every date has exactly the 5 target categories
    counts = df_filtered.groupby("date")["category_clean"].count()
    incomplete_dates = counts[counts != len(target_keys)]
    if not incomplete_dates.empty:
        print(f"Warning: Found {len(incomplete_dates)} dates with missing/duplicate categories: {incomplete_dates.index.tolist()}")
    
    # 5. Group by date and sum the weighted values
    national_core_5 = df_filtered.groupby("date")["weighted_value"].sum().reset_index()
    national_core_5.rename(columns={"weighted_value": "Core-5 CPI"}, inplace=True)
    
    # Sort chronologically
    national_core_5 = national_core_5.sort_values("date").reset_index(drop=True)
    
    # Export to CSV
    national_core_5.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Successfully calculated and exported national Core-5 CPI to {output_path} (Shape: {national_core_5.shape})")
    return national_core_5

def calculate_core_5_city(input_path, output_path):
    """
    Calculate the Core-5 CPI index per city.
    """
    print(f"Reading city category data from {input_path} ...")
    df = pd.read_csv(input_path)
    
    # 1. Clean the category names for robust matching
    df["category_clean"] = df["category"].astype(str).str.strip().str.lower()
    
    # 2. Filter for only the target categories
    target_keys = list(CORE_5_WEIGHTS.keys())
    df_filtered = df[df["category_clean"].isin(target_keys)].copy()
    
    # 3. Map categories to their normalized weights
    df_filtered["weight"] = df_filtered["category_clean"].map(CORE_5_WEIGHTS)
    
    # 4. Multiply CPI level by its weight
    df_filtered["weighted_value"] = df_filtered["CPI level"] * df_filtered["weight"]
    
    # Validation: ensure every city & date group has exactly the 5 target categories
    counts = df_filtered.groupby(["city", "date"])["category_clean"].count()
    incomplete_groups = counts[counts != len(target_keys)]
    if not incomplete_groups.empty:
        print(f"Warning: Found {len(incomplete_groups)} city-date combinations with missing/duplicate categories: {incomplete_groups.index.tolist()}")
        
    # 5. Group by date and city and sum the weighted values
    city_core_5 = df_filtered.groupby(["date", "city"])["weighted_value"].sum().reset_index()
    city_core_5.rename(columns={"weighted_value": "Core-5 CPI"}, inplace=True)
    
    # Sort chronologically by date and alphabetically by city
    city_core_5 = city_core_5.sort_values(["city", "date"]).reset_index(drop=True)
    
    # Reorder columns as requested: date, city, Core-5 CPI
    city_core_5 = city_core_5[["date", "city", "Core-5 CPI"]]
    
    # Export to CSV
    city_core_5.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Successfully calculated and exported city-level Core-5 CPI to {output_path} (Shape: {city_core_5.shape})")
    return city_core_5

def main():
    national_input = "data/national_CPI_by_category.csv"
    city_input = "data/city_level_CPI_by_category.csv"
    
    national_output = "data/national_core_5_CPI.csv"
    city_output = "data/city_level_core_5_CPI.csv"
    
    print("="*60)
    print("STARTING CUSTOM CORE-5 CPI CALCULATION")
    print("="*60)
    
    # Perform calculations
    nat_df = calculate_core_5_national(national_input, national_output)
    city_df = calculate_core_5_city(city_input, city_output)
    
    print("\n" + "="*60)
    print("VALIDATING CORE-5 CPI DATASETS")
    print("="*60)
    
    # Validation displays
    print("\nNational Core-5 CPI Sample:")
    print(nat_df.head(5))
    print("\nCity-Level Core-5 CPI Sample:")
    print(city_df.head(5))
    print("\n" + "="*60)
    print("Custom Core-5 CPI calculation complete!")
    print("="*60)

if __name__ == "__main__":
    main()
