# End-to-End Pipeline Implementation Plan
## From Interview to Dashboard: Working Prototype

### Overview

This document outlines the implementation plan for a working prototype that demonstrates the complete pipeline from raw interview documents to interactive dashboards. We'll build a minimal but functional version that can process real interviews and generate meaningful insights.

---

## 🎯 Goal

Create a working prototype that can:
1. Process a batch of interview documents (DOCX/TXT)
2. Generate AI-powered annotations with quality validation
3. Extract structured data into PostgreSQL
4. Generate an interactive dashboard showing key insights

**Target:** Process 10 interviews end-to-end as proof of concept

---

## 🏗️ Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Interview     │     │       AI        │     │   Structured    │
│   Documents     ├────▶│   Annotation    ├────▶│   Extraction    │
│  (DOCX/TXT)     │     │    Engine       │     │    (Layer 2)    │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                        ┌─────────────────┐               │
                        │    Dashboard    │               ▼
                        │   Generation    │◀──────┌─────────────────┐
                        │   (Streamlit)   │       │   PostgreSQL    │
                        └─────────────────┘       │    Database     │
                                                  └─────────────────┘
```

---

## 📋 Implementation Steps

### Step 1: Document Ingestion Module
**Timeline:** 2-3 days

#### 1.1 Create Document Processor
```python
# src/pipeline/ingestion/document_processor.py
from pathlib import Path
from typing import Dict, Any
import docx
from dataclasses import dataclass

@dataclass
class InterviewDocument:
    id: str
    date: str
    location: str
    participant_count: int
    text: str
    metadata: Dict[str, Any]

