# How to Run the MFT-Enhanced Pipeline

## Prerequisites

### 1. Check Environment
```bash
# Ensure you're in the project directory
cd /Users/mitchellbosley/Desktop/projects/uruguay-interview/

# Activate virtual environment
source venv/bin/activate

# Check dependencies
pip install -r requirements.txt
```

### 2. Verify Database Setup
```bash
# Check if database exists
ls -la data/uruguay_interviews.db

# Add MFT tables (if not already done)
python scripts/add_mft_tables.py
```

## Running the Pipeline

### Option 1: Test Single Interview (Recommended First)
```bash
# Test on interview 058
python scripts/test_mft_annotation.py 058

# This will:
# - Process one interview with 6 dimensions
# - Show sample MFT results
# - Save output to test_mft_annotation_058.json
# - Cost: ~$0.009
```

### Option 2: Process All Interviews
```bash
# Run full MFT pipeline on all 36 interviews
python scripts/run_mft_pipeline.py

# This will:
# - Process all interviews in data/processed/interviews_txt/
# - Store results in database
# - Generate summary report
# - Total cost: ~$0.32
# - Time: ~30-45 minutes
```

### Option 3: Process Specific Interviews
```bash
# Create a custom script for specific interviews
python -c "
import asyncio
from pathlib import Path
import sys
sys.path.insert(0, '.')
from scripts.run_mft_pipeline import process_single_interview
from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator

async def run():
    annotator = MultiPassAnnotator()
    # Process specific interviews
    for id in ['058', '069', '080']:
        file = Path(f'data/processed/interviews_txt/{id}.txt')
        result = await process_single_interview(file, annotator)
        print(f'Interview {id}: {result["success"]}')

asyncio.run(run())
"
```

## Viewing Results

### 1. Check Database
```bash
# View MFT data in database
sqlite3 data/uruguay_interviews.db

# Count MFT annotations
sqlite> SELECT COUNT(*) FROM turn_moral_foundations;

# View sample MFT data
sqlite> SELECT 
    t.turn_number, 
    t.text, 
    mf.dominant_foundation,
    mf.care_harm,
    mf.fairness_cheating,
    mf.loyalty_betrayal
FROM turns t
JOIN turn_moral_foundations mf ON t.id = mf.turn_id
WHERE t.interview_id = '058'
LIMIT 5;

# Exit sqlite
sqlite> .quit
```

### 2. Generate HTML Report with MFT
```bash
# Generate HTML for single interview
python scripts/generate_interview_html.py 058

# This creates: interview_058_annotated.html
# Open in browser to see all 6 dimensions visualized
```

### 3. Launch Dashboard
```bash
# Start the Streamlit dashboard
python scripts/run_dashboard.py

# Open browser to http://localhost:8501
# Navigate to "MFT Analytics" tab (if implemented)
```

## Quick Test Commands

### Verify MFT Integration
```bash
# 1. Check if MFT tables exist
python -c "
import sqlite3
conn = sqlite3.connect('data/uruguay_interviews.db')
cursor = conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%moral%'\")
tables = cursor.fetchall()
print(f'MFT tables: {tables}')
"

# 2. Test MFT analyzer
python -c "
from src.pipeline.annotation.moral_foundations_analyzer import MoralFoundationsAnalyzer
analyzer = MoralFoundationsAnalyzer()
result = analyzer.analyze_turn('El gobierno nos abandonó y ahora los niños sufren')
print(f'MFT scores: {result}')
"

# 3. Check annotation format
python -c "
import json
with open('test_mft_annotation_058.json', 'r') as f:
    data = json.load(f)
    print(f\"Moral turns found: {len(data.get('moral_turns', []))}\")
    if data.get('mft_profile'):
        print(f\"Primary foundations: {data['mft_profile']['primary_foundations']}\")
"
```

## Troubleshooting

### If annotation fails:
```bash
# Check API key
echo $OPENAI_API_KEY

# Test with smaller batch size
# Edit scripts/run_mft_pipeline.py
# Change: turns_per_batch=6 → turns_per_batch=3
```

### If database errors:
```bash
# Backup database first
cp data/uruguay_interviews.db data/uruguay_interviews_backup.db

# Re-run table creation
python scripts/add_mft_tables.py

# Verify tables
sqlite3 data/uruguay_interviews.db ".tables" | grep moral
```

### If cost is concern:
```bash
# Use cheaper model (edit in script)
# Change: model_name="gpt-4o-mini" → model_name="gpt-3.5-turbo"
# Note: Quality may be lower
```

## Expected Output

### Console Output
```
🚀 Uruguay Interview MFT Annotation Pipeline
============================================================
Started at: 2024-06-20 10:30:00

📊 Found 36 interviews to process

🔄 Processing interviews...

[1/36] 📄 Processing 058...
   ✓ Completed in 15.2s
   ✓ 47 turns analyzed
   ✓ 23 turns with moral content
   ✓ Cost: $0.0089
   ✓ Stored MFT data in database

[2/36] 📄 Processing 059...
   ...
```

### Database Results
- ~1,800 turns with MFT analysis
- 36 interview-level MFT profiles
- Moral foundation distribution data

### Files Created
- `mft_annotation_summary_YYYYMMDD_HHMMSS.json`
- Individual test files if using test script

## Next Steps

After running MFT annotation:

1. **Analyze Results**
   ```bash
   python scripts/analyze_mft_patterns.py
   ```

2. **Generate Reports**
   ```bash
   python scripts/generate_mft_report.py
   ```

3. **Export for Analysis**
   ```bash
   python scripts/export_mft_data.py
   ```

Remember: The first run will take time and cost ~$0.32 for all interviews. Start with a single interview test to ensure everything works!