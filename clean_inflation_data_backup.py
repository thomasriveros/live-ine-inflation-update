#!/usr/bin/env python3
"""
Python script to clean, transform, and melt Bolivian inflation data from the INE (Instituto Nacional de Estadística)
into four tidy, long-format CSV files.

Developed by Antigravity.
"""

import os
import re
import pandas as pd

# 1. Define a dictionary mapping Spanish month names and abbreviations to numeric strings
SPANISH_MONTHS = {
    'enero': '01', 'ene': '01',
    'febrero': '02', 'feb': '02',
    'marzo': '03', 'mar': '03',
    'abril': '04', 'abr': '04',
    'mayo': '05', 'may': '05',
    'junio': '06', 'jun': '06',
    'julio': '07', 'jul': '07',
    'agosto': '08', 'ago': '08',
    'septiembre': '09', 'sep': '09', 'setiembre': '09',
    'octubre': '10', 'oct': '10',
    'noviembre': '11', 'nov': '11',
    'diciembre': '12', 'dic': '12'
}

def find_file(base_name):
    """
    Robust file finder that handles duplicate copies (e.g. filename (1).xlsx)
    to ensure smooth execution in different environments.
    """
    if os.path.exists(base_name):
        return base_name
    
    # Try looking for duplicate files with ' (1)' suffix
    name_no_ext, ext = os.path.splitext(base_name)
    alt_name = f"{name_no_ext} (1){ext}"
    if os.path.exists(alt_name):
        return alt_name
    
    raise FileNotFoundError(f"Could not find '{base_name}' or '{alt_name}' in the directory.")

def transform_wide_to_long(df, is_multi_index=True):
    """
    Modular function to handle the wide-to-long transformation (the melt).
    
    Parameters:
    -----------
    df : pd.DataFrame
        The raw DataFrame imported from Excel.
    is_multi_index : bool
        If True, the columns are loaded as a MultiIndex (e.g., File 2 and File 3).
        If False, the columns are a single-index of years and months are rows (File 1).
        
    Returns:
    --------
    pd.DataFrame
        A cleaned, melted, long-format DataFrame with parsed dates.
    """
    if is_multi_index:
        # --- EXPLAINING MULTI-INDEX COLUMN HANDLING & MERGED CELLS ---
        # When pandas.read_excel is invoked with header=[0, 1] (or header=[4, 5] for these specific sheets),
        # pandas automatically resolves Excel's merged header cells by forward-filling (ffill-ing) the top row 
        # (Year) across the subsequent columns. This constructs a perfect pandas MultiIndex.
        # Example of resulting column tuples:
        #   (2018, 'ENERO'), (2018, 'FEBRERO'), ..., (2019, 'ENERO'), etc.
        # This keeps the year aligned with the correct month without requiring manual forward-fill of the header row.
        
        # 1. Clean the rows vertically by removing metadata and footer notes
        # Find the first row starting with 'Fuente' (Source) which marks the end of the data table
        source_indices = df[df.iloc[:, 0].astype(str).str.strip().str.startswith('Fuente')]
        if not source_indices.empty:
            df = df.iloc[:source_indices.index[0]]
            
        # Keep only the rows representing category divisions (where the first column is numeric, e.g. 0 to 12)
        df = df[pd.to_numeric(df.iloc[:, 0], errors='coerce').notna()]
        
        # 2. Melt the wide columns (MultiIndex) into long rows
        # The first two columns represent structural identifiers: 'DIVISIÓN' (numeric code) and 'DESCRIPCIÓN' (category)
        # Any other columns represent the Year-Month multi-index. If we added 'CITY' to the dataframe columns
        # as a tuple, it will be included in the ID variables as well.
        id_vars = [col for col in df.columns if col[0] in ('DIVISIÓN', 'DESCRIPCIÓN', 'CITY')]
        
        df_melted = df.melt(id_vars=id_vars)
        
        # If 'CITY' was one of the id variables, our melted columns will contain it
        if len(id_vars) == 3:
            df_melted.columns = ['division', 'category', 'city', 'year', 'month', 'CPI level']
        else:
            df_melted.columns = ['division', 'category', 'year', 'month', 'CPI level']
            
        # 3. Date parsing and cleaning
        # Year is read as an integer or float, so convert to clean string
        year_str = df_melted['year'].astype(int).astype(str)
        # Clean and map Spanish months to numeric strings (e.g., 'ENERO' -> '01')
        month_num = df_melted['month'].astype(str).str.strip().str.lower().map(SPANISH_MONTHS)
        # Construct YYYY-MM-01 format
        df_melted['date'] = year_str + '-' + month_num + '-01'
        
        # Exclude rows where the CPI level is blank or non-numeric (e.g. future months in 2026)
        df_melted = df_melted[pd.to_numeric(df_melted['CPI level'], errors='coerce').notna()]
        df_melted['CPI level'] = df_melted['CPI level'].astype(float)
        
        return df_melted
        
    else:
        # File 1 has a different structure: Years as columns, Months as rows
        # 1. Keep only rows that represent valid Spanish months in the 'MES' column
        df_clean = df[df['MES'].astype(str).str.strip().str.lower().isin(SPANISH_MONTHS.keys())]
        
        # 2. Melt the wide year columns into a single column
        df_melted = df_clean.melt(id_vars=['MES'], var_name='year', value_name='CPI level')
        
        # 3. Construct datetime objects
        year_str = df_melted['year'].astype(int).astype(str)
        month_num = df_melted['MES'].astype(str).str.strip().str.lower().map(SPANISH_MONTHS)
        df_melted['date'] = year_str + '-' + month_num + '-01'
        
        # Clean up values (filter out NaNs/empties)
        df_melted = df_melted[pd.to_numeric(df_melted['CPI level'], errors='coerce').notna()]
        df_melted['CPI level'] = df_melted['CPI level'].astype(float)
        
        return df_melted

