# Uruguay Interview Rich Annotation Guidelines

## Objective
Create a searchable, research-ready summary for each citizen consultation interview that balances structured tags with rich narrative description.

## Input
- Structured interview JSON file with turn IDs (format: interview_id:turn_number)
- Original conversation between interviewers and participants about national/local priorities

## Schema Definition

```json
{
  "interview_id": "string",  // e.g., "072"
  
  "tags": {
    "demographics": ["string"],     // Who is speaking
    "location": ["string"],         // Where they're from
    "organization": ["string"],     // Their affiliation
    "themes": ["string"],          // Major topics discussed
    "emotions": ["string"],        // Emotional registers
    "evidence_types": ["string"],  // How they support claims
    "priority_ranking": ["string"] // Their stated priorities
  },
  
  "summary": {
    "overview": "string",  // 2-3 sentence introduction
    
    "key_themes": [
      {
        "theme": "string",           // Theme identifier
        "tags": ["string"],          // Specific tags for this theme
        "description": "string",     // Rich narrative (3-5 sentences)
        "intensity": "string",       // high|medium|low
        "primary_evidence": [
          {
            "turn": "string",        // e.g., "072:43"
            "quote": "string"        // Key excerpt
          }
        ],
        "elaboration_turns": ["string"]  // Additional supporting turns
      }
    ],
    
    "notable_quotes": [
      {
        "turn": "string",
        "speaker": "string", 
        "text": "string",
        "context": "string",
        "tags": ["string"]
      }
    ],
    
    "conversation_structure": {
      "section_name": {
        "turns": "string",      // e.g., "072:01-072:15"
        "tags": ["string"]      // What happens here
      }
    },
    
    "research_notes": "string"  // Analytical value paragraph
  }
}
```

## Output Structure

### 1. Interview-Level Tags
Create comprehensive tag arrays covering:
- **Demographics**: [age_range, gender, occupation, location_type]
- **Location**: [specific_place, department, urban/rural/small_town]
- **Organization**: [type_of_organization, sector]
- **Themes**: Major topics discussed (use standardized vocabulary below)
- **Emotions**: Dominant emotional registers present
- **Evidence Types**: How participants support their claims
- **Priority Rankings**: What they identified as top concerns

### 2. Rich Thematic Analysis (2-4 major themes)
For each major theme:
- **Natural language description** (3-5 sentences) capturing essence and nuance
- **Key dimensions**: Bullet points of specific aspects discussed
- **Supporting evidence**: 3-5 turn citations with brief quote excerpts
- **Emotional context**: How participants feel about this issue
- **Research significance**: Why this perspective matters

### 3. Notable Quotes (4-6 quotes)
Select quotes that are:
- Concise and powerful (ideally under 150 characters)
- Representative of major themes
- Emotionally resonant
- Policy-relevant
- Unique to this interview's perspective

For each quote provide:
- Exact text
- Turn citation (e.g., "072:43")
- Speaker identifier
- Context (1 sentence)
- Analytical significance
- Emotional register

### 4. Conversation Structure
Map the interview flow:
- Opening/setup (turn ranges)
- Major topic sections with turn ranges
- Key transitions or turning points
- Participant dynamics (who dominates, collaboration patterns)

### 5. Research Value Statement
One paragraph covering:
- What makes this interview unique
- Which research questions it helps answer
- Cross-interview comparison potential
- Policy implications
- Methodological observations

## Standardized Tag Vocabulary

### Theme Tags
- Security: security_concern, crime_problem, drug_issues, violence_fear
- Education: education_decline, teacher_crisis, academic_standards, school_resources
- Health: healthcare_access, mental_health, specialist_shortage, rural_health_gaps
- Economy: employment_concern, economic_worry, salary_insufficiency, opportunity_lack
- Infrastructure: basic_services, road_conditions, public_transport, connectivity
- Governance: political_instability, policy_discontinuity, corruption_perception

### Emotion Tags
- Negative: frustration, anger, fear, anxiety, resignation, disappointment
- Positive: hope, pride, satisfaction, optimism
- Intensity: high_emotion, moderate_emotion, subdued

### Evidence Tags
- personal_experience, professional_observation, community_knowledge
- statistical_claim, media_reference, comparative_example
- specific_incident, general_pattern

### Demographics Tags
```json
"demographics": [
  "female_participant",      // Gender
  "35_49_age",              // Age range  
  "education_professional",  // Occupation category
  "middle_class",           // Socioeconomic (if evident)
  "parent",                 // Life role
  "long_term_resident"      // Community connection
]
```

### Location Tags
```json
"location": [
  "montevideo",             // City/town name
  "canelones",             // Department
  "urban_context",         // or rural_context, small_town
  "capital_city",          // Special designation
  "border_region"          // Geographic feature
]
```

## Complete Annotation Example

```json
{
  "interview_id": "071",
  
  "tags": {
    "demographics": ["female_participants", "50_64_age", "community_leaders", "parents"],
    "location": ["san_javier", "rio_negro", "small_town", "interior"],
    "organization": ["sports_club", "community_organization"],
    "themes": ["security_concern", "education_decline", "mental_health", "drug_problems"],
    "emotions": ["frustration", "concern", "nostalgia", "engagement"],
    "evidence_types": ["personal_experience", "parenting_perspective", "community_observation"],
    "priority_ranking": ["security_first_national", "education_second_national"]
  },
  
  "summary": {
    "overview": "Two women community leaders from a San Javier sports club discuss national priorities. Both are engaged parents who express strong concerns about societal decline, particularly in security and education standards.",
    
    "key_themes": [
      {
        "theme": "security_as_top_priority",
        "tags": ["security_concern", "drug_problems", "youth_vulnerability"],
        "description": "Security emerges as the unequivocal first priority, driven by drug proliferation affecting youth in their small community. The participants link security failures to inadequate legal frameworks and the vulnerability of young people to drug culture.",
        "intensity": "high",
        "primary_evidence": [
          {"turn": "071:07", "quote": "Yo para mí, primero que nada, la seguridad"},
          {"turn": "071:45", "quote": "el tema de droga... se está viendo mucho en la juventud"}
        ],
        "elaboration_turns": ["071:48", "071:52", "071:58"]
      }
    ],
    
    "notable_quotes": [
      {
        "turn": "071:07",
        "speaker": "MR",
        "text": "Yo para mí, primero que nada, la seguridad",
        "context": "Immediate response when asked about national priorities",
        "tags": ["security_concern", "priority_statement", "decisive"]
      }
    ],
    
    "conversation_structure": {
      "opening_priorities": {
        "turns": "071:01-071:08",
        "tags": ["priority_setting", "national_focus"]
      }
    },
    
    "research_notes": "Valuable for understanding rural women's perspectives on national issues. Strong parental lens provides concrete examples of abstract policy concerns."
  }
}
```

## Quality Criteria
- **Accuracy**: All citations must be correct and quotes exact
- **Balance**: Capture both majority views and dissenting voices
- **Searchability**: Use consistent tags that work across interviews
- **Readability**: Natural language should flow well for researchers
- **Completeness**: Cover all major themes, don't cherry-pick

## Processing Notes
- Read the full interview first to understand context
- Identify 2-4 major themes that dominate discussion
- Select quotes that researchers would want to cite
- Note any unique perspectives not found in other interviews
- Flag any ambiguities or uncertainties in understanding