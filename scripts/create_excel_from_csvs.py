#!/usr/bin/env python3
"""
Create Excel file from exported CSV files.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def main():
    csv_dir = Path("data/exports/csv")
    output_dir = Path("data/exports")
    
    # Get all CSV files
    csv_files = sorted(csv_dir.glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files")
    
    # Create Excel file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = output_dir / f"uruguay_interviews_database_{timestamp}.xlsx"
    
    print(f"\nCreating Excel file: {excel_path}")
    
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        for csv_file in csv_files:
            table_name = csv_file.stem
            print(f"Processing table: {table_name}")
            
            # Read CSV
            df = pd.read_csv(csv_file)
            
            # Excel sheet names have a 31 character limit
            sheet_name = table_name[:31]
            
            # Write to Excel
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Add a header format
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BD',
                'border': 1
            })
            
            # Write the column headers with the header format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Auto-adjust column widths
            for i, col in enumerate(df.columns):
                # Find max length in this column
                max_len = max(
                    df[col].astype(str).apply(len).max() if len(df) > 0 else 0,
                    len(col)
                ) + 2
                # Cap at reasonable width
                max_len = min(max_len, 50)
                worksheet.set_column(i, i, max_len)
    
    print(f"\nExcel file created successfully!")
    
    # Print summary
    print(f"\nDatabase Export Summary:")
    print(f"=" * 50)
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        table_name = csv_file.stem
        print(f"{table_name}: {len(df)} rows, {len(df.columns)} columns")

if __name__ == "__main__":
    main()