def main():
    # --- Resolve file paths ---
    file1_path = find_file("Nal-2026_04_1_Bolivia_Indicegeneral_Var_Mensual_12_Meses_Acumulado.xlsx")
    file2_path = find_file("Nal-2026_04_2_Bolivia_Indice_Division_Var_Mensual_12_Meses_Acumulado_Base_2016.xlsx")
    file3_path = find_file("Ciu-2026_04_3_Ciudad Capital y Conurbacion_Ind_Div_Var_Men_12_Mes_Acum_Base_2016.xlsx")
    
    print("Found files:")
    print(f"  File 1: {file1_path}")
    print(f"  File 2: {file2_path}")
    print(f"  File 3: {file3_path}")
    print("="*60)
    
    # =========================================================================
    # 1. Processing File 1 -> national_CPI.csv
    # =========================================================================
    print("Processing File 1 (National General Index)...")
    # File 1 has title rows at 0-3, year headers at row 4
    df_f1 = pd.read_excel(file1_path, sheet_name='CUADRO Nº 1.1 ÍNDICE MENSUAL', header=4)
    national_CPI = transform_wide_to_long(df_f1, is_multi_index=False)
    national_CPI = national_CPI[['date', 'CPI level']].sort_values('date').reset_index(drop=True)
    
    # =========================================================================
    # 2. Processing File 2 -> national_CPI_by_category.csv
    # =========================================================================
    print("Processing File 2 (National Index by Division/Category)...")
    # File 2 has merged Year header at row 4, Month header at row 5
    df_f2 = pd.read_excel(file2_path, sheet_name='CUADRO Nº 1.1 BOL INDICE', header=[4, 5])
    national_CPI_by_category = transform_wide_to_long(df_f2, is_multi_index=True)
    national_CPI_by_category = national_CPI_by_category[['date', 'CPI level', 'category']].sort_values(['category', 'date']).reset_index(drop=True)
    
    # =========================================================================
    # 3. Processing File 3 -> city_level_CPI.csv & city_level_CPI_by_category.csv
    # =========================================================================
    print("Processing File 3 (City-Level Index by Division/Category)...")
    city_xl = pd.ExcelFile(file3_path)
    # City sheets are named '<number> - <CITY_NAME>', e.g. '1 - SUCRE'
    city_sheets = [s for s in city_xl.sheet_names if re.match(r'^\d+\s*-\s*', s)]
    
    city_wide_dfs = []
    for sheet in city_sheets:
        city_name = sheet.split(' - ', 1)[1]
        df_sheet = city_xl.parse(sheet, header=[4, 5])
        
        # Slice to remove stacked tables below the first table (Cuadro X.1)
        source_indices = df_sheet[df_sheet.iloc[:, 0].astype(str).str.strip().str.startswith('Fuente')]
        if not source_indices.empty:
            df_sheet = df_sheet.iloc[:source_indices.index[0]]
            
        # Drop rows with non-numeric indices to isolate categories
        df_sheet = df_sheet[pd.to_numeric(df_sheet.iloc[:, 0], errors='coerce').notna()]
        
        # Add the 'CITY' column as a MultiIndex tuple to keep structure consistent
        df_sheet[('CITY', 'CITY')] = city_name
        city_wide_dfs.append(df_sheet)
        
    # Concatenate all city wide dataframes before melting
    city_wide_master = pd.concat(city_wide_dfs, ignore_index=True)
    
    # Melt the wide concatenated dataframe
    city_master = transform_wide_to_long(city_wide_master, is_multi_index=True)
    
    # Separate and clean the two target city dataframes
    # - city_level_CPI: Filter to 'ÍNDICE GENERAL' (division 0)
    city_level_CPI = city_master[city_master['division'] == 0][['date', 'CPI level', 'city']].sort_values(['city', 'date']).reset_index(drop=True)
    
    # - city_level_CPI_by_category: Contains all categories
    city_level_CPI_by_category = city_master[['date', 'CPI level', 'city', 'category']].sort_values(['city', 'category', 'date']).reset_index(drop=True)
    
    # =========================================================================
    # 4. Print Shapes and Heads before exporting
    # =========================================================================
    print("\n" + "="*60)
    print("VERIFYING DATAFRAME SHAPES AND HEADS BEFORE EXPORT")
    print("="*60)
    
    dfs_to_export = [
        ("national_CPI.csv", national_CPI),
        ("national_CPI_by_category.csv", national_CPI_by_category),
        ("city_level_CPI.csv", city_level_CPI),
        ("city_level_CPI_by_category.csv", city_level_CPI_by_category)
    ]
    
    for filename, df in dfs_to_export:
        print(f"\nDataFrame for: {filename}")
        print(f"Shape: {df.shape}")
        print("Head:")
        print(df.head(5))
        print("-" * 40)
        
        # Export to CSV
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Successfully exported {filename}!")
        
    print("\n" + "="*60)
    print("All tasks completed successfully!")
    print("="*60)

if __name__ == "__main__":
    main()
