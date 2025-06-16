# Quantitative Insights Framework
## From SQL Tables to Policy Insights with Qualitative Drill-Back

### Overview

This framework demonstrates how structured data extraction enables powerful quantitative analysis while maintaining the ability to drill back into rich qualitative context. Each insight type shows the "what" quantitatively, then allows exploration of the "why" and "how" through source annotations.

---

## 1. Temporal Trend Analysis

### Quantitative Insights
```sql
-- Priority evolution over time
SELECT 
    theme,
    EXTRACT(YEAR_MONTH FROM interview_date) as period,
    COUNT(*) as mentions,
    AVG(priority_rank) as avg_priority,
    AVG(emotional_intensity) as avg_intensity
FROM priorities p
JOIN interviews i ON p.interview_id = i.id
GROUP BY theme, period
ORDER BY period, avg_priority;

-- Emerging issue detection
SELECT 
    theme,
    period,
    mentions,
    LAG(mentions) OVER (PARTITION BY theme ORDER BY period) as prev_mentions,
    (mentions - LAG(mentions) OVER (PARTITION BY theme ORDER BY period)) / LAG(mentions) OVER (PARTITION BY theme ORDER BY period) * 100 as growth_rate
FROM monthly_theme_counts
WHERE growth_rate > 50; -- Issues growing >50% month-over-month
```

**Dashboard Visualization:**
- Line charts showing theme prominence over time
- Heat map of emerging vs. declining concerns
- Alert system for rapidly growing issues

**Drill-Back to Source:**
```sql
-- Get rich context for security concerns spike in March 2025
SELECT 
    i.id,
    i.location,
    a.narrative_elaboration,
    a.key_quotes
FROM annotations a
JOIN interviews i ON a.interview_id = i.id
JOIN priorities p ON i.id = p.interview_id
WHERE p.theme = 'seguridad' 
  AND i.interview_date BETWEEN '2025-03-01' AND '2025-03-31'
ORDER BY p.emotional_intensity DESC;
```

**Policy Insight:** "Security concerns spiked 80% in March 2025" → Click to see actual citizen narratives explaining the crisis

---

## 2. Geographic Pattern Analysis

### Quantitative Insights
```sql
-- Regional priority differences
SELECT 
    i.department,
    p.theme,
    COUNT(*) as mentions,
    AVG(p.priority_rank) as avg_rank,
    AVG(p.emotional_intensity) as intensity
FROM priorities p
JOIN interviews i ON p.interview_id = i.id
GROUP BY i.department, p.theme
HAVING COUNT(*) >= 5  -- Only themes mentioned 5+ times per department
ORDER BY i.department, avg_rank;

-- Urban vs Rural distinctions
SELECT 
    CASE 
        WHEN i.locality_size IN ('capital', 'large_city') THEN 'Urban'
        WHEN i.locality_size IN ('small_town', 'rural') THEN 'Rural'
    END as area_type,
    p.theme,
    COUNT(*) as mentions,
    AVG(p.priority_rank) as avg_priority
FROM priorities p
JOIN interviews i ON p.interview_id = i.id
GROUP BY area_type, p.theme
ORDER BY area_type, avg_priority;
```

**Dashboard Visualization:**
- Choropleth maps showing theme intensity by department
- Urban/rural comparison charts
- Interactive map with drill-down capabilities

**Drill-Back to Source:**
```sql
-- Why is healthcare priority #1 in Artigas but #5 in Montevideo?
SELECT 
    i.department,
    i.locality_size,
    a.priority_summary->'national_priorities'->0->>'narrative_elaboration' as healthcare_narrative
FROM annotations a
JOIN interviews i ON a.interview_id = i.id
JOIN priorities p ON i.id = p.interview_id
WHERE p.theme = 'salud' 
  AND i.department IN ('Artigas', 'Montevideo')
ORDER BY i.department;
```

**Policy Insight:** "Healthcare is 3x more important in border departments" → Read citizen explanations about access barriers

---

## 3. Demographic Analysis

