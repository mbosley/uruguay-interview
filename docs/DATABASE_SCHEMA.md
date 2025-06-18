# Database Schema Documentation

*Comprehensive documentation of the Uruguay Interview Analysis database schema.*

---

## 2025-06-17 00:55 - Database Schema Documentation

### Overview
This document provides a comprehensive specification of the database schema used for storing and analyzing citizen consultation interviews from Uruguay. The schema is designed to support qualitative research analysis, conversation turn tracking, and multi-level priority analysis.

### Database Technology
- **Database Engine**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy with declarative base
- **Total Tables**: 15 core tables + indexes
- **Key Features**: Multi-turn conversation storage, priority tracking, thematic analysis

---

## Core Tables

### 1. interviews
**Purpose**: Core interview metadata and content storage

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | VARCHAR(50) | NOT NULL, UNIQUE | Human-readable interview identifier (e.g., "058") |
| date | VARCHAR(10) | NOT NULL | Interview date (YYYY-MM-DD format) |
| time | VARCHAR(5) | NOT NULL | Interview time (HH:MM format) |
| location | VARCHAR(100) | NOT NULL | Interview location/venue |
| department | VARCHAR(100) |  | Uruguayan department (state/province) |
| participant_count | INTEGER | DEFAULT 1 | Number of interview participants |
| file_path | VARCHAR(500) |  | Original source file path |
| file_type | VARCHAR(10) |  | Source file extension (.docx, .odt, etc.) |
| word_count | INTEGER |  | Total word count of interview |
| raw_text | TEXT |  | Full interview transcript |
| status | VARCHAR(20) | DEFAULT 'pending' | Processing status (pending, processing, completed, error) |
| processed_at | DATETIME |  | Timestamp when processing completed |
| error_message | TEXT |  | Error details if processing failed |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Indexes**: `date`, `location`, `status`

---

### 2. turns
**Purpose**: Individual conversation turns within interviews

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | INTEGER | NOT NULL, FK(interviews.id) | Parent interview reference |
| annotation_id | INTEGER | FK(annotations.id) | Associated annotation reference |
| turn_number | INTEGER | NOT NULL | Sequential order in conversation |
| speaker | VARCHAR(50) | NOT NULL | Speaker identifier (participant, interviewer, etc.) |
| speaker_id | VARCHAR(50) |  | Specific speaker ID if multiple participants |
| text | TEXT | NOT NULL | Actual spoken text content |
| word_count | INTEGER |  | Word count for this turn |
| duration_seconds | FLOAT |  | Turn duration if timing data available |
| start_time | VARCHAR(10) |  | Time offset from interview start |
| end_time | VARCHAR(10) |  | Turn end time offset |

**Relationships**: 
- `interview` → Interview (backref: `turns`)
- `annotation` → Annotation (backref: `turns`)

**Indexes**: `interview_id`, `(interview_id, turn_number)`, `speaker`

---

### 3. priorities
**Purpose**: Citizen priorities extracted from interviews

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | INTEGER | NOT NULL, FK(interviews.id) | Parent interview reference |
| scope | VARCHAR(20) | NOT NULL | Priority scope ('national' or 'local') |
| rank | INTEGER | NOT NULL | Priority ranking (1 = highest) |
| category | VARCHAR(50) | NOT NULL | Priority category (education, healthcare, etc.) |
| subcategory | VARCHAR(50) |  | More specific category classification |
| description | TEXT | NOT NULL | Detailed priority description |
| sentiment | VARCHAR(20) |  | Associated sentiment (positive, negative, neutral) |
| evidence_type | VARCHAR(50) |  | Type of evidence provided |
| confidence | FLOAT | DEFAULT 1.0 | Confidence score (0.0-1.0) |

**Relationships**: 
- `interview` → Interview (backref: `priorities`)

**Indexes**: `(scope, rank)`, `category`, `sentiment`

---

