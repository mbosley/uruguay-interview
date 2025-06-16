#!/bin/bash

# Create output directory for text files
mkdir -p data/processed/interviews_txt

# Counter for processed files
count=0

# Convert all .docx files
for file in data/raw/interviews/*.docx; do
    if [ -f "$file" ]; then
        # Get filename without path and extension
        filename=$(basename "$file" .docx)
        
        # Convert to plain text
        echo "Converting: $file"
        pandoc -f docx -t plain "$file" -o "data/processed/interviews_txt/${filename}.txt"
        
        ((count++))
    fi
done

# Convert the .odt file
for file in data/raw/interviews/*.odt; do
    if [ -f "$file" ]; then
        # Get filename without path and extension
        filename=$(basename "$file" .odt)
        
        # Convert to plain text
        echo "Converting: $file"
        pandoc -f odt -t plain "$file" -o "data/processed/interviews_txt/${filename}.txt"
        
        ((count++))
    fi
done

echo "Conversion complete! Processed $count files."
echo "Text files saved to: data/processed/interviews_txt/"