### Quantitative Insights
```sql
-- Generational differences in priorities
SELECT 
    pt.age_group,
    p.theme,
    COUNT(*) as mentions,
    AVG(p.priority_rank) as avg_rank,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY pt.age_group) as percentage
FROM priorities p
JOIN participants pt ON p.interview_id = pt.interview_id
GROUP BY pt.age_group, p.theme
ORDER BY pt.age_group, avg_rank;

-- Gender-based priority patterns
SELECT 
    pt.gender,
    p.theme,
    COUNT(*) as mentions,
    AVG(p.emotional_intensity) as avg_intensity,
    AVG(p.certainty_level) as avg_certainty
FROM priorities p
JOIN participants pt ON p.interview_id = pt.interview_id
GROUP BY pt.gender, p.theme
HAVING COUNT(*) >= 10
ORDER BY pt.gender, avg_intensity DESC;
```

**Dashboard Visualization:**
- Generational priority matrices
- Gender-based emotional intensity comparisons
- Sector-based concern patterns

**Drill-Back to Source:**
```sql
-- Why do young women show high emotional intensity about education?
SELECT 
    i.id,
    pt.age_group,
    pt.gender,
    a.turn_level_annotations->'education_turns'->0->>'emotional_description' as emotion_context,
    a.turn_level_annotations->'education_turns'->0->>'turn_summary' as context
FROM annotations a
JOIN interviews i ON a.interview_id = i.id
JOIN participants pt ON i.id = pt.interview_id
JOIN priorities p ON i.id = p.interview_id
WHERE p.theme = 'educacion' 
  AND pt.age_group = '18-30' 
  AND pt.gender = 'female'
  AND p.emotional_intensity > 0.8;
```

**Policy Insight:** "Young women are 40% more emotionally invested in education issues" → Read their personal stories and proposed solutions

---

## 4. Discourse & Sentiment Analysis

### Quantitative Insights
```sql
-- Emotional landscape across themes
SELECT 
    p.theme,
    AVG(p.emotional_intensity) as avg_intensity,
    AVG(p.certainty_level) as avg_certainty,
    COUNT(CASE WHEN p.emotional_valence = 'positive' THEN 1 END) as positive_mentions,
    COUNT(CASE WHEN p.emotional_valence = 'negative' THEN 1 END) as negative_mentions,
    COUNT(CASE WHEN p.emotional_valence = 'negative' THEN 1 END) * 100.0 / COUNT(*) as negativity_rate
FROM priorities p
GROUP BY p.theme
ORDER BY negativity_rate DESC;

-- Agency attribution patterns
SELECT 
    d.agency_attribution,
    COUNT(*) as frequency,
    AVG(p.emotional_intensity) as avg_intensity,
    STRING_AGG(DISTINCT p.theme, ', ') as associated_themes
FROM discourse_features d
JOIN priorities p ON d.interview_id = p.interview_id
GROUP BY d.agency_attribution
ORDER BY frequency DESC;
```

**Dashboard Visualization:**
- Sentiment radar charts by theme
- Agency attribution pie charts
- Emotional intensity heat maps

**Drill-Back to Source:**
```sql
-- What does "state abandonment" actually look like in citizen discourse?
SELECT 
    i.id,
    i.location,
    a.narrative_features->'agency_attribution'->>'description' as agency_narrative,
    a.key_narratives->'problem'->>'content' as problem_narrative,
    a.turn_level_annotations->>'high_intensity_turns' as emotional_moments
FROM annotations a
JOIN interviews i ON a.interview_id = i.id
JOIN discourse_features d ON i.id = d.interview_id
WHERE d.agency_attribution = 'state_abandonment'
ORDER BY a.overall_emotional_intensity DESC;
```

**Policy Insight:** "70% of mentions about healthcare show 'state abandonment' framing" → Read how citizens actually describe this experience

---

## 5. Network & Relationship Analysis