### 4. themes
**Purpose**: Thematic content analysis from interviews

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | INTEGER | NOT NULL, FK(interviews.id) | Parent interview reference |
| theme | VARCHAR(100) | NOT NULL | Theme or topic name |
| category | VARCHAR(50) |  | Theme category classification |
| frequency | INTEGER | DEFAULT 1 | Frequency of theme occurrence |

**Relationships**: 
- `interview` → Interview (backref: `themes`)

**Indexes**: `theme`, `category`

---

### 5. annotations
**Purpose**: AI-generated annotations and analysis metadata

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | INTEGER | NOT NULL, FK(interviews.id) | Parent interview reference |
| model_provider | VARCHAR(50) | NOT NULL | AI model provider (e.g., "gemini") |
| model_name | VARCHAR(100) | NOT NULL | Specific model used |
| temperature | FLOAT |  | Model temperature parameter |
| xml_content | TEXT |  | Full XML annotation content |
| dominant_emotion | VARCHAR(50) |  | Primary emotional tone |
| overall_sentiment | VARCHAR(20) |  | Overall sentiment classification |
| confidence_score | FLOAT |  | Overall confidence in annotation |
| annotation_completeness | FLOAT |  | Completeness metric (0.0-1.0) |
| has_validation_errors | BOOLEAN | DEFAULT FALSE | Whether validation errors exist |
| validation_notes | JSON |  | Validation error details |
| processing_time | FLOAT |  | Processing time in seconds |
| token_count | INTEGER |  | Tokens used in processing |
| cost_estimate | FLOAT |  | Estimated processing cost |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

**Relationships**: 
- `interview` → Interview (backref: `annotations`)

**Unique Constraints**: `(interview_id, model_provider, model_name)`
**Indexes**: `overall_sentiment`, `confidence_score`

---

## Conversation Analysis Tables

### 6. turn_functional_annotations
**Purpose**: Functional analysis of conversation turns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| turn_id | INTEGER | NOT NULL, FK(turns.id) | Parent turn reference |
| primary_function | VARCHAR(50) | NOT NULL | Primary turn function |
| secondary_functions | JSON |  | Additional functions (array) |
| coding_confidence | FLOAT | DEFAULT 1.0 | Confidence in coding |
| ambiguous_function | BOOLEAN | DEFAULT FALSE | Whether function is ambiguous |
| uncertainty_notes | TEXT |  | Notes on coding uncertainty |

**Function Types**: greeting, problem_identification, solution_proposal, agreement, disagreement, question, clarification, narrative, evaluation, closing

**Relationships**: 
- `turn` → Turn (backref: `functional_annotations`)

**Indexes**: `primary_function`

---

### 7. turn_content_annotations
**Purpose**: Content analysis of conversation turns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| turn_id | INTEGER | NOT NULL, FK(turns.id) | Parent turn reference |
| topics | JSON | NOT NULL | List of topics discussed |
| topic_narrative | TEXT |  | Explanation of topic coding |
| geographic_scope | JSON |  | Geographic scope levels |
| geographic_mentions | JSON |  | Specific places mentioned |
| temporal_reference | VARCHAR(20) |  | Time reference (past, present, future, timeless) |
| temporal_specifics | JSON |  | Specific time references |
| actors_mentioned | JSON |  | Government, citizens, organizations mentioned |
| actor_relationships | JSON |  | How actors relate to each other |
| indicates_priority | BOOLEAN | DEFAULT FALSE | Whether turn indicates a priority |
| priority_rank_mentioned | INTEGER |  | Priority rank if mentioned |

**Relationships**: 
- `turn` → Turn (backref: `content_annotations`)

---

### 8. turn_evidence
**Purpose**: Evidence and argumentation tracking

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| turn_id | INTEGER | NOT NULL, FK(turns.id) | Parent turn reference |
| evidence_type | VARCHAR(50) | NOT NULL | Type of evidence provided |
| evidence_narrative | TEXT |  | Description of evidence |
| specificity | VARCHAR(20) |  | Evidence specificity level |
| verifiability | VARCHAR(20) |  | Whether evidence can be verified |
| argument_type | VARCHAR(50) |  | Type of argumentation |
| logical_connectors | JSON |  | Logical connection words used |

