#!/usr/bin/env python3
import os
import re
from pathlib import Path

def rename_interviews():
    # Path to the text interviews
    interviews_dir = Path("data/processed/interviews_txt")
    
    # Pattern to match the current naming convention
    # Handles both "T - " and "T- " variants
    pattern = re.compile(r'T\s*-\s*(\d{8})\s+(\d{4})\s+(\d+)\.txt')
    
    renamed_count = 0
    
    for file in interviews_dir.glob("*.txt"):
        match = pattern.match(file.name)
        if match:
            date = match.group(1)
            time = match.group(2)
            interview_id = match.group(3)
            
            # Format 1: interview_ID_YYYYMMDD_HHMM.txt
            new_name1 = f"interview_{interview_id.zfill(3)}_{date}_{time}.txt"
            
            # Format 2: YYYYMMDD_HHMM_ID.txt (sortable by date/time)
            new_name2 = f"{date}_{time}_{interview_id.zfill(3)}.txt"
            
            # Format 3: ID_YYYYMMDD_HHMM.txt (sortable by ID)
            new_name3 = f"{interview_id.zfill(3)}_{date}_{time}.txt"
            
            # Using Format 2 as default (sortable by date/time)
            new_name = new_name2
            
            old_path = file
            new_path = interviews_dir / new_name
            
            print(f"Renaming: {file.name} -> {new_name}")
            old_path.rename(new_path)
            renamed_count += 1
    
    print(f"\nRenamed {renamed_count} files")
    print("\nNaming format: YYYYMMDD_HHMM_ID.txt")
    print("This format makes files sortable by date and time of interview")

if __name__ == "__main__":
    rename_interviews()