### Quantitative Insights
```sql
-- Issue co-occurrence patterns
SELECT 
    p1.theme as theme1,
    p2.theme as theme2,
    COUNT(*) as co_occurrences,
    COUNT(*) * 100.0 / (SELECT COUNT(DISTINCT interview_id) FROM priorities) as co_occurrence_rate
FROM priorities p1
JOIN priorities p2 ON p1.interview_id = p2.interview_id AND p1.theme < p2.theme
GROUP BY p1.theme, p2.theme
HAVING co_occurrences >= 5
ORDER BY co_occurrence_rate DESC;

-- Solution-problem linkages
SELECT 
    problem_theme,
    proposed_solution,
    COUNT(*) as frequency,
    AVG(feasibility_rating) as avg_feasibility,
    STRING_AGG(DISTINCT i.department, ', ') as mentioned_in_departments
FROM solutions s
JOIN interviews i ON s.interview_id = i.id
GROUP BY problem_theme, proposed_solution
ORDER BY frequency DESC;
```

**Dashboard Visualization:**
- Network graphs showing issue relationships
- Solution popularity by theme
- Geographic clustering of solution types

**Drill-Back to Source:**
```sql
-- How do citizens connect security and education issues?
SELECT 
    i.id,
    i.location,
    a.analytical_notes->'thematic_connections'->>'security_education_link' as connection_explanation,
    a.turn_level_annotations->>'transition_moments' as narrative_bridges
FROM annotations a
JOIN interviews i ON a.interview_id = i.id
JOIN priorities p1 ON i.id = p1.interview_id
JOIN priorities p2 ON i.id = p2.interview_id
WHERE p1.theme = 'seguridad' 
  AND p2.theme = 'educacion'
  AND a.analytical_notes->'thematic_connections' IS NOT NULL;
```

**Policy Insight:** "Security and education co-occur in 45% of interviews" → See how citizens conceptually link these issues

---

## 6. Early Warning & Prediction

### Quantitative Insights
```sql
-- Rapid sentiment shifts (potential crisis indicators)
WITH sentiment_trends AS (
    SELECT 
        theme,
        EXTRACT(WEEK FROM i.interview_date) as week,
        AVG(p.emotional_intensity) as avg_intensity,
        AVG(p.certainty_level) as avg_certainty,
        COUNT(*) as mentions
    FROM priorities p
    JOIN interviews i ON p.interview_id = i.id
    GROUP BY theme, week
)
SELECT 
    theme,
    week,
    avg_intensity,
    LAG(avg_intensity) OVER (PARTITION BY theme ORDER BY week) as prev_intensity,
    avg_intensity - LAG(avg_intensity) OVER (PARTITION BY theme ORDER BY week) as intensity_change
FROM sentiment_trends
WHERE mentions >= 3  -- Only themes with sufficient data
  AND ABS(avg_intensity - LAG(avg_intensity) OVER (PARTITION BY theme ORDER BY week)) > 0.3  -- Large shifts
ORDER BY ABS(intensity_change) DESC;

-- Emerging vocabulary analysis
SELECT 
    theme,
    specific_issue,
    COUNT(*) as recent_mentions,
    FIRST_VALUE(i.interview_date) OVER (PARTITION BY specific_issue ORDER BY i.interview_date) as first_mention,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY theme) as share_of_theme
FROM priorities p
JOIN interviews i ON p.interview_id = i.id
WHERE i.interview_date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
GROUP BY theme, specific_issue
HAVING recent_mentions >= 3
ORDER BY first_mention DESC, recent_mentions DESC;
```

**Dashboard Visualization:**
- Real-time sentiment tracking with alerts
- Emerging issue detection dashboard
- Geographic spread of new concerns

**Drill-Back to Source:**
```sql
-- What's driving the sudden spike in economic anxiety?
SELECT 
    i.id,
    i.interview_date,
    i.location,
    a.priority_summary->'national_priorities'->0->>'narrative_elaboration' as economic_narrative,
    a.turn_level_annotations->>'crisis_moments' as crisis_language,
    a.analytical_notes->'interviewer_reflections'->>'urgency_indicators' as interviewer_observations
FROM annotations a
JOIN interviews i ON a.interview_id = i.id
JOIN priorities p ON i.id = p.interview_id
WHERE p.theme = 'economia' 
  AND i.interview_date >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
  AND p.emotional_intensity > 0.8
ORDER BY i.interview_date DESC;
```

