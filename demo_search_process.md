# Demo: How Claude Code Would Search Interview Data

## User Query: "What are citizens saying about employment challenges for people with disabilities?"

### Step 1: Claude runs the search command
```bash
uruguay-graph search --tags employment_concern,disability_rights --context-window 2
```

### Step 2: The CLI tool returns JSON results

```json
{
  "query": {
    "tags": ["employment_concern", "disability_rights"],
    "filters": null
  },
  "results": [
    {
      "interview_id": "058",
      "location": "Young, Río Negro",
      "turn_id": 8,
      "text": "La inserción laboral real es fundamental. No sirve de nada tener una ley si no hay seguimiento, si no hay apoyo real para mantener a las personas con discapacidad en sus trabajos.",
      "semantic_tags": ["employment_concern", "disability_rights", "policy_implementation_gap"],
      "context": {
        "before": [
          {
            "turn_id": 7,
            "speaker": "interviewer",
            "text": "¿Cuáles son las principales necesidades que ven?"
          }
        ],
        "after": [
          {
            "turn_id": 9,
            "speaker": "participant",
            "text": "Y la capacitación de los técnicos es otro tema fundamental..."
          }
        ]
      },
      "insight_citations": [
        {
          "insight_id": "INS_058_01",
          "insight_summary": "Gap between disability laws and implementation in employment",
          "confidence": 0.9
        }
      ]
    },
    {
      "interview_id": "071",
      "location": "Salto",
      "turn_id": 23,
      "text": "Mi hijo tiene discapacidad y aunque hay cupos en las empresas, nunca lo llaman. Es como que existe la ley pero no la voluntad.",
      "semantic_tags": ["disability_rights", "employment_concern", "personal_experience"],
      "insight_citations": [
        {
          "insight_id": "INS_071_03",
          "insight_summary": "Parents report discrimination despite quota laws",
          "confidence": 0.85
        }
      ]
    }
  ],
  "pattern_analysis": {
    "co_occurrence": {
      "disability_rights+policy_implementation_gap": 12,
      "disability_rights+frustration_statement": 8
    },
    "geographic_distribution": {
      "Montevideo": 3,
      "Interior": 15
    }
  }
}
```

### Step 3: Claude analyzes patterns across interviews

```bash
uruguay-graph analyze --pattern cross-interview --tags disability_rights,employment_concern --min-mentions 3
```

Returns:
```json
{
  "corpus_insight": {
    "pattern": "Systematic implementation failure of disability employment laws",
    "evidence_strength": "strong",
    "interview_count": 14,
    "total_mentions": 31,
    "key_themes": [
      {
        "theme": "Laws exist but lack enforcement",
        "mentions": 18,
        "example_quotes": [
          "No sirve de nada tener una ley si no hay seguimiento",
          "Es como que existe la ley pero no la voluntad",
          "Las empresas prefieren pagar la multa antes que contratar"
        ]
      },
      {
        "theme": "Need for ongoing support after hiring",
        "mentions": 13,
        "example_quotes": [
          "apoyo real para mantener a las personas con discapacidad en sus trabajos",
          "Se necesita acompañamiento, no solo colocación"
        ]
      }
    ],
    "geographic_pattern": "More acute in interior departments",
    "demographic_pattern": "Raised primarily by healthcare workers and family members"
  }
}
```

### Step 4: Claude formats the insight for the user

Based on analyzing 14 interviews across Uruguay, citizens consistently report a significant gap between disability employment laws and their implementation:

**Key Finding**: While laws mandate employment quotas for people with disabilities, there's systematic non-compliance:
- 18 mentions of companies ignoring quota requirements
- Healthcare workers in Río Negro note: "No sirve de nada tener una ley si no hay seguimiento" (laws are useless without follow-up)
- Parents report their disabled children are never called despite company quotas

**Geographic Pattern**: This issue is more pronounced in interior departments (15 mentions) vs Montevideo (3 mentions).

**Proposed Solutions from Citizens**:
1. Mandatory follow-up and support programs after job placement (13 mentions)
2. Stronger enforcement mechanisms beyond fines
3. Technical training for both disabled workers and their supervisors

The citation chain allows tracing from this corpus-level insight → specific interviews → exact quotes from citizens.

---

## How This Works Technically

1. **In-Memory Graph**: All 37 interviews loaded as a graph structure
2. **Inverted Index**: Maps semantic tags → turn IDs for instant lookup
3. **Citation Chain**: Every insight traces back to specific turns
4. **Pattern Detection**: Co-occurrence analysis reveals hidden connections
5. **Natural Language**: Claude translates queries to tags, formats results beautifully

This is why the MVP doesn't need embeddings or vector search - the semantic tags ARE the search index!