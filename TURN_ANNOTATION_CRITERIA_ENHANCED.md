# Enhanced Turn Annotation Criteria (with Gemini Refinements)

## Overview
Each conversation turn in the Uruguay Interview Analysis project is annotated across **9 major dimensions** with **55+ specific criteria**. This comprehensive annotation enables deep qualitative analysis with full cultural and political sensitivity.

## 1. Turn Analysis (Functional)
**Purpose**: Understanding the conversational function of each turn

### Criteria:
- **reasoning**: Chain-of-thought explanation of the analysis
- **primary_function**: Main conversational purpose
  - Original: `greeting`, `problem_identification`, `solution_proposal`, `agreement`, `disagreement`, `question`, `clarification`, `personal_narrative`, `evaluation`, `closing`, `elaboration`, `meta_commentary`
  - **NEW**: `making_a_demand`, `performing_good_citizenry`, `expressing_cynicism`, `offering_deference`
- **secondary_functions**: Additional functions (array)
  - Examples: `justification`, `exemplification`, `comparison`
- **function_confidence**: 0.0-1.0 confidence score

## 2. Content Analysis (Enhanced)
**Purpose**: What topics and scope are discussed

### Criteria:
- **reasoning**: Chain-of-thought for content decisions
- **topics**: Array of subjects discussed
  - Examples: `employment`, `security`, `education`, `health`, `infrastructure`
- **geographic_scope**: Array of spatial references
  - Options: `local`, `national`, `international`
- **temporal_reference**: Time focus
  - Options: `past`, `present`, `future`, `comparison`
- **topic_narrative**: Free text describing how topics are discussed
- **key_actors_mentioned** (NEW): Who is referenced
  - Options: `national_government`, `local_government` (intendencia), `state_enterprise` (UTE, OSE, ANTEL), `private_sector`, `civil_society_orgs`, `unions` (sindicatos), `international_actors`, `citizens_collectively`
- **political_affiliation_reference** (NEW): Political references
  - Options: `explicit_party_mention`, `implicit_ideological_reference`, `reference_to_current_gov`, `reference_to_past_gov`, `none`
- **content_confidence**: 0.0-1.0 confidence score

## 3. Evidence Analysis (Enhanced)
**Purpose**: How claims are supported

### Criteria:
- **reasoning**: Analysis of evidence provided
- **evidence_type**: Type of support for claims
  - Original: `personal_experience`, `family_experience`, `community_observation`, `hearsay`, `media_reference`, `statistical_claim`, `general_assertion`, `hypothetical`, `none`
  - **NEW**: `political_narrative_claim` (e.g., "This always happens under X governments")
- **evidence_narrative**: Description of how evidence is used
- **specificity**: Level of detail
  - Options: `very_specific`, `somewhat_specific`, `general`, `vague`
- **evidence_confidence**: 0.0-1.0 confidence score

## 4. Emotional Analysis (Enhanced)
**Purpose**: Emotional content and certainty

### Criteria:
- **reasoning**: Analysis of emotional expression
- **emotional_valence**: Overall emotional tone
  - Options: `positive`, `mostly_positive`, `neutral`, `mostly_negative`, `negative`, `mixed`
- **emotional_intensity**: 0.0-1.0 intensity score
- **specific_emotions**: Array of identified emotions
  - Examples: `frustration`, `hope`, `concern`, `anger`, `sadness`, `joy`, `fear`
- **emotional_narrative**: Description of emotional journey
- **certainty**: Speaker's confidence level
  - Options: `very_certain`, `somewhat_certain`, `uncertain`, `ambivalent`
- **sense_of_efficacy** (NEW): Does speaker feel their voice matters?
  - Options: `hopeful`, `cynical`, `pragmatic`, `resigned`, `empowered`
- **rhetorical_features**: (EXPANDED)
  - Original: Metaphors, linguistic choices, cultural references
  - **NEW tracking**:
    - Use of vos/voseo and its tone
    - Diminutives/Augmentatives (-ito, -ón) and their function
    - Collective identity markers ("nosotros los Uruguayos", "la gente del barrio")
    - Historical references (2002 crisis, dictatorship, inflation periods)

## 5. Uncertainty Tracking (Refined)
**Purpose**: Annotation quality and ambiguity management

### Criteria:
- **coding_confidence**: 0.0-1.0 annotator confidence
- **ambiguous_aspects**: Array of unclear elements
  - Examples: `function`, `emotional_tone`, `evidence_type`
- **edge_case_flag**: Boolean for unusual cases
- **alternative_interpretations**: Array of other valid readings
- **resolution_strategy**: How ambiguity was resolved
  - Original: `participant_framing_privileged`, `context_from_other_turns`, `conservative_coding`
  - **NEW**: `deliberate_coding_ambiguity` (acknowledging inherent ambiguity)
- **annotator_notes**: Free text observations

## 6. Moral Foundations Analysis (Context-Enhanced)
**Purpose**: Identify moral reasoning patterns

### Criteria:
- **reasoning**: Analysis of moral foundations present
- **care_harm**: 0.0-1.0 (Protection, suffering, compassion)
- **fairness_cheating**: 0.0-1.0 (Justice, equality, corruption)
  - *Uruguay context*: Note links to "amiguismo" (cronyism), corruption, unequal state access