**Policy Insight:** "Economic anxiety jumped 60% this week" → Read citizen explanations of what changed and why

---

## 7. Cross-Validation Analysis

### Quantitative Insights
```sql
-- Compare interview priorities with poll results
SELECT 
    interview_theme,
    poll_ranking,
    interview_ranking,
    ABS(poll_ranking - interview_ranking) as ranking_difference,
    interview_emotional_intensity,
    poll_importance_score
FROM priority_comparison_view
ORDER BY ranking_difference DESC;

-- Validation of representative sampling
SELECT 
    department,
    interview_sample_size,
    population_percentage,
    interview_percentage,
    ABS(population_percentage - interview_percentage) as representation_gap
FROM geographic_representation_analysis
ORDER BY representation_gap DESC;
```

**Dashboard Visualization:**
- Method comparison matrices
- Sampling bias detection charts
- Triangulation confidence scores

**Drill-Back to Source:**
```sql
-- Why do interviews show different results than polls on healthcare?
SELECT 
    i.department,
    a.priority_summary->'national_priorities' as interview_priorities,
    a.analytical_notes->'methodological_insights'->>'depth_vs_breadth' as method_comparison,
    a.narrative_features->'dominant_frame'->>'description' as framing_differences
FROM annotations a
JOIN interviews i ON a.interview_id = i.id
JOIN priorities p ON i.id = p.interview_id
WHERE p.theme = 'salud'
  AND a.analytical_notes->'methodological_insights' IS NOT NULL;
```

**Policy Insight:** "Interviews rank healthcare higher than polls (rank 2 vs 5)" → Understand the qualitative depth behind quantitative differences

---

## Implementation Dashboard Examples

### Executive Summary Dashboard
```sql
-- Key Performance Indicators
SELECT 
    COUNT(DISTINCT i.id) as total_interviews,
    COUNT(DISTINCT i.department) as departments_covered,
    AVG(a.overall_confidence) as avg_annotation_quality,
    COUNT(DISTINCT p.theme) as unique_themes_identified,
    MAX(i.interview_date) as most_recent_interview
FROM interviews i
JOIN annotations a ON i.id = a.interview_id
JOIN priorities p ON i.id = p.interview_id;
```

### Operational Dashboard
```sql
-- Data quality monitoring
SELECT 
    EXTRACT(WEEK FROM i.interview_date) as week,
    COUNT(*) as interviews_processed,
    AVG(a.overall_confidence) as avg_quality_score,
    COUNT(CASE WHEN a.uncertainty_flags IS NOT NULL THEN 1 END) as flagged_interviews,
    AVG(EXTRACT(EPOCH FROM (a.processing_completed_at - i.interview_date))/3600) as avg_processing_hours
FROM interviews i
JOIN annotations a ON i.id = a.interview_id
GROUP BY week
ORDER BY week DESC;
```

### Research Dashboard
```sql
-- Academic insights
SELECT 
    theme,
    COUNT(*) as total_mentions,
    AVG(emotional_intensity) as avg_intensity,
    COUNT(DISTINCT i.department) as geographic_spread,
    COUNT(DISTINCT CASE WHEN pt.age_group = '18-30' THEN i.id END) as young_mentions,
    COUNT(DISTINCT CASE WHEN pt.age_group = '60+' THEN i.id END) as older_mentions
FROM priorities p
JOIN interviews i ON p.interview_id = i.id
JOIN participants pt ON i.id = pt.interview_id
GROUP BY theme
ORDER BY total_mentions DESC;
```

---

## Key Benefits of This Framework

1. **Quantitative Scale:** Process 1000+ interviews for statistical significance
2. **Qualitative Depth:** Always maintain connection to citizen voice and context  
3. **Real-time Insights:** Dashboard updates as new interviews arrive
4. **Policy Relevance:** Direct connection between metrics and citizen concerns
5. **Academic Rigor:** Multiple validation methods and confidence scoring
6. **Scalable Impact:** Framework replicable across countries and contexts

This two-layer approach gives you the best of both worlds: the power of big data analysis with the richness of qualitative understanding, all while maintaining the ability to drill down from aggregate patterns to individual citizen stories.