**Evidence Types**: personal_experience, community_observation, statistics, expert_opinion, media_report, government_data, hearsay, none

**Specificity Levels**: very_specific, somewhat_specific, vague, none
**Verifiability**: verifiable, possibly_verifiable, unverifiable

**Relationships**: 
- `turn` → Turn (backref: `evidence_annotations`)

**Indexes**: `evidence_type`

---

### 9. turn_stance
**Purpose**: Emotional and evaluative stance analysis

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| turn_id | INTEGER | NOT NULL, FK(turns.id) | Parent turn reference |
| emotional_valence | VARCHAR(20) |  | Emotional direction |
| emotional_intensity | FLOAT |  | Emotional intensity (0.0-1.0) |
| emotional_categories | JSON |  | Specific emotions (anger, fear, joy, etc.) |
| stance_target | VARCHAR(100) |  | What stance is directed toward |
| stance_polarity | VARCHAR(20) |  | Stance direction |
| certainty_level | VARCHAR(20) |  | Level of certainty expressed |
| hedging_markers | JSON |  | Words indicating uncertainty |
| emotional_narrative | TEXT |  | Summary of emotional content |

**Valence**: positive, negative, neutral, mixed
**Polarity**: supportive, critical, ambivalent, neutral
**Certainty**: certain, probable, possible, uncertain

**Relationships**: 
- `turn` → Turn (backref: `stance_annotations`)

---

### 10. conversation_dynamics
**Purpose**: Overall conversation pattern analysis

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | INTEGER | NOT NULL, FK(interviews.id) | Parent interview reference |
| annotation_id | INTEGER | FK(annotations.id) | Associated annotation |
| total_turns | INTEGER |  | Total conversation turns |
| interviewer_turns | INTEGER |  | Turns by interviewer |
| participant_turns | INTEGER |  | Turns by participants |
| average_turn_length | FLOAT |  | Average words per turn |
| question_count | INTEGER |  | Total questions asked |
| response_rate | FLOAT |  | Percentage of questions answered |
| topic_shifts | INTEGER |  | Number of topic changes |
| speaker_balance | FLOAT |  | Speaking time balance (0.0-1.0) |
| longest_turn_speaker | VARCHAR(50) |  | Speaker with longest turn |
| longest_turn_words | INTEGER |  | Length of longest turn |
| conversation_flow | VARCHAR(20) |  | Flow quality (smooth, choppy, mixed) |
| interruption_count | INTEGER |  | Number of interruptions |
| silence_count | INTEGER |  | Number of silences/pauses |
| topic_introduction_pattern | VARCHAR(50) |  | How topics are introduced |
| topic_depth | VARCHAR(20) |  | Depth of topic exploration |

**Relationships**: 
- `interview` → Interview
- `annotation` → Annotation

---

## Additional Analysis Tables

### 11. emotions
**Purpose**: Emotional expressions in interviews

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | INTEGER | NOT NULL, FK(interviews.id) | Parent interview reference |
| type | VARCHAR(50) | NOT NULL | Emotion type |
| intensity | VARCHAR(20) | NOT NULL | Intensity level (low, medium, high) |
| target | VARCHAR(100) |  | Target of emotion |
| context | TEXT |  | Contextual description |
| turn_number | INTEGER |  | Associated turn number |

**Relationships**: 
- `interview` → Interview (backref: `emotions`)

**Indexes**: `type`, `intensity`

---

