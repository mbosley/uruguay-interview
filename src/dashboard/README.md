# Uruguay Interview Analysis Dashboard

An interactive Streamlit dashboard for exploring and analyzing citizen consultation interview data from Uruguay.

## Features

### 1. Overview Dashboard
- Key metrics: total interviews, average confidence, priorities identified, unique themes
- Sentiment distribution visualization
- Emotional themes analysis  
- Geographic distribution of interviews

### 2. Priorities Analysis
- Filter by scope (National/Local)
- Top priority categories
- Priority ranking distribution
- Detailed priority descriptions by category

### 3. Themes Exploration
- Most frequent themes across all interviews
- Theme distribution heatmap by department
- Theme co-occurrence analysis

### 4. Interview Detail Viewer
- Individual interview exploration
- Full metadata display
- Tabbed views for:
  - National and local priorities
  - Identified themes
  - Emotional analysis
  - Raw interview text (when available)

## Running the Dashboard

### Option 1: Using the launch script
```bash
python scripts/run_dashboard.py
```

### Option 2: Direct Streamlit command
```bash
streamlit run src/dashboard/app.py
```

The dashboard will open in your default web browser at http://localhost:8501

## Navigation

Use the sidebar to:
- Switch between different dashboard views
- Apply filters (date range, department)
- Access different analysis perspectives

## Data Requirements

The dashboard connects to the configured database (SQLite/PostgreSQL) and requires:
- Processed interviews with annotations
- Extracted priorities and themes
- Confidence scores and metadata

## Customization

### Adding New Visualizations

1. Add visualization functions to `visualizations.py`
2. Import and integrate into the main app
3. Add navigation options as needed

### Styling

Custom CSS is included in the app for enhanced styling. Modify the CSS block in `app.py` to customize appearance.

## Performance

- Data is cached for 5 minutes to improve performance
- Database connection is cached as a resource
- Large datasets are paginated automatically

## Troubleshooting

If the dashboard doesn't load:
1. Ensure the database is populated with interview data
2. Check database connection settings in config.yaml
3. Verify all required packages are installed
4. Check for any error messages in the terminal