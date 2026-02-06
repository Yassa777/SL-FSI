#!/usr/bin/env python3
"""
Parse manually extracted CBSL data files and create clean CSVs.

Input files from data/manual_extraction/:
1. Official Reserve Assets - Historical Data Series Dec_2025.xlsx
2. Central Government Debt Q3 2025.xlsx  
3. International Investment Position.xls (HTML format)
4. reserve_money.xls (HTML format)

Output files to data/external/:
1. reserve_assets_monthly_cbsl.csv - Monthly reserves with component breakdown
2. central_govt_debt_quarterly.csv - Quarterly debt with short-term breakdown
3. iip_quarterly.csv - International Investment Position
4. money_supply_monthly.csv - M2 and other monetary aggregates
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
import warnings

warnings.filterwarnings('ignore')

# Paths
MANUAL_DIR = Path("data/manual_extraction")
EXTERNAL_DIR = Path("data/external")


def parse_reserve_assets_xlsx():
    """
    Parse Official Reserve Assets - Historical Data Series Dec_2025.xlsx
    Returns monthly reserve data with component breakdown.
    
    Structure discovered:
    - Row 2: Headers with dates
    - Row 4: Official Reserve Assets (Total)
    - Row 5: Foreign Currency Reserves
    - Row 6: IMF Reserve Position
    - Row 7: SDRs
    - Row 8: Gold
    - Row 9: Other Reserve Assets
    """
    print("\n" + "="*60)
    print("PARSING: Official Reserve Assets xlsx")
    print("="*60)
    
    xlsx_path = MANUAL_DIR / "Official Reserve Assets  -  Historical Data Series Dec_2025.xlsx"
    
    if not xlsx_path.exists():
        print(f"  ERROR: File not found: {xlsx_path}")
        return None
    
    try:
        # Read the Excel file
        df = pd.read_excel(xlsx_path, header=None)
        print(f"  Raw shape: {df.shape}")
        
        # Save raw for inspection
        raw_path = EXTERNAL_DIR / "reserve_assets_raw.csv"
        df.to_csv(raw_path, index=False)
        print(f"  Saved raw data to: {raw_path}")
        
        # Extract the data rows we need
        # Row 2 has dates in columns 3 onwards
        # Row 4 has total reserves, row 5-9 have components
        
        date_row = df.iloc[2]
        
        # Build the clean dataframe
        records = []
        
        # Get dates from row 2, starting from column 3
        for col_idx in range(3, len(df.columns)):
            date_val = date_row.iloc[col_idx]
            
            # Skip NaN columns
            if pd.isna(date_val):
                continue
            
            # Parse the date
            try:
                if isinstance(date_val, str):
                    # Handle various date formats like "Jan-21", "Apr-18 (as at 27 Apr)", etc
                    date_str = date_val.split('(')[0].strip()  # Remove notes in parentheses
                    date_str = date_str.replace('\n', ' ').strip()
                    
                    # Try to parse month-year format
                    for fmt in ['%b-%y', '%b-%Y', '%Y-%m-%d']:
                        try:
                            parsed_date = pd.to_datetime(date_str, format=fmt)
                            break
                        except:
                            continue
                    else:
                        # Try pandas default parser
                        parsed_date = pd.to_datetime(date_str)
                else:
                    # Already a datetime
                    parsed_date = pd.to_datetime(date_val)
                
                # Normalize to first of month
                parsed_date = parsed_date.replace(day=1)
                
            except Exception as e:
                print(f"  Warning: Could not parse date '{date_val}': {e}")
                continue
            
            # Get values from the data rows
            total_reserves = df.iloc[4, col_idx]
            fx_reserves = df.iloc[5, col_idx]
            imf_position = df.iloc[6, col_idx]
            sdrs = df.iloc[7, col_idx]
            gold = df.iloc[8, col_idx]
            other = df.iloc[9, col_idx]
            
            # Clean values - remove (a) markers, commas, etc
            def clean_value(val):
                if pd.isna(val):
                    return np.nan
                if isinstance(val, (int, float)):
                    return float(val)
                # String value - clean it
                val_str = str(val).replace(',', '').replace('(a)', '').replace('(b)', '').strip()
                try:
                    return float(val_str)
                except:
                    return np.nan
            
            records.append({
                'date': parsed_date,
                'gross_reserves_usd_m': clean_value(total_reserves),
                'fx_reserves_usd_m': clean_value(fx_reserves),
                'imf_position_usd_m': clean_value(imf_position),
                'sdrs_usd_m': clean_value(sdrs),
                'gold_usd_m': clean_value(gold),
                'other_reserves_usd_m': clean_value(other),
                'source': 'CBSL Official Reserve Assets Historical'
            })
        
        # Create clean dataframe
        clean_df = pd.DataFrame(records)
        clean_df = clean_df.sort_values('date').reset_index(drop=True)
        
        # Remove duplicates (keep last for each month)
        clean_df = clean_df.drop_duplicates(subset=['date'], keep='last')
        
        print(f"\n  Extracted {len(clean_df)} monthly records")
        print(f"  Date range: {clean_df['date'].min()} to {clean_df['date'].max()}")
        
        # Show sample
        print(f"\n  Sample data (first 5 rows):")
        print(clean_df.head().to_string())
        print(f"\n  Sample data (last 5 rows):")
        print(clean_df.tail().to_string())
        
        # Save clean data
        clean_path = EXTERNAL_DIR / "reserve_assets_monthly_cbsl.csv"
        clean_df.to_csv(clean_path, index=False)
        print(f"\n  Saved clean data to: {clean_path}")
        
        return clean_df
        
    except Exception as e:
        print(f"  ERROR parsing xlsx: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_html_xls(filepath, name):
    """
    Parse HTML-formatted .xls files from CBSL Data Library.
    These are actually HTML tables saved with .xls extension.
    """
    print(f"\n" + "="*60)
    print(f"PARSING: {name}")
    print("="*60)
    
    if not filepath.exists():
        print(f"  ERROR: File not found: {filepath}")
        return None
    
    try:
        # Read HTML tables
        tables = pd.read_html(filepath)
        print(f"  Found {len(tables)} tables")
        
        if len(tables) > 0:
            # Usually the main data is in the first table
            df = tables[0]
            print(f"  Main table shape: {df.shape}")
            print(f"\n  Columns: {list(df.columns)[:10]}...")
            print(f"\n  First 5 rows:")
            print(df.head().to_string())
            
            return df
        else:
            print("  No tables found")
            return None
            
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_iip():
    """Parse International Investment Position data."""
    filepath = MANUAL_DIR / "International Investment Position.xls"
    df = parse_html_xls(filepath, "International Investment Position")
    
    if df is not None:
        # Save raw
        raw_path = EXTERNAL_DIR / "iip_quarterly_raw.csv"
        df.to_csv(raw_path, index=False)
        print(f"\n  Saved raw data to: {raw_path}")
        
        # Try to clean and reshape
        try:
            # The structure has: Item Name, Unit, Scale, then quarterly columns
            # Let's identify the data rows
            
            # Find rows with actual data (not headers)
            cleaned = clean_iip_data(df)
            if cleaned is not None:
                clean_path = EXTERNAL_DIR / "iip_quarterly_clean.csv"
                cleaned.to_csv(clean_path, index=False)
                print(f"  Saved cleaned data to: {clean_path}")
                return cleaned
                
        except Exception as e:
            print(f"  Error cleaning data: {e}")
    
    return df


def clean_iip_data(df):
    """
    Clean IIP data and reshape to long format.
    """
    try:
        # The second column should be "Item Name" with the variable names
        # Columns 4+ should be quarterly data
        
        # Check if this looks like the expected format
        if df.shape[1] < 5:
            print("  Not enough columns for IIP format")
            return None
        
        # Get the item names (column 1 typically)
        # Find the column that contains item names
        item_col = None
        for i, col in enumerate(df.columns):
            if 'Item' in str(df.iloc[0, i]) or 'Name' in str(df.iloc[0, i]):
                item_col = i
                break
        
        if item_col is None:
            # Try column 1 (0-indexed)
            item_col = 1
        
        print(f"  Using column {item_col} for item names")
        
        # Extract key series we need
        records = []
        
        for idx, row in df.iterrows():
            item_name = str(row.iloc[item_col]) if pd.notna(row.iloc[item_col]) else ""
            
            # Skip empty rows
            if not item_name or item_name == 'nan':
                continue
                
            # Look for key items
            if any(x in item_name.lower() for x in ['reserve', 'portfolio', 'import']):
                unit = str(row.iloc[2]) if len(row) > 2 else ""
                
                # Extract quarterly values (columns 4+)
                for col_idx in range(4, len(row)):
                    col_name = str(df.columns[col_idx])
                    value = row.iloc[col_idx]
                    
                    # Parse quarter from column name
                    if 'Q' in col_name or '-' in col_name:
                        records.append({
                            'item': item_name,
                            'unit': unit,
                            'quarter': col_name,
                            'value': value
                        })
        
        if records:
            result = pd.DataFrame(records)
            print(f"  Extracted {len(result)} records")
            return result
        else:
            print("  No matching records found")
            return None
            
    except Exception as e:
        print(f"  Error in clean_iip_data: {e}")
        return None


def parse_reserve_money():
    """Parse Money Supply / Reserve Money data."""
    filepath = MANUAL_DIR / "reserve_money.xls"
    df = parse_html_xls(filepath, "Reserve Money / Money Supply")
    
    if df is not None:
        # Save raw
        raw_path = EXTERNAL_DIR / "money_supply_raw.csv"
        df.to_csv(raw_path, index=False)
        print(f"\n  Saved raw data to: {raw_path}")
        
        # Try to clean
        try:
            cleaned = clean_money_supply_data(df)
            if cleaned is not None:
                clean_path = EXTERNAL_DIR / "money_supply_monthly_clean.csv"
                cleaned.to_csv(clean_path, index=False)
                print(f"  Saved cleaned data to: {clean_path}")
                return cleaned
        except Exception as e:
            print(f"  Error cleaning: {e}")
    
    return df


def clean_money_supply_data(df):
    """
    Clean money supply data and extract M2.
    """
    try:
        # Similar structure to IIP
        records = []
        
        for idx, row in df.iterrows():
            item_name = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
            
            if not item_name or item_name == 'nan':
                continue
            
            # Look for M2 and other key items
            if any(x in item_name for x in ['M2', 'Broad Money', 'Reserve Money', 'Net Foreign']):
                unit = str(row.iloc[2]) if len(row) > 2 else ""
                
                # Extract monthly values
                for col_idx in range(4, len(row)):
                    col_name = str(df.columns[col_idx])
                    value = row.iloc[col_idx]
                    
                    records.append({
                        'item': item_name.strip(),
                        'unit': unit,
                        'month': col_name,
                        'value': value
                    })
        
        if records:
            result = pd.DataFrame(records)
            print(f"  Extracted {len(result)} records")
            return result
        
        return None
        
    except Exception as e:
        print(f"  Error: {e}")
        return None


def parse_debt_xlsx():
    """
    Parse Central Government Debt Q3 2025.xlsx
    
    Structure discovered:
    - Row 6: Headers with quarters (2000, 2001, ..., 2014 Q1, etc.)
    - Row 9: Total Debt
    - Row 10: Total Domestic Debt
    - Row 11: Short Term (Domestic)
    - Row 12: Medium and Long Term (Domestic)
    - Row 13: Total Foreign Debt
    - Row 14: Short Term (Foreign)
    
    Units: Rs. million (LKR)
    """
    print("\n" + "="*60)
    print("PARSING: Central Government Debt xlsx")
    print("="*60)
    
    xlsx_path = MANUAL_DIR / "Central Government Debt                              Q3 2025.xlsx"
    
    if not xlsx_path.exists():
        print(f"  ERROR: File not found: {xlsx_path}")
        return None
    
    try:
        df = pd.read_excel(xlsx_path, header=None)
        print(f"  Raw shape: {df.shape}")
        
        # Save raw
        raw_path = EXTERNAL_DIR / "central_govt_debt_raw.csv"
        df.to_csv(raw_path, index=False)
        print(f"  Saved raw data to: {raw_path}")
        
        # Extract the data
        # Row 6 has period labels starting from column 2
        period_row = df.iloc[6]
        
        records = []
        
        for col_idx in range(2, len(df.columns)):
            period_val = period_row.iloc[col_idx]
            
            if pd.isna(period_val):
                continue
            
            period_str = str(period_val).strip()
            
            # Parse the period
            try:
                # Handle formats: "2000", "2014 Q1", "2020 Q4\n(a)", etc
                period_str = period_str.split('\n')[0].strip()  # Remove footnotes
                period_str = period_str.replace('(a)', '').replace('(b)', '').replace('(c)', '').replace('(d)', '').replace('(e)', '').strip()
                
                if 'Q' in period_str:
                    # Quarterly format like "2014 Q1"
                    parts = period_str.split()
                    year = int(parts[0])
                    quarter = int(parts[1].replace('Q', ''))
                    # Map quarter to month (end of quarter)
                    month = quarter * 3
                    parsed_date = pd.Timestamp(year=year, month=month, day=1)
                else:
                    # Annual format - use December
                    year = int(float(period_str))
                    parsed_date = pd.Timestamp(year=year, month=12, day=1)
                    
            except Exception as e:
                print(f"  Warning: Could not parse period '{period_val}': {e}")
                continue
            
            def clean_value(val):
                if pd.isna(val):
                    return np.nan
                if isinstance(val, (int, float)):
                    return float(val)
                val_str = str(val).replace(',', '').replace('n.a.', '').strip()
                try:
                    return float(val_str)
                except:
                    return np.nan
            
            records.append({
                'date': parsed_date,
                'total_debt_lkr_m': clean_value(df.iloc[9, col_idx]),
                'domestic_debt_lkr_m': clean_value(df.iloc[10, col_idx]),
                'domestic_short_term_lkr_m': clean_value(df.iloc[11, col_idx]),
                'domestic_medium_long_lkr_m': clean_value(df.iloc[12, col_idx]),
                'foreign_debt_lkr_m': clean_value(df.iloc[13, col_idx]),
                'foreign_short_term_lkr_m': clean_value(df.iloc[14, col_idx]),
                'source': 'CBSL Central Government Debt SDDS'
            })
        
        clean_df = pd.DataFrame(records)
        clean_df = clean_df.sort_values('date').reset_index(drop=True)
        
        # Calculate total short-term debt
        clean_df['total_short_term_lkr_m'] = (
            clean_df['domestic_short_term_lkr_m'].fillna(0) + 
            clean_df['foreign_short_term_lkr_m'].fillna(0)
        )
        
        print(f"\n  Extracted {len(clean_df)} periods")
        print(f"  Date range: {clean_df['date'].min()} to {clean_df['date'].max()}")
        
        print(f"\n  Sample data (last 10 rows):")
        print(clean_df.tail(10).to_string())
        
        # Save clean data
        clean_path = EXTERNAL_DIR / "central_govt_debt_quarterly.csv"
        clean_df.to_csv(clean_path, index=False)
        print(f"\n  Saved clean data to: {clean_path}")
        
        return clean_df
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main parsing routine."""
    print("\n" + "="*70)
    print("CBSL MANUAL EXTRACTION DATA PARSER")
    print("="*70)
    print(f"Input directory:  {MANUAL_DIR}")
    print(f"Output directory: {EXTERNAL_DIR}")
    
    # Ensure output directory exists
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    
    # List input files
    print(f"\nInput files found:")
    for f in MANUAL_DIR.iterdir():
        if f.name != '.DS_Store':
            print(f"  - {f.name}")
    
    # Parse each file
    results = {}
    
    # 1. Reserve Assets xlsx
    results['reserve_assets'] = parse_reserve_assets_xlsx()
    
    # 2. Debt xlsx
    results['debt'] = parse_debt_xlsx()
    
    # 3. IIP (HTML)
    results['iip'] = parse_iip()
    
    # 4. Money Supply (HTML)
    results['money_supply'] = parse_reserve_money()
    
    # Summary
    print("\n" + "="*70)
    print("PARSING SUMMARY")
    print("="*70)
    for name, df in results.items():
        if df is not None:
            print(f"  ✓ {name}: {df.shape}")
        else:
            print(f"  ✗ {name}: Failed to parse")
    
    print(f"\nOutput files written to: {EXTERNAL_DIR}")
    print("Review the *_raw.csv files and refine parsing as needed.")
    
    return results


if __name__ == "__main__":
    main()