### 12. concerns
**Purpose**: Specific concerns raised by citizens

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | INTEGER | NOT NULL, FK(interviews.id) | Parent interview reference |
| description | TEXT | NOT NULL | Concern description |
| category | VARCHAR(50) |  | Concern category |
| severity | VARCHAR(20) |  | Severity level (low, medium, high, critical) |
| geographic_scope | VARCHAR(50) |  | Geographic scope |
| specific_location | VARCHAR(100) |  | Specific location if applicable |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

**Indexes**: `category`, `severity`

---

### 13. suggestions
**Purpose**: Policy suggestions from citizens

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | INTEGER | NOT NULL, FK(interviews.id) | Parent interview reference |
| description | TEXT | NOT NULL | Suggestion description |
| target | VARCHAR(100) |  | Target government level/entity |
| category | VARCHAR(50) |  | Suggestion category |
| feasibility | VARCHAR(20) |  | Feasibility assessment |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

**Indexes**: `category`, `target`

---

### 14. geographic_mentions
**Purpose**: Geographic locations mentioned in interviews

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | INTEGER | NOT NULL, FK(interviews.id) | Parent interview reference |
| location_name | VARCHAR(100) | NOT NULL | Name of location |
| location_type | VARCHAR(50) |  | Type of location |
| context | TEXT |  | Context of mention |
| sentiment | VARCHAR(20) |  | Sentiment toward location |
| latitude | FLOAT |  | Geocoded latitude |
| longitude | FLOAT |  | Geocoded longitude |

**Location Types**: city, neighborhood, department, landmark
**Indexes**: `location_name`, `location_type`

---

### 15. demographic_indicators
**Purpose**: Inferred demographic information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | INTEGER | NOT NULL, FK(interviews.id) | Parent interview reference |
| age_group | VARCHAR(20) |  | Inferred age group |
| socioeconomic_level | VARCHAR(20) |  | Inferred socioeconomic status |
| education_level | VARCHAR(50) |  | Inferred education level |
| occupation_category | VARCHAR(50) |  | Inferred occupation category |
| age_confidence | FLOAT |  | Confidence in age inference |
| socioeconomic_confidence | FLOAT |  | Confidence in socioeconomic inference |

**Age Groups**: youth, adult, senior
**Socioeconomic**: low, middle, high
**Indexes**: `age_group`, `socioeconomic_level`

---

## System Tables

### 16. processing_logs
**Purpose**: Log of all processing activities

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| interview_id | INTEGER | FK(interviews.id) | Associated interview |
| activity_type | VARCHAR(50) | NOT NULL | Type of activity |
| status | VARCHAR(20) | NOT NULL | Activity status |
| details | JSON |  | Additional activity details |
| error_message | TEXT |  | Error details if failed |
| duration | FLOAT |  | Activity duration in seconds |
| started_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Start timestamp |
| completed_at | DATETIME |  | Completion timestamp |

**Activity Types**: ingestion, annotation, extraction, export
**Status Values**: started, completed, failed
**Indexes**: `activity_type`, `status`, `started_at`

---

### 17. daily_summaries
**Purpose**: Daily aggregated statistics for dashboard performance

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| date | VARCHAR(10) | NOT NULL, UNIQUE | Summary date (YYYY-MM-DD) |
| interviews_processed | INTEGER | DEFAULT 0 | Number of interviews processed |
| total_participants | INTEGER | DEFAULT 0 | Total participants across interviews |
| positive_count | INTEGER | DEFAULT 0 | Count of positive sentiment interviews |
| negative_count | INTEGER | DEFAULT 0 | Count of negative sentiment interviews |
| neutral_count | INTEGER | DEFAULT 0 | Count of neutral sentiment interviews |
| mixed_count | INTEGER | DEFAULT 0 | Count of mixed sentiment interviews |
| top_national_priorities | JSON |  | Top national priorities summary |
| top_local_priorities | JSON |  | Top local priorities summary |
| locations_covered | JSON |  | Geographic distribution |
| avg_processing_time | FLOAT |  | Average processing time |
| total_cost | FLOAT |  | Total processing cost |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Indexes**: `date`

---