- **loyalty_betrayal**: 0.0-1.0 (Community solidarity, abandonment)
  - *Uruguay context*: Note solidarity within political parties (Frente Amplio, Partidos Tradicionales), unions, local communities
- **authority_subversion**: 0.0-1.0 (Respect, tradition, order)
- **sanctity_degradation**: 0.0-1.0 (Purity, moral decay, values)
- **liberty_oppression**: 0.0-1.0 (Freedom, autonomy, control)
- **dominant_foundation**: Most prominent moral foundation
- **foundations_narrative**: How moral concerns are expressed
- **mft_confidence**: 0.0-1.0 confidence score

## 7. Citation Metadata
**Purpose**: Enable hierarchical citation tracking

### Criteria:
- **key_phrases**: Array of 2-5 important phrases
- **thematic_codes** (renamed from semantic_tags): Standardized labels
  - Categories:
    - Concerns: `security_concern`, `economic_worry`, `health_anxiety`, `education_concern`, `infrastructure_complaint`
    - Emotions: `hope_expression`, `frustration_statement`, `nostalgia_reference`, `pride_expression`, `fear_articulation`
    - Evidence: `personal_experience`, `community_observation`, `statistical_claim`, `media_reference`, `historical_comparison`
    - Solutions: `policy_proposal`, `individual_action`, `community_initiative`, `government_request`
- **quotable_segments**: Array of citable quotes with positions
- **context_dependency**: 0.0-1.0 (reliance on previous turns)
- **standalone_clarity**: 0.0-1.0 (clarity without context)

## 8. Turn Significance
**Purpose**: Overall importance assessment

### Criteria:
- **turn_significance**: Free text explaining why this turn matters

## 9. Agency & Solution Framing (NEW DIMENSION)
**Purpose**: Analyze who the speaker believes is responsible for problems and who has the power to implement solutions

### Criteria:
- **reasoning**: Chain-of-thought for this analysis
- **problem_attribution**: Who or what is blamed for the identified problem?
  - Options: `national_government`, `local_government`, `specific_politician_or_party`, `private_sector_failure`, `market_forces`, `foreign_influence`, `societal_decay_or_values`, `citizen_apathy_or_behavior`, `systemic_issue`, `unattributed`
- **solution_locus**: Who does the speaker believe should solve the problem?
  - Options: `state_intervention` (more regulation/spending), `market_based_solution` (less regulation/privatization), `community_action`, `individual_responsibility`, `technological_fix`
- **citizen_role_conception**: How does the speaker see their own role and other citizens?
  - Options: `active_participant` (co-creator of solutions), `watchdog` (demanding accountability), `voter` (role is primarily electoral), `client_of_state` (passive recipient of services), `victim` (powerless)
- **framing_narrative**: Free text describing the speaker's theory of change
- **framing_confidence**: 0.0-1.0 confidence score

## 10. Open-Ended Observations (NEW DIMENSION)
**Purpose**: Capture insights beyond structured categories

### Criteria:
- **unexpected_themes**: Themes or patterns not fitting standard categories
  - Examples: Digital divide impacts, climate change concerns, mental health stigma
- **cultural_nuances**: Cultural/contextual observations requiring explanation
  - Examples: Local idioms, generational differences, community traditions
- **analytical_hunches**: Interpretive insights or hypotheses worth exploring
  - Examples: Underlying anxieties, unspoken assumptions, emerging social patterns
- **methodological_notes**: Observations about interview dynamics or data quality
  - Examples: Participant hesitation on certain topics, interviewer influence, rapport changes
- **quotable_moments**: Particularly striking expressions beyond the categories
  - Examples: Metaphors, personal stories, philosophical reflections

This dimension is crucial for:
- Preserving the interpretive richness of qualitative analysis
- Identifying emergent themes for future coding iterations
- Capturing context that defies categorization
- Maintaining analytical flexibility
- Addressing the "rigidity of pre-defined criteria" limitation

## Summary of Enhancements

### New Criteria Added:
1. **Consultation-specific functions**: making_a_demand, performing_good_citizenry
2. **Political context**: key_actors_mentioned, political_affiliation_reference
3. **Political evidence**: political_narrative_claim
4. **Political affect**: sense_of_efficacy
5. **Cultural rhetorical features**: voseo, diminutives, collective identity markers
6. **Agency dimension**: Complete new dimension for political framing

### Total Enhanced Statistics:
- **10 Dimensions** (up from 8)
- **60+ Criteria** (up from 45+)
- **Cultural sensitivity** embedded throughout
- **Political discourse** analysis strengthened
- **Agency and power** analysis added
- **Open-ended flexibility** for emergent insights

### Uruguay-Specific Contextual Notes:
- State enterprises (UTE, OSE, ANTEL) recognized as key actors
- Political party references (Frente Amplio, Partidos Tradicionales)
- Historical framing devices (2002 crisis, dictatorship)
- Regional linguistic features (voseo, River Plate Spanish)
- Concepts like "amiguismo" in fairness/corruption discussions

This enhanced system moves beyond capturing *what* citizens say to deeply analyzing *how* they say it, *why* they frame it that way, and what it reveals about their understanding of politics, society, and their own role within it.