class DocumentProcessor:
    def process_interview(self, file_path: Path) -> InterviewDocument:
        """Extract text and metadata from interview document."""
        if file_path.suffix == '.docx':
            return self._process_docx(file_path)
        elif file_path.suffix == '.txt':
            return self._process_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
    
    def _process_docx(self, file_path: Path) -> InterviewDocument:
        doc = docx.Document(file_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
        metadata = self._extract_metadata(file_path.name, text)
        
        return InterviewDocument(
            id=metadata['id'],
            date=metadata['date'],
            location=metadata['location'],
            participant_count=metadata['participant_count'],
            text=text,
            metadata=metadata
        )
    
    def _extract_metadata(self, filename: str, text: str) -> Dict[str, Any]:
        # Extract metadata from filename and text content
        # Example: "20250528_0900_058.txt"
        parts = filename.replace('.txt', '').replace('.docx', '').split('_')
        
        return {
            'id': parts[2] if len(parts) > 2 else 'unknown',
            'date': f"{parts[0][:4]}-{parts[0][4:6]}-{parts[0][6:8]}",
            'time': f"{parts[1][:2]}:{parts[1][2:]}",
            'location': self._detect_location(text),
            'participant_count': self._count_participants(text)
        }
```

#### 1.2 Test with Sample Interviews
- Process 10 sample interviews
- Validate text extraction
- Ensure metadata accuracy

### Step 2: AI Annotation Engine
**Timeline:** 3-4 days

#### 2.1 Create Annotation Prompt Manager
```python
# src/pipeline/annotation/prompt_manager.py
from pathlib import Path
import xml.etree.ElementTree as ET

class PromptManager:
    def __init__(self, schema_path: Path):
        self.schema = self._load_schema(schema_path)
        self.system_prompt = self._build_system_prompt()
    
    def _load_schema(self, schema_path: Path) -> ET.Element:
        tree = ET.parse(schema_path)
        return tree.getroot()
    
    def _build_system_prompt(self) -> str:
        return """You are an expert qualitative researcher analyzing citizen interviews.
        Follow the provided annotation schema exactly.
        Output valid JSON that matches the schema structure.
        Include confidence scores for all annotations."""
    
    def create_annotation_prompt(self, interview_text: str) -> str:
        return f"""
        Analyze this interview according to the annotation schema.
        
        Interview text:
        {interview_text}
        
        Provide a comprehensive annotation including:
        1. Priority rankings (national and local)
        2. Emotional coding
        3. Key themes and narratives
        4. Uncertainty tracking
        
        Output format: Valid JSON matching the schema.
        """
```

#### 2.2 Implement Annotation Engine
```python
# src/pipeline/annotation/annotator.py
import openai
import json
from typing import Dict, Any

class AnnotationEngine:
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
        self.client = openai.OpenAI()
    
    def annotate_interview(self, interview: InterviewDocument) -> Dict[str, Any]:
        """Generate AI annotation for interview."""
        prompt = self.prompt_manager.create_annotation_prompt(interview.text)
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": self.prompt_manager.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        annotation = json.loads(response.choices[0].message.content)
        annotation['interview_id'] = interview.id
        annotation['processing_metadata'] = {
            'model': 'gpt-4-turbo-preview',
            'timestamp': datetime.now().isoformat(),
            'confidence': self._calculate_confidence(annotation)
        }
        
        return annotation
    
    def _calculate_confidence(self, annotation: Dict[str, Any]) -> float:
        # Calculate overall confidence based on various factors
        return 0.85  # Placeholder
```

#### 2.3 Add Quality Validation
```python
# src/pipeline/quality/validator.py
from typing import Dict, Any, List, Tuple

class AnnotationValidator:
    def validate(self, annotation: Dict[str, Any], source_text: str) -> Tuple[bool, List[str]]:
        """Validate annotation quality and detect issues."""
        errors = []
        
        # Check schema compliance
        if not self._check_schema_compliance(annotation):
            errors.append("Schema compliance failure")
        
        # Check for hallucinations
        hallucinations = self._detect_hallucinations(annotation, source_text)
        if hallucinations:
            errors.extend(hallucinations)
        
        # Check logical consistency
        if not self._check_consistency(annotation):
            errors.append("Logical inconsistency detected")
        
        return len(errors) == 0, errors
    
    def _detect_hallucinations(self, annotation: Dict[str, Any], source_text: str) -> List[str]:
        """Detect content not present in source."""
        hallucinations = []
        
        # Check if priorities mentioned exist in text
        for priority in annotation.get('priorities', []):
            if priority['theme'] not in source_text.lower():
                hallucinations.append(f"Priority theme '{priority['theme']}' not found in text")
        
        return hallucinations
```

### Step 3: Structured Data Extraction
**Timeline:** 2 days

#### 3.1 Create Extraction Pipeline
```python
# src/pipeline/storage/extractor.py
from typing import Dict, Any, List
import pandas as pd

class StructuredDataExtractor:
    def extract_to_dataframes(self, annotations: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
        """Extract structured data from annotations into pandas DataFrames."""
        
        # Extract interviews table
        interviews_data = []
        for ann in annotations:
            interviews_data.append({
                'id': ann['interview_id'],
                'date': ann['metadata']['date'],
                'location': ann['metadata']['location'],
                'participant_count': ann['metadata']['participant_count'],
                'overall_confidence': ann['processing_metadata']['confidence']
            })
        
        # Extract priorities table
        priorities_data = []
        for ann in annotations:
            for priority_type in ['national', 'local']:
                for priority in ann.get(f'{priority_type}_priorities', []):
                    priorities_data.append({
                        'interview_id': ann['interview_id'],
                        'type': priority_type,
                        'rank': priority['rank'],
                        'theme': priority['theme'],
                        'confidence': priority.get('confidence', 0.8)
                    })
        
        # Extract themes table
        themes_data = []
        for ann in annotations:
            for theme in ann.get('themes', []):
                themes_data.append({
                    'interview_id': ann['interview_id'],
                    'theme': theme['name'],
                    'emotional_intensity': theme.get('emotional_intensity', 0.5),
                    'frequency': theme.get('frequency', 1)
                })
        
        return {
            'interviews': pd.DataFrame(interviews_data),
            'priorities': pd.DataFrame(priorities_data),
            'themes': pd.DataFrame(themes_data)
        }
```

### Step 4: Database Setup and Population
**Timeline:** 1-2 days

#### 4.1 Create Database Schema
```sql
-- config/database/schema.sql
CREATE DATABASE uruguay_interviews;

-- Interviews table
CREATE TABLE interviews (
    id VARCHAR(50) PRIMARY KEY,
    date DATE NOT NULL,
    location VARCHAR(100),
    participant_count INTEGER,
    overall_confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Priorities table
CREATE TABLE priorities (
    id SERIAL PRIMARY KEY,
    interview_id VARCHAR(50) REFERENCES interviews(id),
    type VARCHAR(20) NOT NULL CHECK (type IN ('national', 'local')),
    rank INTEGER NOT NULL,
    theme VARCHAR(200) NOT NULL,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Themes table
CREATE TABLE themes (
    id SERIAL PRIMARY KEY,
    interview_id VARCHAR(50) REFERENCES interviews(id),
    theme VARCHAR(200) NOT NULL,
    emotional_intensity FLOAT,
    frequency INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_priorities_interview ON priorities(interview_id);
CREATE INDEX idx_priorities_theme ON priorities(theme);
CREATE INDEX idx_themes_interview ON themes(interview_id);
CREATE INDEX idx_themes_theme ON themes(theme);
```

#### 4.2 Create Database Manager
```python
# src/pipeline/storage/database_manager.py
import pandas as pd
from sqlalchemy import create_engine
from typing import Dict

class DatabaseManager:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
    
    def initialize_schema(self):
        """Create database tables if they don't exist."""
        with open('config/database/schema.sql', 'r') as f:
            schema_sql = f.read()
        
        with self.engine.connect() as conn:
            conn.execute(schema_sql)
    
    def insert_dataframes(self, dataframes: Dict[str, pd.DataFrame]):
        """Insert dataframes into database tables."""
        for table_name, df in dataframes.items():
            df.to_sql(
                table_name,
                self.engine,
                if_exists='append',
                index=False
            )
    
    def get_connection(self):
        """Get database connection for queries."""
        return self.engine.connect()
```

### Step 5: Dashboard Generation
**Timeline:** 2-3 days

#### 5.1 Create Dashboard Application
```python
# src/dashboards/app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

class UruguayDashboard:
    def __init__(self, db_connection_string: str):
        self.engine = create_engine(db_connection_string)
        st.set_page_config(
            page_title="Uruguay Active Listening Dashboard",
            page_icon="🇺🇾",
            layout="wide"
        )
    
    def run(self):
        st.title("🇺🇾 Uruguay Active Listening Dashboard")
        st.markdown("Real-time insights from citizen interviews")
        
        # Sidebar filters
        with st.sidebar:
            st.header("Filters")
            date_range = st.date_input(
                "Date Range",
                value=(pd.Timestamp.now() - pd.Timedelta(days=30), pd.Timestamp.now())
            )
            location_filter = st.multiselect(
                "Locations",
                options=self._get_locations()
            )
        
        # Main dashboard
        self._show_overview_metrics()
        self._show_priority_analysis()
        self._show_theme_trends()
        self._show_geographic_insights()
    
    def _show_overview_metrics(self):
        st.header("📊 Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Total interviews
        total_interviews = pd.read_sql(
            "SELECT COUNT(*) as count FROM interviews",
            self.engine
        )['count'][0]
        
        col1.metric("Total Interviews", total_interviews)
        
        # Average confidence
        avg_confidence = pd.read_sql(
            "SELECT AVG(overall_confidence) as avg FROM interviews",
            self.engine
        )['avg'][0]
        
        col2.metric("Avg Confidence", f"{avg_confidence:.2%}")
        
        # Top national priority
        top_priority = pd.read_sql("""
            SELECT theme, COUNT(*) as count 
            FROM priorities 
            WHERE type = 'national' AND rank = 1
            GROUP BY theme
            ORDER BY count DESC
            LIMIT 1
        """, self.engine)
        
        if not top_priority.empty:
            col3.metric("Top National Priority", top_priority['theme'][0])
        
        # Unique themes
        unique_themes = pd.read_sql(
            "SELECT COUNT(DISTINCT theme) as count FROM themes",
            self.engine
        )['count'][0]
        
        col4.metric("Unique Themes", unique_themes)
    
    def _show_priority_analysis(self):
        st.header("🎯 Priority Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # National priorities
            national_priorities = pd.read_sql("""
                SELECT theme, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM priorities
                WHERE type = 'national'
                GROUP BY theme
                ORDER BY count DESC
                LIMIT 10
            """, self.engine)
            
            fig = px.bar(
                national_priorities,
                x='count',
                y='theme',
                orientation='h',
                title="Top National Priorities",
                color='avg_confidence',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Local priorities
            local_priorities = pd.read_sql("""
                SELECT theme, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM priorities
                WHERE type = 'local'
                GROUP BY theme
                ORDER BY count DESC
                LIMIT 10
            """, self.engine)
            
            fig = px.bar(
                local_priorities,
                x='count',
                y='theme',
                orientation='h',
                title="Top Local Priorities",
                color='avg_confidence',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_theme_trends(self):
        st.header("📈 Theme Trends")
        
        # Emotional intensity by theme
        theme_emotions = pd.read_sql("""
            SELECT theme, 
                   AVG(emotional_intensity) as avg_intensity,
                   COUNT(*) as frequency
            FROM themes
            GROUP BY theme
            HAVING COUNT(*) > 2
            ORDER BY avg_intensity DESC
        """, self.engine)
        
        fig = px.scatter(
            theme_emotions,
            x='frequency',
            y='avg_intensity',
            size='frequency',
            hover_data=['theme'],
            title="Theme Emotional Intensity vs Frequency",
            labels={'avg_intensity': 'Average Emotional Intensity', 'frequency': 'Frequency'}
        )
        
        # Add theme labels for top points
        for idx, row in theme_emotions.head(5).iterrows():
            fig.add_annotation(
                x=row['frequency'],
                y=row['avg_intensity'],
                text=row['theme'][:20] + '...' if len(row['theme']) > 20 else row['theme'],
                showarrow=True,
                arrowhead=2
            )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_geographic_insights(self):
        st.header("🗺️ Geographic Insights")
        
        # Priorities by location
        location_priorities = pd.read_sql("""
            SELECT i.location, p.theme, COUNT(*) as count
            FROM interviews i
            JOIN priorities p ON i.id = p.interview_id
            WHERE p.type = 'national' AND p.rank <= 3
            GROUP BY i.location, p.theme
            ORDER BY i.location, count DESC
        """, self.engine)
        
        if not location_priorities.empty:
            # Pivot for heatmap
            pivot_data = location_priorities.pivot(
                index='theme',
                columns='location',
                values='count'
            ).fillna(0)
            
            fig = px.imshow(
                pivot_data,
                title="Priority Themes by Location",
                labels=dict(x="Location", y="Theme", color="Count"),
                aspect="auto"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _get_locations(self):
        """Get unique locations for filter."""
        locations = pd.read_sql(
            "SELECT DISTINCT location FROM interviews ORDER BY location",
            self.engine
        )
        return locations['location'].tolist()

# Run dashboard
if __name__ == "__main__":
    dashboard = UruguayDashboard("postgresql://user:password@localhost/uruguay_interviews")
    dashboard.run()
```

### Step 6: Integration Pipeline
**Timeline:** 1-2 days

#### 6.1 Create Main Pipeline Script
```python
# scripts/run_pipeline.py
import click
from pathlib import Path
import logging
from tqdm import tqdm

from src.pipeline.ingestion import DocumentProcessor
from src.pipeline.annotation import AnnotationEngine, PromptManager
from src.pipeline.quality import AnnotationValidator
from src.pipeline.storage import StructuredDataExtractor, DatabaseManager
from config.settings import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option('--input-dir', type=click.Path(exists=True), required=True)
@click.option('--batch-size', default=10, help='Number of interviews to process')
@click.option('--skip-validation', is_flag=True, help='Skip quality validation')
def run_pipeline(input_dir: str, batch_size: int, skip_validation: bool):
    """Run end-to-end annotation pipeline."""
    
    # Initialize components
    logger.info("Initializing pipeline components...")
    doc_processor = DocumentProcessor()
    prompt_manager = PromptManager(config.get_prompt_path("annotation_prompt_v1.xml"))
    annotation_engine = AnnotationEngine(prompt_manager)
    validator = AnnotationValidator()
    extractor = StructuredDataExtractor()
    db_manager = DatabaseManager(config.database_url)
    
    # Get interview files
    input_path = Path(input_dir)
    interview_files = list(input_path.glob("*.txt")) + list(input_path.glob("*.docx"))
    interview_files = interview_files[:batch_size]
    
    logger.info(f"Found {len(interview_files)} interviews to process")
    
    # Process interviews
    annotations = []
    for file_path in tqdm(interview_files, desc="Processing interviews"):
        try:
            # 1. Process document
            logger.info(f"Processing {file_path.name}")
            interview = doc_processor.process_interview(file_path)
            
            # 2. Generate annotation
            logger.info(f"Annotating {interview.id}")
            annotation = annotation_engine.annotate_interview(interview)
            
            # 3. Validate quality
            if not skip_validation:
                is_valid, errors = validator.validate(annotation, interview.text)
                if not is_valid:
                    logger.warning(f"Validation failed for {interview.id}: {errors}")
                    annotation['validation_errors'] = errors
            
            annotations.append(annotation)
            
            # Save annotation
            annotation_path = Path(f"data/processed/annotations/{interview.id}_annotation.json")
            annotation_path.parent.mkdir(parents=True, exist_ok=True)
            with open(annotation_path, 'w') as f:
                json.dump(annotation, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue
    
    # 4. Extract structured data
    logger.info("Extracting structured data...")
    dataframes = extractor.extract_to_dataframes(annotations)
    
    # 5. Insert into database
    logger.info("Inserting into database...")
    db_manager.initialize_schema()
    db_manager.insert_dataframes(dataframes)
    
    logger.info(f"Pipeline complete! Processed {len(annotations)} interviews")
    logger.info("Run 'streamlit run src/dashboards/app.py' to view dashboard")

if __name__ == "__main__":
    run_pipeline()
```

### Step 7: Testing and Validation
**Timeline:** 1-2 days

#### 7.1 Create Integration Tests
```python
# tests/integration/test_pipeline.py
import pytest
from pathlib import Path
import tempfile

from src.pipeline.ingestion import DocumentProcessor
from src.pipeline.annotation import AnnotationEngine
from src.pipeline.storage import StructuredDataExtractor

class TestEndToEndPipeline:
    def test_document_processing(self, sample_interview_path):
        processor = DocumentProcessor()
        interview = processor.process_interview(sample_interview_path)
        
        assert interview.id is not None
        assert len(interview.text) > 100
        assert interview.metadata['date'] is not None
    
    def test_annotation_generation(self, sample_interview):
        engine = AnnotationEngine()
        annotation = engine.annotate_interview(sample_interview)
        
        assert 'priorities' in annotation
        assert 'themes' in annotation
        assert annotation['processing_metadata']['confidence'] > 0.5
    
    def test_data_extraction(self, sample_annotations):
        extractor = StructuredDataExtractor()
        dataframes = extractor.extract_to_dataframes(sample_annotations)
        
        assert 'interviews' in dataframes
        assert 'priorities' in dataframes
        assert len(dataframes['priorities']) > 0
    
    def test_full_pipeline(self, sample_interview_dir):
        # Run full pipeline on test data
        result = run_pipeline(
            input_dir=sample_interview_dir,
            batch_size=3,
            skip_validation=False
        )
        
        assert result['processed_count'] == 3
        assert result['errors'] == 0
```

---

## 🚀 Implementation Schedule

### Week 1: Core Components
- **Day 1-2**: Document ingestion module
- **Day 3-5**: AI annotation engine with basic prompt

### Week 2: Data Pipeline
- **Day 6-7**: Quality validation system
- **Day 8-9**: Structured data extraction
- **Day 10**: Database setup and population

### Week 3: Dashboard & Testing
- **Day 11-12**: Dashboard development
- **Day 13**: Integration pipeline
- **Day 14-15**: Testing and refinement

---

## 🎯 Success Criteria

1. **Document Processing**: Successfully extract text from 10 interviews
2. **Annotation Quality**: Achieve >80% validation pass rate
3. **Data Extraction**: All key fields populated in database
4. **Dashboard Functionality**: Display all core visualizations
5. **End-to-End Performance**: Process 10 interviews in <30 minutes

---

## 🛠️ Required Setup

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your OpenAI API key and database credentials

# Initialize database
createdb uruguay_interviews
python scripts/init_database.py
```

### Running the Pipeline
```bash
# Process interviews
python scripts/run_pipeline.py --input-dir data/processed/interviews_txt --batch-size 10

# Start dashboard
streamlit run src/dashboards/app.py
```

---

## 📊 Expected Outputs

### 1. Annotation Files
- JSON files in `data/processed/annotations/`
- Contains full annotation with confidence scores

### 2. Database Tables
- `interviews`: Basic interview metadata
- `priorities`: National and local priorities
- `themes`: Extracted themes with emotional coding

### 3. Dashboard Views
- Overview metrics (total interviews, confidence, top priorities)
- Priority analysis (bar charts by type)
- Theme trends (emotional intensity scatter plot)
- Geographic insights (heatmap of priorities by location)

---

## 🔄 Next Steps

Once the basic pipeline is working:

1. **Enhance Annotation Quality**
   - Fine-tune prompts based on results
   - Add more sophisticated validation
   - Implement human-in-the-loop review

2. **Expand Database Schema**
   - Add more tables for richer analysis
   - Implement time-series tracking
   - Add participant demographics

3. **Advanced Dashboard Features**
   - Real-time updates
   - Drill-down capabilities
   - Export functionality
   - Multiple dashboard views

4. **Scale Testing**
   - Process 100+ interviews
   - Optimize for performance
   - Add batch processing features

This implementation plan provides a clear path to a working prototype that demonstrates the full value chain of the Uruguay Active Listening system.