## Key Relationships

### Primary Relationships
```
interviews (1) ←→ (many) turns
interviews (1) ←→ (many) priorities  
interviews (1) ←→ (many) themes
interviews (1) ←→ (many) annotations
interviews (1) ←→ (many) emotions
interviews (1) ←→ (many) concerns
interviews (1) ←→ (many) suggestions
```

### Conversation Analysis Relationships
```
turns (1) ←→ (many) turn_functional_annotations
turns (1) ←→ (many) turn_content_annotations  
turns (1) ←→ (many) turn_evidence
turns (1) ←→ (many) turn_stance
```

### Analysis Relationships
```
interviews (1) ←→ (1) conversation_dynamics
annotations (1) ←→ (many) turns
```

---

## Query Examples

### Basic Interview Access
```sql
-- Get interview with all related data
SELECT i.*, COUNT(t.id) as turn_count, COUNT(p.id) as priority_count
FROM interviews i
LEFT JOIN turns t ON i.id = t.interview_id  
LEFT JOIN priorities p ON i.id = p.interview_id
WHERE i.interview_id = '058'
GROUP BY i.id;
```

### Turn Analysis with Conditions
```sql
-- Find turns mentioning specific topics
SELECT i.interview_id, t.turn_number, t.speaker, t.text
FROM interviews i
JOIN turns t ON i.id = t.interview_id
WHERE t.text LIKE '%educación%' OR t.text LIKE '%inclusion%'
ORDER BY i.interview_id, t.turn_number;
```

### Priority Analysis
```sql
-- Priority frequency by category and scope
SELECT p.scope, p.category, COUNT(*) as frequency
FROM priorities p
GROUP BY p.scope, p.category
ORDER BY p.scope, frequency DESC;
```

### Conversation Dynamics
```sql
-- Speaker participation analysis
SELECT t.speaker, 
       COUNT(*) as turn_count,
       AVG(t.word_count) as avg_words_per_turn,
       COUNT(DISTINCT t.interview_id) as interviews_participated
FROM turns t
GROUP BY t.speaker
ORDER BY turn_count DESC;
```

---

## Schema Design Principles

### 1. Normalization
- **3rd Normal Form**: Eliminates data redundancy while maintaining query performance
- **Separate Concerns**: Interview metadata, conversation content, and analysis results stored separately
- **Flexible Relationships**: Support for one-to-many and many-to-many relationships

### 2. Scalability
- **Indexed Fields**: Strategic indexes on frequently queried columns
- **JSON Storage**: Flexible storage for variable-length arrays and complex data
- **Partitioning Ready**: Date-based partitioning support for large datasets

### 3. Analysis-Friendly
- **Multi-Level Analysis**: Support for interview-level, turn-level, and conversation-level analysis
- **Temporal Analysis**: Time-based querying and trend analysis
- **Geographic Analysis**: Location-based filtering and spatial analysis capabilities
- **Confidence Tracking**: Uncertainty quantification throughout the analysis pipeline

### 4. Research Compliance
- **Audit Trail**: Complete processing history in logs
- **Data Lineage**: Clear traceability from raw interviews to analysis results
- **Validation Support**: Error tracking and quality assurance fields
- **Export Ready**: Structure supports multiple export formats for research publication

---

## Migration History

### Version 1.0 (2025-06-16)
- Initial schema with basic interview, priority, and theme tables
- Single annotation table for AI-generated analysis

### Version 2.0 (2025-06-16) 
- Added comprehensive turn-level conversation analysis
- Added 6 new tables: turns, turn_functional_annotations, turn_content_annotations, turn_evidence, turn_stance, conversation_dynamics
- Enhanced relationship structure with backref support

### Version 2.1 (2025-06-17)
- Fixed repository pattern inconsistencies
- Added proper session management for all repository classes
- Resolved NOT NULL constraint issues in priorities table

---

*This schema documentation is maintained as a living document and updated with each schema modification.*