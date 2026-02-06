#!/usr/bin/env python3
"""
Parse CBSL Statistical Tables from xlsx files.

Files processed:
- table2.12: External Debt (USD millions) - quarterly
- table4.02: Monetary Aggregates M0, M2, M2b (LKR millions) - monthly
- table2.14.1: Tourism Earnings (USD millions) - monthly
- table2.14.2: Workers' Remittances (USD millions) - monthly
- table2.14.3: CSE Inflows/Outflows (USD millions) - monthly
- table4.11: Reserve Money, Multiplier, Velocity - monthly

Created: January 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

MANUAL_DIR = Path("data/manual_extraction")
EXTERNAL_DIR = Path("data/external")


def parse_external_debt_usd():
    """
    Parse table2.12 - Outstanding External Debt (USD millions)
    
    Structure:
    - Row 1: Title
    - Row 4: Column headers (dates)
    - Row 5+: Debt categories with values
    - Categories in column 3, values in columns 4+
    """
    print("\n" + "="*70)
    print("PARSING: table2.12 - External Debt (USD millions)")
    print("="*70)
    
    path = MANUAL_DIR / "table2.12_20251231_e.xlsx"
    df = pd.read_excel(path, header=None)
    
    print(f"  Raw shape: {df.shape}")
    
    # Get dates from row 1 (columns 4 onwards)
    date_row = df.iloc[1]
    
    # Parse dates - format like "2012 Annual", "2013 1st Quarter", etc
    dates = []
    date_cols = []
    
    for col_idx in range(4, df.shape[1]):
        date_str = str(date_row.iloc[col_idx]).strip()
        if 'nan' in date_str.lower() or not date_str:
            continue
            
        try:
            # Parse different formats
            if 'Annual' in date_str:
                year = int(date_str.split()[0])
                parsed = pd.Timestamp(year=year, month=12, day=31)
            elif '1st Quarter' in date_str or '1st' in date_str:
                year = int(date_str.split()[0])
                parsed = pd.Timestamp(year=year, month=3, day=31)
            elif '2nd Quarter' in date_str or '2nd' in date_str:
                year = int(date_str.split()[0])
                parsed = pd.Timestamp(year=year, month=6, day=30)
            elif '3rd Quarter' in date_str or '3rd' in date_str:
                year = int(date_str.split()[0])
                parsed = pd.Timestamp(year=year, month=9, day=30)
            elif '4th Quarter' in date_str or '4th' in date_str:
                year = int(date_str.split()[0])
                parsed = pd.Timestamp(year=year, month=12, day=31)
            else:
                continue
                
            dates.append(parsed)
            date_cols.append(col_idx)
        except:
            continue
    
    print(f"  Found {len(dates)} date columns")
    print(f"  Date range: {dates[0]} to {dates[-1]}")
    
    # Extract key debt series
    # Find rows by looking for labels in column 3
    series_map = {}
    
    for row_idx in range(4, min(100, df.shape[0])):
        label = str(df.iloc[row_idx, 3]).strip()
        if label and label != 'nan':
            # Extract values for this row
            values = []
            for col_idx in date_cols:
                val = df.iloc[row_idx, col_idx]
                if pd.notna(val):
                    try:
                        values.append(float(val))
                    except:
                        values.append(np.nan)
                else:
                    values.append(np.nan)
            
            # Clean label for column name
            clean_label = label.lower().replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
            series_map[clean_label] = values
    
    # Create DataFrame
    result = pd.DataFrame({'date': dates})
    
    # Add key series
    key_series = [
        ('1_general_government', 'govt_total_usd_m'),
        ('short-term', 'govt_short_term_usd_m'),
        ('long-term', 'govt_long_term_usd_m'),
        ('2_central_bank', 'central_bank_usd_m'),
        ('3_deposit-taking_corporations_except_the_central_bank', 'banks_usd_m'),
        ('4_other_sectors', 'other_sectors_usd_m'),
    ]
    
    for pattern, col_name in key_series:
        for label, values in series_map.items():
            if pattern in label:
                result[col_name] = values
                break
    
    # Calculate total short-term if we have components
    if 'govt_short_term_usd_m' in result.columns:
        result['total_short_term_usd_m'] = result['govt_short_term_usd_m'].fillna(0)
    
    result = result.sort_values('date').reset_index(drop=True)
    
    print(f"\n  Columns: {list(result.columns)}")
    print(f"  Records: {len(result)}")
    print(f"\n  Sample (last 5 rows):")
    print(result.tail().to_string())
    
    # Save
    output_path = EXTERNAL_DIR / "external_debt_usd_quarterly.csv"
    result.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    return result


def parse_monetary_aggregates():
    """
    Parse table4.02 - Monetary Aggregates (LKR millions)
    
    Structure:
    - Column 1: Dates (monthly)
    - Column 2: Reserve Money (M0)
    - Column 3: Broad Money (M2)
    """
    print("\n" + "="*70)
    print("PARSING: table4.02 - Monetary Aggregates (LKR millions)")
    print("="*70)
    
    path = MANUAL_DIR / "table4.02_20251223.xlsx"
    df = pd.read_excel(path, header=None)
    
    print(f"  Raw shape: {df.shape}")
    
    # Data starts at row 5
    # Column 1: date, Column 2: M0, Column 3: M2
    records = []
    
    for row_idx in range(5, df.shape[0]):
        date_val = df.iloc[row_idx, 1]
        m0_val = df.iloc[row_idx, 2]
        m2_val = df.iloc[row_idx, 3]
        
        # Skip if no date
        if pd.isna(date_val):
            continue
            
        try:
            # Parse date
            if isinstance(date_val, datetime):
                parsed_date = pd.Timestamp(date_val)
            else:
                parsed_date = pd.to_datetime(date_val)
            
            records.append({
                'date': parsed_date,
                'reserve_money_m0_lkr_m': float(m0_val) if pd.notna(m0_val) else np.nan,
                'broad_money_m2_lkr_m': float(m2_val) if pd.notna(m2_val) else np.nan,
            })
        except Exception as e:
            continue
    
    result = pd.DataFrame(records)
    result = result.sort_values('date').reset_index(drop=True)
    
    print(f"  Records: {len(result)}")
    print(f"  Date range: {result['date'].min()} to {result['date'].max()}")
    print(f"\n  Sample (last 10 rows):")
    print(result.tail(10).to_string())
    
    # Save
    output_path = EXTERNAL_DIR / "monetary_aggregates_monthly.csv"
    result.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    return result


def parse_tourism_earnings():
    """
    Parse table2.14.1 - Tourism Earnings (USD millions)
    
    Structure: Years in row 4 (cols 2+), Months in col 1 (rows 5+)
    """
    print("\n" + "="*70)
    print("PARSING: table2.14.1 - Tourism Earnings (USD millions)")
    print("="*70)
    
    path = MANUAL_DIR / "table2.14.1_20251119_e.xlsx"
    df = pd.read_excel(path, header=None)
    
    print(f"  Raw shape: {df.shape}")
    
    # Row 4 has years (columns 2+)
    years = []
    year_cols = []
    
    for col_idx in range(2, df.shape[1]):
        year_val = df.iloc[4, col_idx]
        if pd.notna(year_val):
            try:
                years.append(int(year_val))
                year_cols.append(col_idx)
            except:
                continue
    
    print(f"  Years: {years[0]} to {years[-1]}")
    
    # Months in column 1, rows 5-16
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    records = []
    
    for row_idx in range(5, min(18, df.shape[0])):
        month_name = str(df.iloc[row_idx, 1]).strip()
        if month_name not in month_names:
            continue
        month_num = month_names.index(month_name) + 1
        
        for year, col_idx in zip(years, year_cols):
            val = df.iloc[row_idx, col_idx]
            if pd.notna(val):
                try:
                    records.append({
                        'date': pd.Timestamp(year=year, month=month_num, day=1),
                        'tourism_earnings_usd_m': float(val)
                    })
                except:
                    continue
    
    result = pd.DataFrame(records)
    if len(result) > 0:
        result = result.sort_values('date').reset_index(drop=True)
        print(f"  Records: {len(result)}")
        print(f"  Date range: {result['date'].min()} to {result['date'].max()}")
    else:
        print("  No records extracted")
    
    # Save
    output_path = EXTERNAL_DIR / "tourism_earnings_monthly.csv"
    result.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    return result


def parse_remittances():
    """
    Parse table2.14.2 - Workers' Remittances (USD millions)
    
    Structure: Years in row 4 (cols 2+), Months in col 1 (rows 5+)
    """
    print("\n" + "="*70)
    print("PARSING: table2.14.2 - Remittances (USD millions)")
    print("="*70)
    
    path = MANUAL_DIR / "table2.14.2_20251119_e.xlsx"
    df = pd.read_excel(path, header=None)
    
    print(f"  Raw shape: {df.shape}")
    
    # Years in row 4, columns 2+
    years = []
    year_cols = []
    
    for col_idx in range(2, df.shape[1]):
        year_val = df.iloc[4, col_idx]
        if pd.notna(year_val):
            try:
                years.append(int(year_val))
                year_cols.append(col_idx)
            except:
                continue
    
    print(f"  Years: {years[0]} to {years[-1]}")
    
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    records = []
    
    for row_idx in range(5, min(18, df.shape[0])):
        month_name = str(df.iloc[row_idx, 1]).strip()
        if month_name not in month_names:
            continue
        month_num = month_names.index(month_name) + 1
        
        for year, col_idx in zip(years, year_cols):
            val = df.iloc[row_idx, col_idx]
            if pd.notna(val):
                try:
                    records.append({
                        'date': pd.Timestamp(year=year, month=month_num, day=1),
                        'remittances_usd_m': float(val)
                    })
                except:
                    continue
    
    result = pd.DataFrame(records)
    if len(result) > 0:
        result = result.sort_values('date').reset_index(drop=True)
        print(f"  Records: {len(result)}")
        print(f"  Date range: {result['date'].min()} to {result['date'].max()}")
    else:
        print("  No records extracted")
    
    # Save
    output_path = EXTERNAL_DIR / "remittances_monthly.csv"
    result.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    return result


def parse_cse_flows():
    """
    Parse table2.14.3 - CSE Inflows/Outflows (USD millions)
    
    Structure: Date in col 1 (row 6+), Inflows col 3, Outflows col 4, Net col 5
    """
    print("\n" + "="*70)
    print("PARSING: table2.14.3 - CSE Flows (USD millions)")
    print("="*70)
    
    path = MANUAL_DIR / "table2.14.3_20251231_e.xlsx"
    df = pd.read_excel(path, header=None)
    
    print(f"  Raw shape: {df.shape}")
    
    records = []
    
    for row_idx in range(6, df.shape[0]):
        date_val = df.iloc[row_idx, 1]  # Date in column 1
        
        if pd.isna(date_val):
            continue
            
        try:
            if isinstance(date_val, datetime):
                parsed_date = pd.Timestamp(date_val)
            else:
                parsed_date = pd.to_datetime(date_val)
            
            # Get values
            inflows = df.iloc[row_idx, 3]   # Secondary market inflows
            outflows = df.iloc[row_idx, 4]  # Outflows
            net = df.iloc[row_idx, 5]       # Net
            
            records.append({
                'date': parsed_date,
                'cse_inflows_usd_m': float(inflows) if pd.notna(inflows) and str(inflows) != 'n.a.' else np.nan,
                'cse_outflows_usd_m': float(outflows) if pd.notna(outflows) and str(outflows) != 'n.a.' else np.nan,
                'cse_net_usd_m': float(net) if pd.notna(net) and str(net) != 'n.a.' else np.nan,
            })
        except:
            continue
    
    result = pd.DataFrame(records)
    if len(result) > 0:
        result = result.sort_values('date').reset_index(drop=True)
        print(f"  Records: {len(result)}")
        print(f"  Date range: {result['date'].min()} to {result['date'].max()}")
    else:
        print("  No records extracted")
    
    # Save
    output_path = EXTERNAL_DIR / "cse_flows_monthly.csv"
    result.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    return result


def parse_reserve_money_velocity():
    """
    Parse table4.11 - Reserve Money, Multiplier, Velocity
    
    Structure: Col 1 has period ("2003 Jan", "Feb", etc.), Col 5 total, Col 6 M1 multiplier
    """
    print("\n" + "="*70)
    print("PARSING: table4.11 - Reserve Money & Velocity")
    print("="*70)
    
    path = MANUAL_DIR / "table4.11_20251231.xlsx"
    df = pd.read_excel(path, header=None)
    
    print(f"  Raw shape: {df.shape}")
    
    records = []
    current_year = None
    
    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    
    for row_idx in range(5, df.shape[0]):
        period = str(df.iloc[row_idx, 1]).strip()  # Column 1 has period
        
        if pd.isna(period) or period == 'nan' or not period:
            continue
        
        # Parse year and month from period like "2003 Jan" or just "Feb"
        parts = period.split()
        
        if len(parts) >= 2 and parts[0].isdigit():
            # Format: "2003 Jan"
            current_year = int(parts[0])
            month_str = parts[1][:3]
        elif len(parts) == 1:
            # Just month name like "Feb"
            month_str = parts[0][:3]
        else:
            continue
        
        if month_str not in month_map or current_year is None:
            continue
        
        month_num = month_map[month_str]
        
        try:
            reserve_money = df.iloc[row_idx, 5]  # Total in column 5
            multiplier_m1 = df.iloc[row_idx, 6]  # M1 multiplier in column 6
            
            records.append({
                'date': pd.Timestamp(year=current_year, month=month_num, day=1),
                'reserve_money_total_lkr_m': float(reserve_money) if pd.notna(reserve_money) else np.nan,
                'money_multiplier_m1': float(multiplier_m1) if pd.notna(multiplier_m1) else np.nan,
            })
        except:
            continue
    
    result = pd.DataFrame(records)
    if len(result) > 0:
        result = result.sort_values('date').reset_index(drop=True)
        print(f"  Records: {len(result)}")
        print(f"  Date range: {result['date'].min()} to {result['date'].max()}")
    else:
        print("  No records extracted")
    
    # Save
    output_path = EXTERNAL_DIR / "reserve_money_velocity_monthly.csv"
    result.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    return result


def main():
    print("\n" + "="*70)
    print("CBSL STATISTICAL TABLES PARSER")
    print("="*70)
    
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Parse all tables
    results['external_debt'] = parse_external_debt_usd()
    results['monetary'] = parse_monetary_aggregates()
    results['tourism'] = parse_tourism_earnings()
    results['remittances'] = parse_remittances()
    results['cse_flows'] = parse_cse_flows()
    results['reserve_money'] = parse_reserve_money_velocity()
    
    # Summary
    print("\n" + "="*70)
    print("PARSING SUMMARY")
    print("="*70)
    
    for name, df in results.items():
        if df is not None and len(df) > 0:
            print(f"  ✓ {name}: {len(df)} records, {df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}")
        else:
            print(f"  ✗ {name}: No data")
    
    return results


if __name__ == "__main__":
    main()
