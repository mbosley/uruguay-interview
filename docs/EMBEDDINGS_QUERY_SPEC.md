# Embeddings & Natural Language Query System Specification (Enhanced with Gemini Insights)

## Executive Summary

This specification outlines the implementation of an embeddings-based natural language query system for the Uruguay Interview Analysis project. The system will enhance the existing citation infrastructure by adding semantic search capabilities, enabling researchers to query the corpus using natural language and discover patterns through similarity matching. This version incorporates critical improvements suggested by Gemini's analysis of our pipeline.

## Current Implementation Status

### What We've Already Built: The Hierarchical Citation System

Before detailing the proposed embeddings/query system, it's crucial to understand what's already implemented and working:

#### Existing 4-Pass Annotation Pipeline with Citations

We have a complete, working citation system that creates a three-level hierarchy:

```
Corpus Level (cross-interview patterns)
    ↓ cites
Interview Level (insights & priorities) 
    ↓ cites
Turn Level (individual utterances with semantic tags)
```

#### Implemented Components:

1. **Multi-Pass Annotation System** (`multipass_annotator.py` - 866 lines)
   - **Pass 1**: Interview-level analysis + complete turn inventory
   - **Pass 2**: Batch turn analysis (6 turns per batch for API efficiency)
   - **Pass 3**: Integration and validation (ensures 100% turn coverage)
   - **Pass 4**: Citation-aware interview insights generation
   - Cost: ~$0.0017 per interview for Pass 4, ~$0.05 total per interview
   - Tested on real Uruguay interview data (INT_001_montevideo)

2. **Citation Tracking System** (`citation_tracker.py` - 177 lines)
   ```python
   @dataclass
   class InsightCitation:
       insight_type: str  # "priority", "narrative", etc.
       insight_content: Dict[str, Any]
       primary_citations: List[TurnCitation]  # relevance > 0.8
       supporting_citations: List[TurnCitation]  # relevance 0.5-0.8
       synthesis_note: str
       confidence: float
   ```
   - Validates all turn references exist
   - Calculates relevance scores based on semantic tag overlap
   - Generates synthesis notes explaining citation relationships

3. **Semantic Tagging** (`semantic_tagger.py` - 184 lines)
   - Standardized tag categories:
     - **Concerns**: security_concern, economic_worry, health_anxiety, education_concern, infrastructure_complaint
     - **Emotions**: hope_expression, frustration_statement, nostalgia_reference, pride_expression, fear_articulation
     - **Evidence**: personal_experience, community_observation, statistical_claim, media_reference, historical_comparison
     - **Solutions**: policy_proposal, individual_action, community_initiative, government_request
   - Extracts key phrases with importance scores
   - Identifies quotable segments with character positions

4. **Corpus-Level Analysis** (`corpus_citation.py` - 331 lines)
   ```python
   @dataclass
   class CorpusInsight:
       insight_id: str
       insight_type: str  # "common_priority", "regional_pattern", etc.
       content: Dict[str, Any]
       supporting_interviews: List[InterviewCitation]
       prevalence: float  # e.g., 0.73 = 73% of interviews
       confidence: float
   ```
   - Finds patterns across interviews with citation chains
   - Calculates prevalence percentages
   - Tracks regional variations
   - Maintains full traceability: Corpus → Interview → Turn

5. **Database Schema** (Already deployed)
   ```sql
   -- Turn-level citation metadata
   CREATE TABLE turn_citation_metadata (
       id INTEGER PRIMARY KEY,
       turn_id INTEGER NOT NULL REFERENCES turns(id),
       semantic_tags JSON,        -- ["security_concern", "fear_expression"]
       key_phrases JSON,          -- [{"text": "...", "importance": 0.9}]
       quotable_segments JSON,    -- [{"text": "...", "start": 0, "end": 50}]
       context_dependency FLOAT,  -- 0.0-1.0
       standalone_clarity FLOAT   -- 0.0-1.0
   );
   
   -- Interview insight citations
   CREATE TABLE interview_insight_citations (
       id INTEGER PRIMARY KEY,
       interview_id VARCHAR NOT NULL,
       insight_type VARCHAR NOT NULL,
       citation_data JSON,
       primary_turn_ids JSON,      -- [3, 7, 15]
       supporting_turn_ids JSON,   -- [12, 23]
       confidence_score FLOAT
   );
   ```

#### Example of Current System Output:

```json
{
  "corpus_insight": {
    "pattern": "Security is top priority in urban areas",
    "prevalence": 0.73,
    "supporting_interviews": [
      {
        "interview_id": "INT_001",
        "priority": "neighborhood security",
        "intensity": 0.8,
        "primary_turns": [
          {
            "turn_id": 7,
            "text": "No puedo dormir tranquilo pensando en los robos",
            "tags": ["security_concern", "fear_expression", "personal_experience"]
          }
        ]
      }
    ]
  }
}
```

### Current System Capabilities:

1. **100% Turn Coverage**: Every turn in every interview is analyzed
2. **Full Traceability**: Any corpus-level claim can be traced to specific turns
3. **Semantic Validation**: Citations validated through tag matching
4. **Confidence Scoring**: All insights include confidence scores
5. **Tested with Real Data**: Successfully tested on actual Uruguay interview transcripts

### What the Embeddings System Will Add:

The proposed system will build on this rich, structured foundation by adding:
- Semantic similarity search (not just tag matching)
- Natural language querying
- Cross-interview pattern discovery through vector clustering
- Contextual understanding of dialogue flow
- Real-time exploration capabilities

<!-- GEMINI: Context Questions
1. Given our existing semantic tags, should we generate embeddings at the tag level too?
2. How can we best leverage the existing citation chains for embedding context?
3. Should we embed the synthesis notes to capture human interpretation?
4. What's the best way to combine our structured citations with vector similarity?
5. How do we maintain our traceability guarantee when using approximate vector search?
-->

<!-- GEMINI ANSWERS: Context Integration

1. **Tag-Level Embeddings**: Yes, but strategically. Create "tag profile embeddings" by concatenating all text segments associated with each tag, then embed. This creates a semantic signature for each tag that can be used for tag expansion and similarity matching. Store these separately and update them as new examples are tagged.

2. **Leveraging Citation Chains**: Use citation chains to create "contextual embeddings" - when embedding a turn, include weighted context from its cited turns. For corpus→interview→turn chains, create hierarchical embeddings where child embeddings influence parent embeddings with decreasing weights (e.g., 0.7, 0.3).

3. **Embedding Synthesis Notes**: Absolutely yes. These capture human interpretive insight that raw text misses. Create a separate embedding for synthesis notes and use them as a "interpretive layer" in search, weighted at ~30% of the main content embedding.

4. **Combining Citations with Vector Search**: Implement a "citation boost" score - if a vector search result has existing citations, boost its relevance by 20-30%. Use citations as a "ground truth" for validating vector search quality. Track when vector search misses cited content.

5. **Maintaining Traceability**: Never rely solely on vector similarity. Always maintain direct ID mappings. Use vector search to find candidates, then retrieve full citation metadata. Implement a "citation guarantee" where any result must be traceable to specific turn IDs, even if found via embedding similarity.
-->

<!-- GEMINI: Integration Strategy Questions
1. Should we run the embedding pipeline AFTER the 4-pass annotation completes, or in parallel?
2. How do we handle updates - if an annotation changes, how do we update embeddings efficiently?
3. Should we create a "citation strength" signal for vector search ranking?
4. What's the best way to version embeddings when we update the annotation schema?
5. How do we ensure the NL query system respects the hierarchical citation structure?
-->

<!-- GEMINI ANSWERS: Integration Strategy

1. **Pipeline Timing**: Run AFTER completion. The 4-pass pipeline generates critical metadata (tags, citations, synthesis notes) that should be included in embeddings. Running in parallel risks embedding incomplete data. Exception: You can pre-generate "raw text" embeddings in parallel, then create enriched embeddings after annotation.

2. **Update Handling**: Implement an "embedding queue" with change detection. When annotations update, add to queue with priority based on change magnitude. Use embedding versioning - don't delete old embeddings immediately. Process updates in batches during low-usage periods.

3. **Citation Strength Signal**: Yes! Create a composite "citation_strength" score:
   - Primary citation = 1.0
   - Supporting citation = 0.7
   - Mentioned in synthesis = 0.5
   - Cross-interview citation = 1.2 (multiplier)
   Use this as a ranking boost in vector search results.

4. **Embedding Versioning**: Use a "embedding_version" field with semantic versioning (e.g., "2.1.0"). Major version = embedding model change, Minor = annotation schema change, Patch = bug fixes. Keep last 2 major versions for compatibility. Include version in vector metadata.

5. **Respecting Hierarchy**: Implement "hierarchical search modes":
   - Corpus-first: Search corpus insights → retrieve supporting interviews → get turns
   - Turn-first: Search turns → aggregate to interviews → synthesize patterns
   - Citation-aware: Boost results that are part of existing citation chains
   Default to corpus-first for "what/how many" queries, turn-first for "who said/specific examples".
-->

## What's New in This Enhanced Specification

This document has been significantly enhanced based on Gemini's expert analysis of our 4-pass citation pipeline. The AI research expert identified both strengths (hierarchical processing, exceptional traceability, cost efficiency) and critical weaknesses (error cascade risk, fixed codebook rigidity, meaning atomization) in our current approach.

## Key Enhancements from Pipeline Analysis

Based on Gemini's expert analysis, this sprint will include:

1. **Enhanced Turn Analysis**
   - Inter-turn dynamics tracking (dialogic functions)
   - Agency and locus of control dimensions
   - Problem vs solution orientation tags

2. **Improved Citation System**
   - Explainable relevance scores with component breakdown
   - Contextual citations including full turn text
   - Previous turn context for dialogue understanding

3. **Validation & Quality**
   - Human-in-the-loop validation sampling
   - Contradiction detection within interviews
   - Bottom-up theme emergence for validation

4. **Uruguay-Specific Features**
   - Local terminology and idiom detection
   - Montevideo vs Interior geographic analysis
   - Historical context recognition (dictatorship, 2002 crisis)

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                   Query Interface                         │
│  (Natural language input → Structured results)           │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────┐
│                   Query Engine                            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │Intent Parser│  │Query Planner │  │Result Synthesizer│ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────┐
│                  Hybrid Search Layer                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │Vector Search│  │ Tag Matching │  │ SQL Filtering  │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────┐
│                    Data Layer                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Vector DB   │  │ PostgreSQL   │  │ Embedding Cache│ │
│  │ (Pinecone)  │  │ (Existing)   │  │ (Redis)        │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

<!-- GEMINI: Architecture Questions
1. Should we use a message queue (RabbitMQ/Kafka) between layers for better scalability?
2. How should we handle failover between vector DB providers (Pinecone → Weaviate)?
3. What's the optimal connection pooling strategy between services?
4. Should the Query Engine be stateless or maintain session state?
5. How do we ensure consistency between Vector DB and PostgreSQL during updates?
-->

<!-- GEMINI ANSWERS: Architecture

1. **Message Queue**: Yes, but start simple with AWS SQS or Redis Pub/Sub for the MVP (37 interviews). Use SQS for:
   - Embedding generation tasks (with dead letter queues)
   - Async annotation updates
   - Cache invalidation messages
   Only move to Kafka when you exceed 10K messages/minute or need event replay.

2. **Vector DB Failover**: Implement a "Vector DB Abstraction Layer" with:
   - Common interface (search, upsert, delete)
   - Health checks every 30 seconds
   - Automatic failover with 5-second timeout
   - Query replay for failed operations
   - Pinecone → Weaviate → Local FAISS (degraded mode)

3. **Connection Pooling**:
   - PostgreSQL: 20 connections per service, 100 total
   - Redis: 50 connections (lightweight protocol)
   - Vector DB: 10 connections (API-based)
   - Use PgBouncer for PostgreSQL if exceeding 200 total connections

4. **Query Engine State**: Hybrid approach:
   - Stateless for individual queries (scalability)
   - Session state in Redis for research threads (15-min TTL)
   - State includes: query history, active filters, citation accumulator
   - Pass session_id in API calls

5. **Consistency Strategy**: "Eventually consistent with guarantees":
   - PostgreSQL = source of truth
   - Write to PostgreSQL first, then queue vector updates
   - Use database triggers to capture changes
   - Implement "consistency checker" that runs every hour
   - Allow "strong consistency mode" that waits for both DBs
-->

## Data Model Extensions

### 1. Enhanced Turn Analysis (New from Gemini + User Insight)

```python
# Enhanced turn metadata based on Gemini's suggestions and open-ended fields
class TurnDynamics(Base):
    __tablename__ = 'turn_dynamics'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('conversation_turns.id'), unique=True)
    
    # Inter-turn dynamics
    dialogic_function = Column(String)  # "agrees_with_interviewer", "challenges_premise", "elaborates_own_point", "changes_topic"
    response_to_turn_id = Column(Integer, ForeignKey('conversation_turns.id'))
    
    # Agency and control
    agency_type = Column(String)  # "personal_agency", "institutional_agency", "lack_of_agency"
    agency_score = Column(Float)  # 0.0-1.0
    
    # Problem/solution orientation
    orientation = Column(String)  # "problem_identification", "solution_proposal", "both", "neither"
    solution_specificity = Column(Float)  # 0.0-1.0 if solution present
    
    # Geographic reference
    geographic_reference = Column(String)  # "montevideo", "interior", "both", "none"
    specific_location = Column(String)  # e.g., "Salto", "Canelones"
    
    # Cultural markers
    contains_idiom = Column(Boolean, default=False)
    idiom_text = Column(Text)
    historical_reference = Column(String)  # "dictatorship", "2002_crisis", etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)

class OpenEndedObservations(Base):
    __tablename__ = 'open_ended_observations'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('conversation_turns.id'))
    interview_id = Column(String, ForeignKey('interviews.id'))
    observation_level = Column(String)  # "turn" or "interview"
    
    # Open-ended qualitative fields (NEW)
    unexpected_themes = Column(Text)  # Themes not captured by categories
    cultural_nuances = Column(Text)  # Context requiring explanation
    analytical_hunches = Column(Text)  # Interpretive insights
    methodological_notes = Column(Text)  # Interview dynamics observations
    quotable_moments = Column(Text)  # Striking expressions
    
    # For interview level
    emergent_patterns = Column(Text)  # Patterns defying categorization
    interpretive_insights = Column(Text)  # Holistic interpretations
    areas_for_exploration = Column(Text)  # Future research questions
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # These fields are crucial for:
    # 1. Capturing insights that don't fit predefined categories
    # 2. Preserving the interpretive richness of qualitative analysis
    # 3. Identifying new themes for future coding iterations
    # 4. Maintaining analytical flexibility as Gemini suggested

### 2. Embedding Storage

```python
# Embedding models with enhanced metadata
class TurnEmbedding(Base):
    __tablename__ = 'turn_embeddings'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('conversation_turns.id'), unique=True)
    model_name = Column(String, nullable=False)  # e.g., "text-embedding-3-small"
    embedding_version = Column(String, nullable=False)  # e.g., "v1.0"
    
    # Embedding vectors
    full_text_embedding = Column(LargeBinary)  # Stored as bytes
    embedding_dim = Column(Integer, nullable=False)  # e.g., 1536
    
    # Context embeddings (new)
    with_previous_turn_embedding = Column(LargeBinary)  # Turn + previous turn context
    with_question_embedding = Column(LargeBinary)  # For participant turns, includes interviewer question
    
    <!-- GEMINI: Embedding Storage Questions
    1. Should we use numpy.save format, pickle, or msgpack for serializing embeddings to bytes?
    2. Is PostgreSQL LargeBinary the best choice, or should we use external blob storage (S3)?
    3. Should we compress embeddings? What's the tradeoff between storage and decompression time?
    4. For 37K interviews with ~50 turns each, that's 1.85M embeddings. At 6KB each, that's 11GB. Is this sustainable?
    5. Should we implement embedding versioning to handle model updates?
    6. How do we handle partial embedding failures during batch processing?
    -->
    
    <!-- GEMINI ANSWERS: Embedding Storage
    
    1. **Serialization Format**: Use NumPy's native format with compression:
       ```python
       # Save: np.savez_compressed(buffer, embedding=vector)
       # Load: np.load(buffer)['embedding']
       ```
       This is 30% faster than pickle and produces 40% smaller files than msgpack. For PostgreSQL storage, convert to bytes: `vector.astype(np.float16).tobytes()`
    
    2. **Storage Strategy**: Hybrid approach:
       - PostgreSQL: Store as FLOAT4[] using pgvector extension (not LargeBinary)
       - Enables SQL operations: `ORDER BY embedding <-> query_embedding`
       - For 37K interviews: PostgreSQL can handle it
       - For 370K+: Move to S3 with PostgreSQL storing S3 keys
       - Hot embeddings cached in Redis
    
    3. **Compression**: Yes, but intelligently:
       - Use float16 instead of float32 (50% reduction, <1% accuracy loss)
       - Gzip only for cold storage (S3)
       - Decompression time: ~0.5ms for float16 conversion, acceptable
       - Don't compress hot embeddings in cache
    
    4. **Scalability at 11GB**: Very sustainable with proper architecture:
       - PostgreSQL with pgvector: Handles up to 100GB efficiently
       - Use partitioning by date/region for 37K+ interviews
       - Actual size with float16: ~5.5GB
       - Index size (HNSW): Additional ~2GB
       - Total: ~8GB, fits in memory on modern servers
    
    5. **Embedding Versioning**: Yes, critical for production:
       ```sql
       embedding_version VARCHAR(10) NOT NULL DEFAULT '1.0.0',
       model_name VARCHAR(50) NOT NULL,
       INDEX idx_embedding_version (embedding_version)
       ```
       - Keep compatible versions (minor changes) together
       - Separate tables/partitions for incompatible versions
       - Background migration jobs for version updates
    
    6. **Partial Failure Handling**:
       - Implement checkpointing every 100 embeddings
       - Store state in Redis: `{"job_id": "xyz", "last_processed_turn_id": 1234}`
       - On failure: resume from checkpoint
       - Use transaction batches: commit every 1000 successful embeddings
       - Failed items go to dead letter queue for manual review
       - Maximum 3 retries with exponential backoff
    -->
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Integer)
    
    # Relationships
    turn = relationship("ConversationTurn", back_populates="embedding")

class PhraseEmbedding(Base):
    __tablename__ = 'phrase_embeddings'
    
    id = Column(Integer, primary_key=True)
    turn_id = Column(Integer, ForeignKey('conversation_turns.id'))
    phrase_text = Column(Text, nullable=False)
    phrase_type = Column(String)  # "key_phrase" | "quotable_segment"
    
    embedding = Column(LargeBinary)
    importance_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class InterviewEmbedding(Base):
    __tablename__ = 'interview_embeddings'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(String, ForeignKey('interviews.id'), unique=True)
    
    # Aggregated embeddings
    mean_embedding = Column(LargeBinary)
    weighted_embedding = Column(LargeBinary)  # Weighted by turn significance
    
    # Cluster information
    cluster_id = Column(Integer)
    cluster_distance = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2. Query Metadata

```python
class QueryLog(Base):
    __tablename__ = 'query_logs'
    
    id = Column(Integer, primary_key=True)
    query_text = Column(Text, nullable=False)
    query_embedding = Column(LargeBinary)
    
    # Query analysis
    detected_intent = Column(JSON)  # {type, entities, filters}
    search_strategy = Column(String)  # "vector" | "hybrid" | "structured"
    
    # Results
    result_count = Column(Integer)
    top_result_relevance = Column(Float)
    response_time_ms = Column(Integer)
    
    # Feedback
    user_rating = Column(Integer)  # 1-5 stars
    user_feedback = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Implementation Phases

### Phase 1: Embedding Generation Pipeline

#### 1.1 Embedding Service
```python
# src/embeddings/embedding_service.py
class EmbeddingService:
    def __init__(self, model_name="text-embedding-3-small"):
        self.model_name = model_name
        self.client = OpenAI()
        self.batch_size = 100
        self.cache = Redis()
    
    async def embed_turn(self, turn: ConversationTurn) -> TurnEmbedding:
        """Generate embeddings for a single turn."""
        # Check cache
        cache_key = f"turn_emb:{turn.id}:{self.model_name}"
        if cached := self.cache.get(cache_key):
            return pickle.loads(cached)
        
        <!-- GEMINI: Caching Strategy Questions
        1. What's the optimal Redis cache TTL for embeddings? 86400 seems arbitrary.
        2. Should we implement a multi-tier cache (local memory → Redis → DB)?
        3. How do we handle cache invalidation when annotations are updated?
        4. Should we pre-warm the cache for frequently accessed turns?
        5. What's the memory budget for Redis? How many embeddings can we keep hot?
        -->
        
        <!-- GEMINI ANSWERS: Caching Strategy
        
        1. **Optimal TTL**: Use variable TTL based on access patterns:
           - Hot embeddings (accessed in last hour): 7 days
           - Warm embeddings (accessed in last day): 24 hours
           - Cold embeddings: Don't cache
           - Implement "sliding TTL" - reset on each access
           - Track access patterns to optimize
        
        2. **Multi-Tier Cache**: Yes, absolutely:
           - L1 (Local): LRU cache, 100MB, ~17K embeddings (using float16)
           - L2 (Redis): 2GB, ~350K embeddings
           - L3 (PostgreSQL): Full storage
           - Cache-aside pattern with write-through for updates
           - 90% hit rate achievable with proper warming
        
        3. **Cache Invalidation**: Event-driven invalidation:
           ```python
           # On annotation update:
           1. Delete from all cache tiers
           2. Publish invalidation event: {"type": "turn_updated", "turn_id": 123}
           3. Background job re-generates embedding
           4. Pre-populate caches with new embedding
           ```
           Use cache tags for bulk invalidation by interview_id
        
        4. **Cache Pre-warming**: Smart warming strategy:
           - On startup: Load top 1000 most-accessed embeddings
           - After invalidation: Immediately regenerate and cache
           - Predictive warming: Cache related turns when one is accessed
           - Daily job: Refresh cache with previous day's popular embeddings
           - Keep "access_count" and "last_accessed" in Redis
        
        5. **Redis Memory Budget**:
           - Recommended: 4GB for MVP, 16GB for scale
           - With 4GB and float16: ~700K embeddings
           - Reserve 20% for other data (sessions, queues)
           - Use Redis eviction policy: "allkeys-lru"
           - Monitor memory usage, alert at 80%
           - Cost: ~$50/month for 4GB Redis on AWS
        -->
        
        # Generate embedding
        full_text = turn.text
        response = await self.client.embeddings.create(
            input=full_text,
            model=self.model_name
        )
        
        <!-- GEMINI: API Rate Limiting Questions
        1. OpenAI has rate limits - how do we implement exponential backoff?
        2. Should we batch embed multiple turns in a single API call?
        3. What's the optimal batch size considering API limits and response time?
        4. How do we track API costs and implement cost controls?
        5. Should we implement a circuit breaker pattern for API failures?
        -->
        
        <!-- GEMINI ANSWERS: API Rate Limiting
        
        1. **Exponential Backoff Implementation**:
           ```python
           async def embed_with_retry(text, max_retries=5):
               for attempt in range(max_retries):
                   try:
                       return await openai.embed(text)
                   except RateLimitError:
                       wait_time = min(2 ** attempt + random.uniform(0, 1), 60)
                       await asyncio.sleep(wait_time)
               raise Exception("Max retries exceeded")
           ```
           Use token bucket algorithm for proactive rate limiting
        
        2. **Batch Embedding**: Yes, absolutely critical for efficiency:
           - OpenAI supports up to 2048 inputs per request
           - Reduces API calls by 50-100x
           - Batch processing reduces cost from $0.02 to $0.0004 per turn
           - Implement intelligent batching with timeout (don't wait forever for a full batch)
        
        3. **Optimal Batch Size**:
           - Sweet spot: 50 texts per batch
           - Why: Balances latency (< 2s) with efficiency
           - Dynamic batching: Start sending after 50 texts OR 1 second
           - For text-embedding-3-small: 8191 token limit per input
           - Monitor p95 response time, adjust batch size accordingly
        
        4. **Cost Tracking & Controls**:
           ```python
           class APIcostTracker:
               daily_limit = 10.00  # $10/day
               hourly_limit = 1.00  # $1/hour
               
               def track_usage(self, tokens, model):
                   cost = calculate_cost(tokens, model)
                   self.redis.incrbyfloat(f"api_cost:{date}:hour:{hour}", cost)
                   if self.get_hourly_cost() > hourly_limit:
                       raise CostLimitExceeded("Hourly limit reached")
           ```
           - Log every API call with cost
           - Implement hard stops at limits
           - Send alerts at 80% of limits
        
        5. **Circuit Breaker Pattern**: Yes, essential for reliability:
           ```python
           class OpenAICircuitBreaker:
               def __init__(self):
                   self.failure_threshold = 5
                   self.recovery_timeout = 60
                   self.state = "closed"  # closed, open, half-open
               
               async def call(self, func, *args):
                   if self.state == "open":
                       if time.time() - self.opened_at > self.recovery_timeout:
                           self.state = "half-open"
                       else:
                           raise CircuitOpenError()
                   
                   try:
                       result = await func(*args)
                       if self.state == "half-open":
                           self.state = "closed"
                       return result
                   except Exception as e:
                       self.record_failure()
                       raise
           ```
        -->
        
        # Create phrase embeddings
        phrase_embeddings = []
        for phrase in turn.citation_metadata.get("key_phrases", []):
            phrase_emb = await self._embed_phrase(phrase["text"])
            phrase_embeddings.append(PhraseEmbedding(
                turn_id=turn.id,
                phrase_text=phrase["text"],
                phrase_type="key_phrase",
                embedding=phrase_emb,
                importance_score=phrase.get("importance", 0.5)
            ))
        
        # Store and cache
        turn_embedding = TurnEmbedding(
            turn_id=turn.id,
            model_name=self.model_name,
            embedding_version="v1.0",
            full_text_embedding=response.data[0].embedding,
            embedding_dim=len(response.data[0].embedding)
        )
        
        self.cache.setex(cache_key, 86400, pickle.dumps(turn_embedding))
        return turn_embedding, phrase_embeddings
```

#### 1.2 Batch Processing Script
```python
# scripts/generate_embeddings.py
async def generate_all_embeddings():
    """Process all turns in batches."""
    service = EmbeddingService()
    
    # Get all turns without embeddings
    turns = session.query(ConversationTurn).filter(
        ~ConversationTurn.embedding.has()
    ).all()
    
    # Process in batches
    for batch in chunks(turns, 100):
        embeddings = await asyncio.gather(*[
            service.embed_turn(turn) for turn in batch
        ])
        
        # Bulk insert
        session.bulk_save_objects([e[0] for e in embeddings])
        session.bulk_save_objects([p for e in embeddings for p in e[1]])
        session.commit()
        
        # Update vector DB
        await update_vector_db(embeddings)
```

### Phase 2: Vector Database Integration

#### 2.1 Vector Index Management
```python
# src/embeddings/vector_store.py
class VectorStore:
    def __init__(self, index_name="uruguay-interviews"):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(index_name)
        
    async def upsert_turn(self, turn: ConversationTurn, embedding: TurnEmbedding):
        """Add turn to vector index with metadata."""
        metadata = {
            "turn_id": turn.id,
            "interview_id": turn.interview_id,
            "speaker": turn.speaker,
            "text_preview": turn.text[:200],
            
            # From citation metadata
            "semantic_tags": turn.citation_metadata.get("semantic_tags", []),
            "topics": turn.content_analysis.get("topics", []),
            
            # From analysis
            "emotional_valence": turn.emotional_analysis.get("emotional_valence"),
            "primary_function": turn.turn_analysis.get("primary_function"),
            
            # Geographic/demographic
            "department": turn.interview.department,
            "municipality": turn.interview.municipality,
            "age_range": turn.interview.participant_profile.get("age_range"),
            
            # Scores for filtering
            "emotional_intensity": turn.emotional_analysis.get("emotional_intensity", 0),
            "significance_score": turn.citation_metadata.get("standalone_clarity", 0.5)
        }
        
        <!-- GEMINI: Vector DB Metadata Questions
        1. What metadata fields does Pinecone support for filtering? Are arrays supported?
        2. How should we handle metadata that exceeds Pinecone's 40KB limit per vector?
        3. Should we denormalize all filtering fields or use a hybrid approach?
        4. How do we handle NULL values in metadata (e.g., missing age_range)?
        5. What's the indexing strategy for high-cardinality fields like interview_id?
        -->
        
        <!-- GEMINI ANSWERS: Vector DB Metadata
        
        1. **Pinecone Metadata Support**:
           - Supported types: strings, numbers, booleans, arrays of strings
           - Arrays ARE supported for filtering: `{"tags": ["security", "employment"]}`
           - Filters: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
           - Array operations: `{"tags": {"$in": ["security"]}}`
           - Maximum 40KB metadata per vector
        
        2. **Handling 40KB Limit**:
           - Store only filterable fields in Pinecone metadata
           - Essential fields: turn_id, interview_id, tags (top 10), department, age_range
           - Move full text and detailed analysis to PostgreSQL
           - Create a "metadata_hash" field for change detection
           - Reference PostgreSQL for full data after vector search
        
        3. **Denormalization Strategy**: Selective denormalization:
           ```json
           {
             // Denormalized for filtering (in Pinecone)
             "interview_id": "INT_001",
             "department": "Montevideo",
             "age_range": "25-34",
             "top_tags": ["security_concern", "economic_worry"],
             "emotion_intensity": 0.8,
             
             // Reference only (fetch from PostgreSQL)
             "full_text_id": 12345,
             "annotation_version": "1.2.0"
           }
           ```
        
        4. **NULL Value Handling**:
           - Use sentinel values: `"age_range": "unknown"` not null
           - Pinecone doesn't index null values (they're unfilterable)
           - Create "has_demographics" boolean for presence checking
           - Default values: age_range="unknown", department="unspecified"
           - Document all sentinel values in data dictionary
        
        5. **High-Cardinality Indexing**:
           - Don't index interview_id directly (too many unique values)
           - Instead, use bucketing: `"interview_batch": "batch_001"`
           - Create composite keys: `"dept_date": "montevideo_20250528"`
           - For interview_id filtering, use PostgreSQL first, then vector search
           - Index strategy: Focus on fields with <1000 distinct values
        -->
        
        # Upsert to Pinecone
        self.index.upsert(
            vectors=[(
                f"turn_{turn.id}",
                embedding.full_text_embedding,
                metadata
            )]
        )
        
        <!-- GEMINI: Vector DB Operations Questions
        1. Should we batch upserts? What's the optimal batch size for Pinecone?
        2. How do we handle partial batch failures?
        3. What's the strategy for vector ID collisions?
        4. Should we implement async upserts with a queue?
        5. How do we monitor index freshness and sync lag?
        -->
        
        <!-- GEMINI ANSWERS: Vector DB Operations
        
        1. **Batch Upserts**: Yes, batching is critical:
           - Optimal batch size: 100 vectors per request
           - Why: Balances throughput vs latency
           - Larger batches (1000) for initial load
           - Smaller batches (50) for real-time updates
           - Pinecone processes ~1000 vectors/second per pod
        
        2. **Partial Batch Failures**: Implement retry logic:
           ```python
           async def batch_upsert_with_retry(vectors, batch_size=100):
               failed = []
               for batch in chunks(vectors, batch_size):
                   try:
                       await index.upsert(batch)
                   except Exception as e:
                       # Try individual upserts for failed batch
                       for vector in batch:
                           try:
                               await index.upsert([vector])
                           except:
                               failed.append(vector)
               return failed  # Send to dead letter queue
           ```
        
        3. **Vector ID Strategy**:
           - Use deterministic IDs: `f"turn_{interview_id}_{turn_number}"`
           - Benefits: Idempotent updates, easy debugging
           - For versions: `f"turn_{interview_id}_{turn_number}_v{version}"`
           - Never use random UUIDs (can't track what's indexed)
           - Collision handling: IDs are unique by design
        
        4. **Async Upserts**: Yes, queue-based approach:
           ```python
           # Producer
           await queue.send("embeddings_to_index", {
               "turn_id": 123,
               "embedding": vector,
               "metadata": meta,
               "priority": "high"  # real-time updates
           })
           
           # Consumer (separate process)
           async def process_embedding_queue():
               batch = []
               async for msg in queue.receive("embeddings_to_index"):
                   batch.append(msg)
                   if len(batch) >= 100 or timeout_reached():
                       await batch_upsert(batch)
                       batch = []
           ```
        
        5. **Monitoring Index Freshness**:
           - Track "last_indexed_at" timestamp per turn
           - Monitor lag: `SELECT COUNT(*) WHERE last_indexed_at < NOW() - INTERVAL '5 minutes'`
           - Set up alerts: >5% vectors out of sync = warning, >10% = critical
           - Implement health check endpoint: `/api/vector-db/health`
           - Daily reconciliation job to find missing vectors
           - Dashboard metrics: indexing rate, queue depth, failure rate
        -->
    
    def build_contextual_embedding(self, turn: ConversationTurn, 
                                 previous_turn: Optional[ConversationTurn] = None):
        """Create embeddings with dialogue context (Gemini suggestion)."""
        contexts = {
            'solo': turn.text,
            'with_previous': f"Previous: {previous_turn.text}\nCurrent: {turn.text}" if previous_turn else turn.text,
            'with_question': self._get_question_context(turn) if turn.speaker == 'participant' else turn.text
        }
        return contexts
```

#### 2.2 Hybrid Search Implementation
```python
# src/search/hybrid_search.py
class HybridSearcher:
    def __init__(self):
        self.vector_store = VectorStore()
        self.db = DatabaseConnection()
        
    async def search(
        self,
        query: str,
        filters: Dict[str, Any],
        top_k: int = 20,
        alpha: float = 0.7  # Weight for vector vs keyword search
    ) -> List[SearchResult]:
        """Perform hybrid vector + keyword search."""
        
        # 1. Vector search
        query_embedding = await self.embed_query(query)
        vector_results = self.vector_store.index.query(
            vector=query_embedding,
            filter=self._build_pinecone_filter(filters),
            top_k=top_k * 2,  # Get more for re-ranking
            include_metadata=True
        )
        
        # 2. Keyword/tag search
        keyword_results = self.db.query(ConversationTurn).filter(
            or_(
                ConversationTurn.citation_metadata["semantic_tags"].contains(
                    filters.get("tags", [])
                ),
                ConversationTurn.text.ilike(f"%{query}%")
            )
        ).limit(top_k * 2).all()
        
        # 3. Combine and re-rank
        combined = self._merge_results(
            vector_results, 
            keyword_results,
            alpha=alpha
        )
        
        <!-- GEMINI: Result Merging Questions
        1. What's the best algorithm for merging vector and keyword results? 
        2. How do we handle duplicate turns from both search methods?
        3. Should alpha be dynamic based on query characteristics?
        4. How do we normalize scores from different sources (0-1 vs unbounded)?
        5. Should we implement learning-to-rank with user feedback?
        -->
        
        <!-- GEMINI ANSWERS: Result Merging
        
        1. **Merging Algorithm**: Use Reciprocal Rank Fusion (RRF):
           ```python
           def reciprocal_rank_fusion(vector_results, keyword_results, k=60):
               scores = {}
               # Vector results
               for rank, result in enumerate(vector_results):
                   scores[result.id] = scores.get(result.id, 0) + 1/(k + rank)
               # Keyword results  
               for rank, result in enumerate(keyword_results):
                   scores[result.id] = scores.get(result.id, 0) + 1/(k + rank)
               # Sort by combined score
               return sorted(scores.items(), key=lambda x: x[1], reverse=True)
           ```
           RRF is parameter-free and works well for heterogeneous sources
        
        2. **Duplicate Handling**: Merge and enrich:
           ```python
           def merge_duplicates(vector_result, keyword_result):
               return {
                   "turn_id": vector_result.id,
                   "text": vector_result.text,
                   "vector_score": vector_result.score,
                   "keyword_score": keyword_result.score,
                   "combined_score": rrf_score,
                   "match_type": "both",  # vs "vector_only" or "keyword_only"
                   "explanation": generate_match_explanation()
               }
           ```
        
        3. **Dynamic Alpha**: Yes, adapt based on query:
           - Short queries (1-3 words): alpha=0.3 (favor keywords)
           - Long queries (>10 words): alpha=0.8 (favor vectors)
           - Question queries: alpha=0.7 (semantic understanding)
           - Exact phrase queries: alpha=0.2 (favor literal matches)
           - Named entity queries: alpha=0.4 (balanced)
        
        4. **Score Normalization**:
           ```python
           def normalize_scores(scores, method="minmax"):
               if method == "minmax":
                   min_score, max_score = min(scores), max(scores)
                   return [(s - min_score) / (max_score - min_score) for s in scores]
               elif method == "zscore":
                   mean, std = np.mean(scores), np.std(scores)
                   return [(s - mean) / std for s in scores]
               elif method == "rank":
                   # Convert to rank-based scores
                   return [1 / (1 + rank) for rank in range(len(scores))]
           ```
           Use minmax for display, rank-based for merging
        
        5. **Learning-to-Rank**: Start simple, evolve:
           - Phase 1: Log clicks/dwell time per result
           - Phase 2: A/B test different alpha values
           - Phase 3: Train LightGBM ranker on click data
           - Features: query length, result type, user demographics
           - Don't over-engineer for 37 interviews; prep infrastructure for scale
        -->
        
        # 4. Fetch full turn data
        return await self._hydrate_results(combined[:top_k])
        
        <!-- GEMINI: Data Hydration Questions  
        1. Should we batch fetch from PostgreSQL or use JOIN?
        2. How do we handle missing turns (deleted after indexing)?
        3. What fields should we eagerly load vs lazy load?
        4. Should we implement a DataLoader pattern to avoid N+1 queries?
        5. How do we handle database connection pooling under load?
        -->
        
        <!-- GEMINI ANSWERS: Data Hydration
        
        1. **Batch Fetch vs JOIN**: Use batch fetch with IN clause:
           ```python
           # Good: Single query for multiple turns
           turn_ids = [r.turn_id for r in search_results]
           turns = db.query(Turn).filter(Turn.id.in_(turn_ids)).all()
           
           # Better: Include essential joins
           turns = db.query(Turn)
                    .options(joinedload(Turn.citation_metadata))
                    .filter(Turn.id.in_(turn_ids)).all()
           ```
           Avoid complex JOINs that fetch entire interview data
        
        2. **Missing Turns**: Graceful degradation:
           ```python
           def hydrate_results(search_results):
               turn_ids = [r.turn_id for r in search_results]
               turns = {t.id: t for t in fetch_turns(turn_ids)}
               
               hydrated = []
               for result in search_results:
                   if result.turn_id in turns:
                       hydrated.append(merge(result, turns[result.turn_id]))
                   else:
                       # Log missing turn
                       logger.warning(f"Turn {result.turn_id} missing")
                       # Include partial result
                       hydrated.append(result.with_error("Content unavailable"))
               return hydrated
           ```
        
        3. **Eager vs Lazy Loading**:
           - Eager: turn text, speaker, semantic_tags, interview_id
           - Lazy: full annotation, interview metadata, other turns
           - Use field projection:
           ```python
           .options(load_only(Turn.id, Turn.text, Turn.speaker))
           ```
           - For search results: 90% of data needs are satisfied by eager fields
        
        4. **DataLoader Pattern**: Yes, absolutely critical:
           ```python
           class TurnDataLoader:
               def __init__(self):
                   self.cache = {}
                   self.pending = set()
               
               async def load(self, turn_id):
                   if turn_id in self.cache:
                       return self.cache[turn_id]
                   
                   self.pending.add(turn_id)
                   if len(self.pending) >= 50 or timeout():
                       await self._batch_load()
                   
                   return self.cache.get(turn_id)
               
               async def _batch_load(self):
                   turns = await fetch_turns(list(self.pending))
                   self.cache.update({t.id: t for t in turns})
                   self.pending.clear()
           ```
        
        5. **Connection Pooling Under Load**:
           - Pool size: min=5, max=20 per service
           - Overflow: max_overflow=10 (temporary connections)
           - Timeout: pool_timeout=30 seconds
           - Recycle: pool_recycle=3600 (close stale connections)
           - Monitor: Track pool wait time, alert if >100ms
           - Circuit breaker: Fail fast if pool exhausted
        -->
    
    def _calculate_explainable_relevance(self, turn: ConversationTurn, query: str, 
                                       query_embedding: np.ndarray) -> Dict[str, float]:
        """Calculate explainable relevance score (Gemini suggestion)."""
        return {
            "semantic_similarity": self._cosine_similarity(query_embedding, turn.embedding),
            "keyword_match": 1.0 if any(word in turn.text.lower() for word in query.lower().split()),
            "tag_match": len(set(query_tags) & set(turn.semantic_tags)) / len(query_tags) if query_tags else 0,
            "intensity_score": turn.emotional_intensity if hasattr(turn, 'emotional_intensity') else 0.5,
            "recency_score": self._calculate_recency(turn.created_at),
            "overall": 0.0  # Weighted combination calculated separately
        }
```

### Phase 3: Natural Language Query Engine

#### 3.1 Intent Parser
```python
# src/query/intent_parser.py
class IntentParser:
    def __init__(self, model="gpt-4.1-nano"):
        self.client = OpenAI()
        self.model = model
        
    async def parse(self, query: str) -> QueryIntent:
        """Parse natural language query into structured intent."""
        
        prompt = f"""
        Analyze this query about citizen interviews from Uruguay:
        "{query}"
        
        Extract:
        1. Query type: search|comparison|aggregation|temporal|causal
        2. Entities:
           - Topics: [security, education, health, etc.]
           - Locations: [departments, municipalities]
           - Demographics: [age, gender, occupation]
           - Emotions: [frustration, hope, fear, etc.]
           - Time: [past, present, future references]
        3. Filters needed
        4. Comparison groups (if comparative)
        5. Aggregation type (if aggregate query)
        
        Return as JSON.
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return QueryIntent(**json.loads(response.choices[0].message.content))
```

#### 3.2 Query Planner
```python
# src/query/query_planner.py
class QueryPlanner:
    def __init__(self):
        self.intent_parser = IntentParser()
        self.searcher = HybridSearcher()
        
    async def plan_query(self, intent: QueryIntent) -> QueryPlan:
        """Convert intent into execution plan."""
        
        if intent.query_type == "search":
            return SearchPlan(
                search_embedding=True,
                filters=intent.to_filters(),
                rerank_by=intent.get_ranking_criteria(),
                include_context=True
            )
            
        elif intent.query_type == "comparison":
            return ComparisonPlan(
                groups=intent.comparison_groups,
                metrics=["emotional_intensity", "topic_distribution"],
                aggregation_level="turn",  # or "interview"
                statistical_tests=["mann_whitney", "chi_square"]
            )
            
        elif intent.query_type == "aggregation":
            return AggregationPlan(
                group_by=intent.aggregation_fields,
                metrics=intent.metrics,
                filters=intent.to_filters(),
                visualization="heatmap"  # or "bar", "network"
            )
```

#### 3.3 Result Synthesizer
```python
# src/query/result_synthesizer.py
class ResultSynthesizer:
    def __init__(self, model="gpt-4.1-mini"):
        self.client = OpenAI()
        self.model = model
        
    async def synthesize(
        self,
        query: str,
        results: List[SearchResult],
        query_type: str
    ) -> NaturalLanguageResponse:
        """Generate natural language response from results."""
        
        # Format results for context
        context = self._format_results(results)
        
        prompt = f"""
        User query: "{query}"
        
        Search results with citations:
        {context}
        
        Generate a natural language response that:
        1. Directly answers the query
        2. Cites specific turns using (Interview_ID, Turn_X) format
        3. Notes patterns if multiple similar responses
        4. Acknowledges limitations if few results
        5. Suggests related queries if appropriate
        
        Keep response concise but complete.
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return NaturalLanguageResponse(
            text=response.choices[0].message.content,
            cited_turns=[r.turn_id for r in results],
            confidence=self._calculate_confidence(results),
            suggested_queries=self._generate_suggestions(query, results)
        )
```

### Phase 4: Query Interface

#### 4.1 Python API
```python
# src/query/corpus_query_api.py
class CorpusQueryAPI:
    def __init__(self):
        self.planner = QueryPlanner()
        self.executor = QueryExecutor()
        self.synthesizer = ResultSynthesizer()
        
    async def query(
        self,
        text: str,
        return_format: str = "natural",  # or "structured", "citations"
        max_results: int = 10
    ) -> QueryResponse:
        """Main entry point for natural language queries."""
        
        # Parse intent
        intent = await self.planner.intent_parser.parse(text)
        
        # Plan query
        plan = await self.planner.plan_query(intent)
        
        # Execute
        results = await self.executor.execute(plan, max_results)
        
        # Format response
        if return_format == "natural":
            response = await self.synthesizer.synthesize(text, results, intent.query_type)
        elif return_format == "structured":
            response = self._format_structured(results)
        else:  # citations
            response = self._format_citations(results)
            
        # Log query
        await self._log_query(text, intent, results, response)
        
        return response
```

#### 4.2 REST API Endpoints
```python
# src/api/query_endpoints.py
@app.post("/api/query")
async def natural_language_query(request: QueryRequest):
    """
    Natural language query endpoint.
    
    Example:
    POST /api/query
    {
        "query": "What are young people's main concerns about employment?",
        "filters": {
            "age_range": ["18-29"],
            "departments": ["Montevideo", "Canelones"]
        },
        "max_results": 20,
        "return_format": "natural"
    }
    """
    api = CorpusQueryAPI()
    response = await api.query(
        text=request.query,
        return_format=request.return_format,
        max_results=request.max_results
    )
    return response

@app.post("/api/query/similar")
async def find_similar_turns(request: SimilarityRequest):
    """Find turns similar to provided text."""
    
@app.get("/api/query/themes")
async def discover_themes(department: str = None):
    """Discover emergent themes using clustering."""

@app.post("/api/query/contradictions")
async def find_contradictions(interview_id: str = None):
    """Find contradictory statements within interviews (Gemini suggestion)."""
```

### Phase 5: Validation & Quality Enhancements (New from Gemini)

#### 5.1 Contradiction Detection
```python
# src/analysis/contradiction_detector.py
class ContradictionDetector:
    def __init__(self):
        self.embedder = EmbeddingService()
        
    async def find_contradictions(self, interview_id: str) -> List[Contradiction]:
        """Find potentially contradictory statements within an interview."""
        
        # Get all turns for interview
        turns = self.db.query(ConversationTurn).filter_by(interview_id=interview_id).all()
        
        contradictions = []
        for i, turn1 in enumerate(turns):
            for turn2 in turns[i+1:]:
                # Check if turns discuss same topic but with opposite sentiment/claims
                if self._same_topic(turn1, turn2) and self._opposite_stance(turn1, turn2):
                    contradiction = Contradiction(
                        turn1_id=turn1.id,
                        turn2_id=turn2.id,
                        topic=self._extract_common_topic(turn1, turn2),
                        confidence=self._calculate_contradiction_confidence(turn1, turn2),
                        explanation=self._generate_explanation(turn1, turn2)
                    )
                    contradictions.append(contradiction)
        
        return contradictions
```

#### 5.2 Human-in-the-Loop Validation
```python
# src/validation/human_validation.py
class ValidationSampler:
    def __init__(self, sample_rate: float = 0.05):
        self.sample_rate = sample_rate
        
    def create_validation_batch(self, annotations: List[Dict]) -> ValidationBatch:
        """Create a batch of annotations for human review."""
        
        # Sample annotations stratified by confidence
        low_confidence = [a for a in annotations if a['confidence'] < 0.7]
        high_confidence = [a for a in annotations if a['confidence'] >= 0.7]
        
        sample = {
            'low_confidence': random.sample(low_confidence, 
                                          min(10, len(low_confidence))),
            'high_confidence': random.sample(high_confidence, 
                                           int(len(high_confidence) * self.sample_rate)),
            'edge_cases': [a for a in annotations if a.get('edge_case_flag', False)]
        }
        
        return ValidationBatch(
            batch_id=str(uuid4()),
            samples=sample,
            created_at=datetime.now(),
            status='pending_review'
        )
```

#### 5.3 Bottom-Up Theme Emergence
```python
# src/analysis/emergent_themes.py
class EmergentThemeAnalyzer:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.clusterer = HDBSCAN(min_cluster_size=5)
        
    async def discover_themes(self, turns: List[ConversationTurn]) -> List[EmergentTheme]:
        """Discover themes bottom-up from turn embeddings (Gemini suggestion)."""
        
        # Get embeddings for all turns
        embeddings = [await self.embedder.embed(turn.text) for turn in turns]
        
        # Cluster embeddings
        clusters = self.clusterer.fit_predict(embeddings)
        
        <!-- GEMINI: Clustering Algorithm Questions
        1. Is HDBSCAN the best choice for small datasets (37 interviews)?
        2. What's the minimum viable cluster size for meaningful themes?
        3. Should we use our semantic tags as features alongside embeddings?
        4. How do we validate that emergent themes are actually different from our predefined categories?
        5. Should we implement hierarchical clustering to find sub-themes?
        -->
        
        <!-- GEMINI ANSWERS: Clustering Algorithms
        
        1. **HDBSCAN for Small Datasets**: No, use Agglomerative Clustering instead:
           ```python
           from sklearn.cluster import AgglomerativeClustering
           
           # For 37 interviews (~1850 turns)
           clusterer = AgglomerativeClustering(
               n_clusters=None,
               distance_threshold=0.5,  # Tune based on dendrogram
               linkage='ward'
           )
           ```
           HDBSCAN needs ~2000+ points to work well. For <100 interviews, hierarchical clustering gives more stable results.
        
        2. **Minimum Cluster Size**:
           - For 37 interviews: minimum 3-4 turns per cluster
           - For 370 interviews: minimum 10-15 turns
           - Rule of thumb: sqrt(total_turns) / 10
           - Validate by human review of smallest clusters
           - Merge tiny clusters with nearest neighbor
        
        3. **Combining Tags with Embeddings**: Yes, but carefully:
           ```python
           def create_hybrid_features(turn, embedding):
               # One-hot encode top 20 most common tags
               tag_features = encode_tags(turn.semantic_tags)  # 20-dim
               
               # Weight embeddings more heavily
               weighted_embedding = embedding * 0.8  # 1536-dim
               weighted_tags = tag_features * 0.2
               
               # Concatenate and normalize
               combined = np.concatenate([weighted_embedding, weighted_tags])
               return combined / np.linalg.norm(combined)
           ```
           Tags provide interpretability, embeddings provide nuance
        
        4. **Validating Emergent vs Predefined Themes**:
           ```python
           def validate_theme_novelty(emergent_theme, predefined_themes):
               # 1. Semantic similarity check
               max_similarity = max(
                   cosine_similarity(emergent_theme.embedding, predef.embedding)
                   for predef in predefined_themes
               )
               
               # 2. Tag overlap analysis
               tag_overlap = calculate_jaccard_similarity(
                   emergent_theme.common_tags,
                   all_predefined_tags
               )
               
               # 3. Human validation prompt
               if max_similarity < 0.7 and tag_overlap < 0.5:
                   return "likely_novel"
               else:
                   return "needs_human_review"
           ```
        
        5. **Hierarchical Sub-themes**: Yes, this is powerful:
           ```python
           # First level: Major themes
           major_themes = AgglomerativeClustering(n_clusters=10)
           
           # Second level: Sub-themes within each major theme
           for theme_id in range(10):
               theme_turns = turns[labels == theme_id]
               if len(theme_turns) > 20:
                   sub_clusters = AgglomerativeClustering(n_clusters=3)
                   sub_labels = sub_clusters.fit_predict(theme_embeddings)
           ```
           This mimics how qualitative researchers naturally organize themes
        -->
        
        # Extract themes from clusters
        themes = []
        for cluster_id in set(clusters):
            if cluster_id == -1:  # Noise
                continue
                
            cluster_turns = [turns[i] for i, c in enumerate(clusters) if c == cluster_id]
            
            # Extract common semantic tags
            common_tags = self._extract_common_tags(cluster_turns)
            
            # Generate theme description
            theme = EmergentTheme(
                cluster_id=cluster_id,
                turn_count=len(cluster_turns),
                common_tags=common_tags,
                representative_quotes=self._get_representative_quotes(cluster_turns),
                description=await self._generate_theme_description(cluster_turns),
                confidence=self._calculate_theme_coherence(cluster_turns, embeddings)
            )
            themes.append(theme)
        
        return themes
    
    def compare_with_top_down(self, emergent_themes: List[EmergentTheme], 
                            predefined_themes: List[Dict]) -> ValidationReport:
        """Compare emergent themes with predefined themes for validation."""
        matches = []
        missed_emergent = []
        missed_predefined = []
        
        # Implementation of theme matching logic
        return ValidationReport(matches, missed_emergent, missed_predefined)
```

### Phase 6: Uruguay-Specific Enhancements (New from Gemini)

#### 6.1 Local Context Recognition
```python
# src/context/uruguay_context.py
class UruguayContextEnhancer:
    def __init__(self):
        self.local_terms = {
            'security': ['pasta base', 'rapiñas', 'copamiento', 'barras bravas'],
            'employment': ['zafral', 'informalidad', 'changas', 'fuga de cerebros'],
            'politics': ['Frente Amplio', 'Partido Nacional', 'Partido Colorado', 
                        'Cabildo Abierto', 'intendencia', 'ediles'],
            'infrastructure': ['OSE', 'UTE', 'ANTEL', 'AFE', 'ANCAP'],
            'social': ['MIDES', 'BPS', 'FONASA', 'Plan Ceibal'],
            'historical': ['dictadura', 'tupamaros', '2002', 'crisis bancaria']
        }
        
        self.idioms = {
            'reverse_prison': ['cárcel al revés', 'presos somos nosotros'],
            'abandonment': ['nos olvidaron', 'nadie se acuerda', 'estamos abandonados'],
            'solidarity': ['entre todos', 'el barrio se organiza', 'nos ayudamos']
        }
        
        self.geographic_markers = {
            'montevideo': ['la capital', 'montevideo', 'la ciudad'],
            'interior': ['el interior', 'mi pueblo', 'acá en el campo', 'en campaña']
        }
    
    def enhance_annotation(self, turn: Dict) -> Dict:
        """Add Uruguay-specific context to turn annotation."""
        
        text = turn['text'].lower()
        
        # Detect local terms
        detected_terms = {}
        for category, terms in self.local_terms.items():
            found = [term for term in terms if term in text]
            if found:
                detected_terms[category] = found
        
        # Detect idioms
        detected_idioms = []
        for idiom_type, phrases in self.idioms.items():
            if any(phrase in text for phrase in phrases):
                detected_idioms.append(idiom_type)
        
        # Detect geographic reference
        geographic_ref = 'none'
        if any(marker in text for marker in self.geographic_markers['montevideo']):
            geographic_ref = 'montevideo'
        elif any(marker in text for marker in self.geographic_markers['interior']):
            geographic_ref = 'interior'
        
        turn['uruguay_context'] = {
            'local_terms': detected_terms,
            'idioms': detected_idioms,
            'geographic_reference': geographic_ref,
            'requires_cultural_note': len(detected_terms) > 0 or len(detected_idioms) > 0
        }
        
        return turn
```

#### 6.2 Enhanced Query Understanding
```python
# src/query/uruguay_query_enhancer.py
class UruguayQueryEnhancer:
    def enhance_query(self, query: str) -> str:
        """Expand query with Uruguay-specific synonyms and context."""
        
        expansions = {
            'seguridad': 'seguridad OR rapiñas OR delincuencia OR pasta base',
            'trabajo': 'trabajo OR empleo OR desempleo OR changas OR zafral',
            'gobierno': 'gobierno OR intendencia OR ministerio OR estado'
        }
        
        enhanced = query
        for term, expansion in expansions.items():
            if term in query.lower():
                enhanced = enhanced.replace(term, f"({expansion})")
        
        return enhanced
```

## Example Query Flows

### Example 1: Simple Topic Search
```
Query: "What do people say about healthcare?"

1. Intent: {type: "search", topics: ["healthcare", "health"], emotions: null}
2. Search: Vector search for "healthcare" + tag filter "health_anxiety"
3. Results: 23 turns across 8 interviews
4. Response: "Citizens express concerns about healthcare primarily focusing on..."
```

### Example 2: Comparative Analysis
```
Query: "How do rural vs urban residents discuss security differently?"

1. Intent: {type: "comparison", topics: ["security"], groups: ["rural", "urban"]}
2. Search: Separate searches for each group
3. Analysis: Compare emotional intensity, specific concerns, proposed solutions
4. Response: "Rural residents emphasize property crime (avg intensity 0.7) while..."
```

### Example 3: Temporal Pattern
```
Query: "How has the discussion of inflation evolved over the interview period?"

1. Intent: {type: "temporal", topics: ["inflation", "economy"], time: "evolution"}
2. Search: Group by date, track topic frequency and sentiment
3. Analysis: Time series of mentions and emotional valence
4. Response: "Early interviews (May 28) show moderate concern, but by May 29..."
```

### Example 4: Contradiction Detection (New)
```
Query: "Find contradictions about government trust in interview INT_001"

1. Intent: {type: "contradiction", interview_id: "INT_001", topic: "government"}
2. Analysis: Compare all turns mentioning government
3. Results: 
   - Turn 4: "El gobierno se olvidó de nosotros" (negative)
   - Turn 10: "Necesitamos que el gobierno apoye más" (expects help)
4. Response: "Participant shows ambivalence: criticizes abandonment but still expects government action"
```

### Example 5: Uruguay-Specific Query (New)
```
Query: "What do people in the interior say about employment?"

1. Query Enhancement: "interior" + "empleo OR trabajo OR changas OR zafral"
2. Geographic Filter: geographic_reference = "interior"
3. Results: Focus on rural employment issues, seasonal work
4. Response: "Rural participants emphasize 'zafral' work and youth migration to Montevideo..."
```

### Example 6: Open-Ended Insights Query (New)
```
Query: "What unexpected themes are emerging from the interviews?"

1. Intent: {type: "emergent", source: "open_observations"}
2. Search: Query open_ended_observations.unexpected_themes
3. Clustering: Group similar observations across interviews
4. Response: "Several unexpected themes not captured by standard categories:
   - Nostalgia for pre-digital community life
   - Climate change impacts on rural livelihoods
   - Mental health stigma preventing help-seeking..."
```

## Performance Considerations

### Embedding Generation
- **Cost**: ~$0.02 per 1000 turns (text-embedding-3-small)
- **Time**: ~2-3 seconds per 100 turns
- **Storage**: ~6KB per turn (1536-dim float32)

<!-- GEMINI: Performance Optimization Questions
1. Should we implement embedding compression (PQ, OPQ) for 10x storage reduction?
2. What's the impact of using float16 vs float32 for embeddings?
3. How do we handle the "cold start" problem for 37K interviews?
4. Should we pre-generate common query embeddings?
5. What's the optimal shard size for distributed vector search?
-->

<!-- GEMINI ANSWERS: Performance Optimization

1. **Embedding Compression**: Not for MVP, yes for scale:
   - For 37 interviews: Use float16, no PQ needed
   - For 37K interviews: Implement Product Quantization
   - PQ settings: 768 dimensions → 96 subquantizers × 8 bits
   - Storage reduction: 6KB → 600 bytes (10x)
   - Accuracy loss: <5% for recall@10
   - Implementation: Use Faiss's IVFPQ index

2. **Float16 vs Float32 Impact**:
   ```python
   # Conversion
   float16_emb = embedding.astype(np.float16)
   
   # Impact:
   # - Storage: 50% reduction (6KB → 3KB per embedding)
   # - Accuracy: 0.3-1% loss in recall@10
   # - Speed: 2x faster memory transfer
   # - Computation: Minimal impact (GPUs handle float16 natively)
   ```
   Recommendation: Use float16 for storage, float32 for computation

3. **Cold Start for 37K Interviews**:
   - Pre-embed in batches of 1000 interviews
   - Use warm replicas during migration:
     1. Keep old system running
     2. Pre-populate new system over 48 hours
     3. Run in shadow mode for 24 hours
     4. Switch traffic gradually (10% → 50% → 100%)
   - Cache warming: Pre-load top 10% most accessed content

4. **Pre-generated Query Embeddings**: Yes, for common queries:
   ```python
   COMMON_QUERIES = {
       "security": embed("security safety crime violence"),
       "employment": embed("work job employment unemployment"),
       "health": embed("health medical hospital doctor"),
       # ... 50 more common themes
   }
   
   # On startup
   for topic, embedding in COMMON_QUERIES.items():
       cache.set(f"query_emb:{topic}", embedding, ttl=None)
   ```

5. **Optimal Shard Size**:
   - For Pinecone: 1M vectors per pod (p1 or s1)
   - For 37K interviews (1.85M turns):
     - Use 2 pods with replica for HA
     - Shard by geographic region or date
   - For custom FAISS:
     - 500K vectors per shard
     - Load shards on-demand based on query filters
   - Query routing by metadata to avoid searching all shards
-->

### Query Performance
- **Vector search**: <100ms for 100k turns
- **Hybrid search**: <200ms typical
- **NL generation**: 1-2 seconds

<!-- GEMINI: Query Performance Questions
1. How do we maintain <100ms with 1M+ vectors? Multiple indices?
2. Should we implement query result caching? What's the cache key?
3. How do we handle "long tail" queries that search entire corpus?
4. What's the p99 latency target and how do we monitor it?
5. Should we implement progressive loading for large result sets?
-->

<!-- GEMINI ANSWERS: Query Performance

1. **Maintaining <100ms at Scale**:
   - Use multiple specialized indices:
     ```python
     indices = {
         "recent": "Last 30 days (hot)",      # 100K vectors
         "security": "Security-tagged turns",   # 200K vectors
         "employment": "Employment-tagged",     # 150K vectors
         "general": "Everything else"          # 550K vectors
     }
     ```
   - Query router selects appropriate index
   - Parallel search across relevant indices
   - Approximate search (top_k=100, nprobe=10)

2. **Query Result Caching**:
   ```python
   def generate_cache_key(query, filters, options):
       # Normalize query (lowercase, remove stop words)
       normalized_query = normalize(query)
       
       # Create deterministic key
       key_parts = [
           normalized_query,
           json.dumps(filters, sort_keys=True),
           f"top_k:{options.get('top_k', 20)}"
       ]
       
       cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
       return f"query_result:{cache_key}"
   ```
   Cache TTL: 1 hour for common queries, 15 min for rare

3. **Long Tail Queries**:
   - Implement query complexity scoring:
     ```python
     if query_complexity_score > threshold:
         # Route to async job queue
         job_id = await enqueue_complex_query(query)
         return {"status": "processing", "job_id": job_id}
     ```
   - Use sampling for exploratory queries
   - Implement timeout (5 seconds) with partial results
   - Suggest query refinement for better performance

4. **P99 Latency Monitoring**:
   - Targets:
     - P50: <50ms
     - P95: <200ms
     - P99: <500ms
   - Monitoring:
     ```python
     @metrics.timer("query.latency")
     async def search(query):
         # Implementation
         pass
     ```
   - Alert if P99 > 500ms for 5 minutes
   - Track by query type and time of day

5. **Progressive Loading**:
   ```python
   async def progressive_search(query, filters):
       # First: Return top 10 immediately
       quick_results = await fast_search(query, top_k=10)
       yield {"results": quick_results, "status": "partial"}
       
       # Second: Deeper search in background
       deep_results = await thorough_search(query, top_k=50)
       yield {"results": deep_results[10:], "status": "complete"}
   ```
   - Use Server-Sent Events or WebSockets
   - Show results as they arrive
   - Critical for user experience at scale
-->

### Optimization Strategies
1. **Caching**: Redis for frequent queries
2. **Pre-computation**: Common aggregations
3. **Incremental updates**: Only embed new turns
4. **Compression**: Quantize embeddings to int8

<!-- GEMINI: System-Wide Optimization Questions
1. How do we implement zero-downtime embedding model updates?
2. What's the indexing strategy for real-time updates vs batch?
3. Should we use GPU acceleration for embedding generation?
4. How do we handle A/B testing of different embedding models?
5. What metrics should we track for continuous optimization?
-->

<!-- GEMINI ANSWERS: System-Wide Optimization

1. **Zero-Downtime Model Updates**:
   ```python
   # Blue-Green Deployment for Embeddings
   class EmbeddingModelManager:
       def __init__(self):
           self.active_model = "v1.0"
           self.models = {
               "v1.0": load_model("text-embedding-3-small"),
               "v1.1": None  # Loaded on demand
           }
       
       async def rolling_update(self, new_version):
           # 1. Load new model
           self.models[new_version] = load_model(new_version)
           
           # 2. Dual-write period (write both, read old)
           self.dual_write = True
           
           # 3. Background migration
           await migrate_embeddings(new_version)
           
           # 4. Switch reads to new model
           self.active_model = new_version
           
           # 5. Clean up old model
           del self.models[old_version]
   ```

2. **Real-time vs Batch Indexing**:
   - Real-time pipeline (for new interviews):
     - Trigger: On annotation completion
     - Latency target: <30 seconds
     - Process: Embed → Index → Cache
   - Batch pipeline (for updates/corrections):
     - Schedule: Every 4 hours
     - Process: Collect changes → Batch embed → Bulk index
     - Handles: Annotation updates, model updates
   - Hybrid for urgent updates: Priority queue jumps batch

3. **GPU Acceleration**:
   - For 37 interviews: Not needed (CPU is fine)
   - For 37K interviews: Yes, use GPU
   - Setup:
     ```python
     # Use sentence-transformers with GPU
     model = SentenceTransformer('...', device='cuda')
     
     # Batch processing on GPU
     embeddings = model.encode(
         sentences,
         batch_size=64,
         show_progress_bar=True,
         convert_to_tensor=True
     )
     ```
   - Cost: ~$0.10/hour on AWS g4dn.xlarge
   - Speed: 100x faster than CPU

4. **A/B Testing Embedding Models**:
   ```python
   class ABTestRouter:
       def __init__(self):
           self.experiments = {
               "exp_001": {
                   "model_a": "text-embedding-3-small",
                   "model_b": "text-embedding-3-large",
                   "traffic_split": 0.1,  # 10% to model_b
                   "metrics": ["click_rate", "relevance_score"]
               }
           }
       
       def route_request(self, user_id, query):
           # Consistent hashing for user stickiness
           if hash(user_id) % 100 < 10:
               model = "model_b"
               log_experiment_exposure(user_id, "exp_001", "model_b")
           else:
               model = "model_a"
           
           return process_with_model(query, model)
   ```

5. **Continuous Optimization Metrics**:
   ```python
   OPTIMIZATION_METRICS = {
       # Performance
       "query_latency_p50": {"target": 50, "unit": "ms"},
       "query_latency_p99": {"target": 500, "unit": "ms"},
       "indexing_lag": {"target": 30, "unit": "seconds"},
       
       # Quality
       "search_click_through_rate": {"target": 0.7},
       "result_relevance_score": {"target": 0.8},
       "zero_result_rate": {"target": 0.05, "lower_is_better": True},
       
       # Cost
       "embedding_cost_per_turn": {"target": 0.0001, "unit": "USD"},
       "cache_hit_rate": {"target": 0.6},
       
       # Scale
       "vectors_indexed_per_minute": {"track_only": True},
       "concurrent_queries": {"track_only": True}
   }
   ```
   Dashboard in Grafana, alerts in PagerDuty
-->

## Migration Plan

### Prerequisites
- Existing citation system fully deployed
- All interviews annotated with current schema
- Vector database account (Pinecone recommended)

### Migration Steps
1. **Infrastructure Setup**
   - Set up vector database (Pinecone) and Redis
   - Configure Uruguay-specific dictionaries and context
   
   <!-- GEMINI: Infrastructure Questions
   1. What's the recommended Pinecone plan for our scale? (p2.x8?)
   2. How much Redis memory do we need? Cluster or single instance?
   3. Should we use Kubernetes for orchestration? Docker Swarm?
   4. What's the disaster recovery strategy for vector indices?
   5. How do we handle multi-region deployment for global researchers?
   -->
   
   <!-- GEMINI ANSWERS: Infrastructure
   
   1. **Pinecone Plan Recommendation**:
      - For MVP (37 interviews, ~2K vectors): **Starter Plan Free**
      - For 370 interviews (~20K vectors): **Starter Plan ($70/mo)**
      - For 3,700 interviews (~200K vectors): **Standard Plan with 1x s1.x1 pod**
      - For 37K interviews (~2M vectors): **Standard Plan with 2x s1.x2 pods**
      
      Why not p2 pods: They're optimized for billions of vectors. For <10M vectors, s1 pods are more cost-effective with similar performance.
   
   2. **Redis Requirements**:
      - For MVP: **4GB single instance** (AWS ElastiCache t3.medium)
        - Handles ~700K cached embeddings (float16)
        - Cost: ~$50/month
      - For Scale: **16GB single instance** (no cluster needed)
        - Redis Cluster adds complexity with minimal benefit at this scale
        - Use Redis Sentinel for HA instead
      - Configuration:
        ```redis
        maxmemory 16gb
        maxmemory-policy allkeys-lru
        save ""  # Disable persistence for cache
        ```
   
   3. **Container Orchestration**:
      - For MVP: **Docker Compose** is sufficient
        ```yaml
        services:
          api:
            deploy:
              replicas: 2
          embedder:
            deploy:
              replicas: 1
          redis:
            image: redis:7-alpine
        ```
      - For Production: **Kubernetes** (specifically EKS or GKE)
        - Use Helm charts for deployment
        - Horizontal Pod Autoscaler for API pods
        - Separate node pools for CPU vs memory-intensive workloads
      - Avoid Docker Swarm (smaller community, fewer tools)
   
   4. **Disaster Recovery for Vector Indices**:
      ```python
      # Daily backup strategy
      class VectorBackupManager:
          async def backup_daily(self):
              # 1. Export vectors with metadata
              vectors = await pinecone.fetch_all()
              
              # 2. Store in S3 with versioning
              s3.put_object(
                  Bucket="embeddings-backup",
                  Key=f"backup/{date}/vectors.parquet",
                  Body=vectors.to_parquet()
              )
              
              # 3. Also backup to secondary region
              await replicate_to_region("us-west-2")
      ```
      - RPO: 24 hours (acceptable for research)
      - RTO: 2 hours (time to rebuild index)
      - Test restoration monthly
   
   5. **Multi-Region Deployment**:
      - Primary architecture: **Single region with CDN**
        - Main deployment: US-East-1 (lowest latency to OpenAI)
        - CloudFront for static assets and API caching
        - Read replicas can be geographic
      - For true multi-region:
        ```
        Regions: us-east-1 (primary), eu-west-1 (replica)
        - PostgreSQL: Aurora Global Database
        - Pinecone: Separate indices per region
        - Redis: Regional caches (no sync needed)
        - Sync: Async replication with 5-minute lag
        ```
      - Route users to nearest region via Route53
   -->
   
2. **Schema Enhancements**
   - Add TurnDynamics table for inter-turn relationships
   - Add contextual embedding columns
   - Add Uruguay context fields
   
3. **Data Processing**
   - Generate embeddings for existing turns (with context variants)
   - Run emergent theme analysis on existing data
   - Detect and store contradictions
   - Add Uruguay-specific annotations retroactively
   
   <!-- GEMINI: Migration Process Questions
   1. How do we handle the 3-4 hour embedding generation for 37 interviews?
   2. Should we implement checkpointing for resumable processing?
   3. How do we validate embedding quality during migration?
   4. What's the rollback strategy if we find issues mid-migration?
   5. Should we run old and new systems in parallel initially?
   -->
   
   <!-- GEMINI ANSWERS: Migration Process
   
   1. **Handling 3-4 Hour Processing**:
      ```python
      # Optimize to reduce to 30-45 minutes
      async def fast_migration():
          # 1. Batch process (100 turns at once)
          batches = chunk_turns(all_turns, size=100)
          
          # 2. Parallel processing (4 workers)
          async with asyncio.TaskGroup() as tg:
              for i, batch in enumerate(batches):
                  tg.create_task(process_batch(batch, worker_id=i%4))
          
          # 3. Progress tracking
          with tqdm(total=len(all_turns)) as pbar:
              async for completed in results:
                  pbar.update(len(completed))
      ```
      Run during off-hours, send completion notification
   
   2. **Checkpointing Implementation**:
      ```python
      class CheckpointedProcessor:
          def __init__(self, redis_client):
              self.redis = redis_client
              self.checkpoint_key = "migration:checkpoint"
          
          async def process_with_checkpoints(self, items):
              # Load checkpoint
              last_processed = self.redis.get(self.checkpoint_key) or 0
              remaining = items[last_processed:]
              
              for i, item in enumerate(remaining, start=last_processed):
                  try:
                      await process_item(item)
                      
                      # Checkpoint every 50 items
                      if i % 50 == 0:
                          self.redis.set(self.checkpoint_key, i)
                          self.redis.expire(self.checkpoint_key, 86400)
                  
                  except Exception as e:
                      logger.error(f"Failed at item {i}: {e}")
                      raise  # Resume from this point
      ```
   
   3. **Embedding Quality Validation**:
      ```python
      async def validate_embedding_quality():
          # 1. Semantic similarity test
          test_pairs = [
              ("seguridad en el barrio", "criminalidad en la zona"),  # Should be similar
              ("educación", "transporte"),  # Should be different
          ]
          
          for text1, text2 in test_pairs:
              sim = cosine_similarity(embed(text1), embed(text2))
              assert 0.7 < sim < 0.9 for similar pairs
          
          # 2. Known-item search test
          test_queries = load_test_queries()  # Pre-defined test set
          for query in test_queries:
              results = await search(query.text)
              assert query.expected_turn_id in top_10_results
          
          # 3. Clustering coherence
          sample_embeddings = random.sample(all_embeddings, 100)
          silhouette_score = calculate_silhouette(sample_embeddings)
          assert silhouette_score > 0.3  # Reasonable separation
      ```
   
   4. **Rollback Strategy**:
      ```python
      class MigrationManager:
          def __init__(self):
              self.feature_flags = FeatureFlags()
              self.states = ["old_only", "shadow", "canary", "full"]
          
          async def rollback(self):
              current = self.feature_flags.get("embedding_system")
              
              if current == "full":
                  # Keep vector data but route to old system
                  self.feature_flags.set("embedding_system", "old_only")
                  logger.alert("Rolled back to tag-based search")
              
              elif current == "canary":
                  # Stop sending traffic to new system
                  self.feature_flags.set("canary_percentage", 0)
              
              # Data is append-only, so no data rollback needed
              # Old system continues working throughout
      ```
   
   5. **Parallel Running Strategy**: Yes, absolutely:
      ```python
      class DualSystemRouter:
          async def search(self, query, user_id):
              # Phase 1: Shadow mode (log but don't use)
              if self.flags.is_enabled("shadow_mode"):
                  asyncio.create_task(self.new_system_search(query))  # Fire and forget
                  return await self.old_system_search(query)
              
              # Phase 2: Canary (small % of traffic)
              if self.should_use_canary(user_id):
                  try:
                      return await self.new_system_search(query)
                  except Exception:
                      # Fallback to old system
                      return await self.old_system_search(query)
              
              # Phase 3: Full migration with fallback
              return await self.new_system_search(query)
      ```
      
      Timeline:
      - Week 1-2: Shadow mode (compare results)
      - Week 3: 10% canary
      - Week 4: 50% traffic
      - Week 5: 100% with fallback
      - Week 6: Remove old system
   -->
   
4. **API Deployment**
   - Deploy enhanced query API with all new endpoints
   - Add validation sampling interface
   - Enable contradiction detection endpoints
   
   <!-- GEMINI: API Deployment Questions
   1. What's the API gateway strategy? Kong? AWS API Gateway?
   2. How do we implement API versioning for backward compatibility?
   3. What's the authentication strategy? OAuth2? API keys?
   4. How do we implement rate limiting per user/organization?
   5. Should we use GraphQL for flexible querying?
   -->
   
   <!-- GEMINI ANSWERS: API Deployment
   
   1. **API Gateway Strategy**: Use **AWS API Gateway** for simplicity:
      - Managed service (no infrastructure to maintain)
      - Built-in rate limiting, API keys, and monitoring
      - Easy integration with Lambda for lightweight endpoints
      - Cost: ~$3.50 per million requests
      
      For complex needs later, consider Kong, but it's overkill for MVP.
   
   2. **API Versioning Implementation**:
      ```python
      # URL path versioning (clearest for API clients)
      @app.route('/api/v1/search', methods=['POST'])
      @app.route('/api/v2/search', methods=['POST'])
      
      # Version routing
      def route_by_version(version, endpoint):
          handlers = {
              'v1': {
                  'search': search_v1,  # Original citation-based
                  'query': None  # Not available in v1
              },
              'v2': {
                  'search': search_v2,  # Enhanced with embeddings
                  'query': natural_language_query  # New in v2
              }
          }
          return handlers[version][endpoint]
      ```
      
      Deprecation policy: Support previous version for 6 months
   
   3. **Authentication Strategy**: Start with **API Keys**, evolve to **JWT**:
      ```python
      # Phase 1: Simple API Keys
      @require_api_key
      async def search(request):
          api_key = request.headers.get('X-API-Key')
          user = await validate_api_key(api_key)
          
      # Phase 2: JWT for user context
      @require_jwt
      async def search(request):
          claims = decode_jwt(request.headers['Authorization'])
          user_id = claims['sub']
          organization = claims['org']
      ```
      
      No need for full OAuth2 unless integrating with third parties
   
   4. **Rate Limiting Implementation**:
      ```python
      # Using Redis for distributed rate limiting
      class RateLimiter:
          def __init__(self, redis_client):
              self.redis = redis_client
              self.limits = {
                  'free': {'requests': 100, 'window': 3600},      # 100/hour
                  'researcher': {'requests': 1000, 'window': 3600}, # 1000/hour
                  'institutional': {'requests': 10000, 'window': 3600}
              }
          
          async def check_rate_limit(self, api_key, tier='free'):
              key = f"rate_limit:{api_key}:{int(time.time() // self.limits[tier]['window'])}"
              
              current = await self.redis.incr(key)
              if current == 1:
                  await self.redis.expire(key, self.limits[tier]['window'])
              
              if current > self.limits[tier]['requests']:
                  raise RateLimitExceeded(
                      f"Limit {self.limits[tier]['requests']}/hour exceeded"
                  )
      ```
   
   5. **GraphQL vs REST**: **Stick with REST** for this use case:
      - GraphQL adds complexity without clear benefit
      - Your queries are not deeply nested (main benefit of GraphQL)
      - REST is simpler for caching and rate limiting
      - Researchers are familiar with REST
      
      However, provide flexible response shaping:
      ```python
      # REST with field selection
      GET /api/v2/search?q=security&fields=turn_id,text,score
      
      # Response shaping
      def shape_response(results, fields=None):
          if not fields:
              return results  # Full response
          
          return [{
              field: getattr(result, field)
              for field in fields.split(',')
              if hasattr(result, field)
          } for result in results]
      ```
   -->
   
5. **Quality Validation**
   - Run bottom-up theme discovery and compare with existing
   - Create initial human validation batches (5% sample)
   - Test Uruguay-specific query enhancements

<!-- GEMINI: Testing Strategy Questions
1. How do we create a representative test dataset from 37 interviews?
2. What's the benchmark for "good" search results? F1 score? NDCG?
3. How do we test the system's behavior at scale (load testing)?
4. Should we implement automated regression tests for query quality?
5. How do we measure and track annotation quality over time?
-->

<!-- GEMINI ANSWERS: Testing Strategy

1. **Representative Test Dataset Creation**:
   ```python
   class TestDatasetBuilder:
       def create_test_set(self, interviews, n_queries=50):
           test_set = {
               'queries': [],
               'relevance_judgments': {}
           }
           
           # 1. Topic-based queries (40%)
           for topic in ['security', 'employment', 'health', 'education']:
               queries = [
                   f"What do people say about {topic}?",
                   f"Main concerns regarding {topic}",
                   f"{topic} in rural areas"
               ]
               test_set['queries'].extend(queries)
           
           # 2. Demographic queries (20%)
           test_set['queries'].extend([
               "Young people's priorities",
               "Women's perspectives on safety",
               "Elderly concerns about healthcare"
           ])
           
           # 3. Complex queries (20%)
           test_set['queries'].extend([
               "Compare urban and rural employment challenges",
               "How does age affect security concerns?"
           ])
           
           # 4. Known-item queries (20%)
           # Select impactful quotes and create queries to find them
           
           # Manual relevance judgments (or use LLM for initial labels)
           for query in test_set['queries']:
               relevant_turns = manually_judge_relevance(query, all_turns)
               test_set['relevance_judgments'][query] = relevant_turns
           
           return test_set
   ```

2. **Search Quality Benchmarks**:
   - Primary metric: **NDCG@10** (Normalized Discounted Cumulative Gain)
     - Target: >0.75 for topic queries
     - Target: >0.80 for known-item queries
   - Secondary metrics:
     - **MRR** (Mean Reciprocal Rank): >0.6
     - **P@5** (Precision at 5): >0.7
     - **Zero-result rate**: <5%
   
   ```python
   def calculate_ndcg(ranked_results, relevance_judgments, k=10):
       dcg = sum(
           (2**relevance_judgments.get(r.id, 0) - 1) / np.log2(i + 2)
           for i, r in enumerate(ranked_results[:k])
       )
       ideal_dcg = sum(
           (2**r - 1) / np.log2(i + 2)
           for i, r in enumerate(sorted(relevance_judgments.values(), reverse=True)[:k])
       )
       return dcg / ideal_dcg if ideal_dcg > 0 else 0
   ```

3. **Load Testing at Scale**:
   ```python
   # Using Locust for load testing
   class SearchUser(HttpUser):
       wait_time = between(1, 3)
       
       @task(70)
       def simple_search(self):
           query = random.choice(self.test_queries)
           self.client.post("/api/v2/search", 
                          json={"query": query, "top_k": 20})
       
       @task(20)
       def complex_search(self):
           self.client.post("/api/v2/search",
                          json={
                              "query": "employment challenges",
                              "filters": {"age_range": "18-29"},
                              "top_k": 50
                          })
       
       @task(10)
       def aggregation_query(self):
           self.client.get("/api/v2/aggregate/themes")
   ```
   
   Target: 100 concurrent users, <200ms p95 response time

4. **Automated Regression Tests**: Yes, essential:
   ```python
   class QueryRegressionTest:
       def __init__(self):
           self.baseline_results = load_baseline()
           self.threshold = 0.9  # 90% similarity required
       
       def test_query_regression(self, query):
           current_results = search(query)
           baseline = self.baseline_results.get(query)
           
           # Check result similarity
           overlap = len(set(current_results) & set(baseline)) / len(baseline)
           assert overlap >= self.threshold, 
                  f"Query '{query}' regression: {overlap:.2%} overlap"
           
           # Check ranking correlation
           correlation = spearmanr(
               [r.id for r in current_results[:10]],
               [r.id for r in baseline[:10]]
           )
           assert correlation > 0.7, f"Ranking changed significantly"
   ```
   
   Run on every deployment, update baseline monthly

5. **Annotation Quality Tracking**:
   ```python
   class AnnotationQualityMonitor:
       def __init__(self):
           self.metrics = {
               'inter_annotator_agreement': [],  # For human validation
               'confidence_distribution': [],     # Track confidence scores
               'tag_consistency': [],            # Same content, same tags?
               'citation_coverage': []           # % insights with citations
           }
       
       def track_batch_quality(self, batch_annotations):
           # 1. Confidence distribution
           confidences = [a.confidence for a in batch_annotations]
           self.metrics['confidence_distribution'].append({
               'mean': np.mean(confidences),
               'std': np.std(confidences),
               'low_confidence_rate': sum(c < 0.6 for c in confidences) / len(confidences)
           })
           
           # 2. Tag consistency (for similar content)
           similar_pairs = find_similar_turns(batch_annotations)
           consistency = calculate_tag_overlap(similar_pairs)
           self.metrics['tag_consistency'].append(consistency)
           
           # 3. Alert on quality degradation
           if self.metrics['confidence_distribution'][-1]['mean'] < 0.7:
               alert("Annotation confidence dropping")
   ```
   
   Dashboard with trends, alert on degradation
-->

### Rollback Plan
- Embeddings are additive (don't modify existing data)
- Can disable vector search, fall back to tag-based
- Remove vector DB connection to fully rollback

## Security & Privacy

### Data Protection
- Embeddings stored separately from PII
- No interview text in vector DB metadata
- Query logs anonymized

### Access Control
- API key required for vector DB
- Rate limiting on query endpoints
- Audit trail for all queries

## Monitoring & Evaluation

### Key Metrics
1. **Query Performance**
   - Response time (p50, p95, p99)
   - Result relevance scores
   - Cache hit rate

2. **Usage Analytics**
   - Query volume by type
   - Most common search terms
   - User satisfaction ratings

3. **System Health**
   - Embedding generation lag
   - Vector DB sync status
   - Storage growth rate

### Quality Assurance (Enhanced with Gemini Insights)
1. **Continuous Validation**
   - Weekly human-in-the-loop review of 5% sample
   - Automated contradiction detection reports
   - Bottom-up vs top-down theme comparison monthly
   
2. **Error Cascade Prevention**
   - Monitor Pass 1 accuracy through emergent theme validation
   - Flag interviews where bottom-up themes diverge significantly
   - Implement confidence thresholds for pipeline progression
   
3. **Cultural Accuracy**
   - Regular review of Uruguay-specific term detection
   - Validation of idiom and cultural reference interpretation
   - Geographic distribution analysis (Montevideo vs Interior)

## Future Enhancements

### Phase 5: Advanced Features
1. **Multi-modal Embeddings**: Include interviewer tone, speaking pace
2. **Cross-lingual Search**: Spanish/English unified search
3. **Conversational Interface**: Multi-turn query refinement
4. **Proactive Insights**: Alert on emerging themes

### Phase 6: Research Tools
1. **Hypothesis Testing**: Statistical analysis on query results  
2. **Citation Networks**: Visualize connection patterns
3. **Longitudinal Analysis**: Track theme evolution
4. **Export Integration**: Direct to papers, presentations

<!-- GEMINI: Strategic Implementation Questions
1. Should we prioritize the embeddings/NL query system or the tool interface for AI assistants?
2. What's the minimum viable product that provides real research value?
3. How do we measure success for a qualitative research tool?
4. Should we open-source any components?
5. What's the sustainability model for maintaining this system?
-->

<!-- GEMINI ANSWERS: Strategic Implementation

1. **Prioritization: Tool Interface First**
   Start with the AI assistant tool interface (Phase 8) because:
   - Immediate value: Researchers can use Claude/GPT to query existing citations
   - Lower technical risk: Builds on working citation system
   - Faster feedback loop: 1 month to MVP vs 3 months
   - Natural evolution: Add embeddings later for better search
   
   Roadmap:
   - Month 1: Basic tool interface with citation search
   - Month 2: Add research threads and summaries
   - Month 3: Integrate embeddings for semantic search
   - Month 4-6: Advanced features (contradictions, clustering)

2. **Minimum Viable Product Definition**:
   ```python
   MVP_FEATURES = {
       'core': [
           'Natural language search with citations',
           'Theme summarization across interviews',
           'Demographic filtering',
           'Export citations to paper/presentation'
       ],
       'nice_to_have': [
           'Contradiction detection',
           'Research threads',
           'Visual network browser'
       ],
       'future': [
           'Multi-language support',
           'Longitudinal analysis',
           'Collaborative features'
       ]
   }
   ```
   
   Success metric: Researchers save 80% time finding relevant quotes

3. **Success Metrics for Qualitative Research Tool**:
   ```python
   SUCCESS_METRICS = {
       # Efficiency metrics
       'time_to_find_quote': {'baseline': '15 min', 'target': '< 2 min'},
       'citations_per_paper': {'baseline': '20', 'target': '50+'},
       'coverage_per_theme': {'baseline': '5 interviews', 'target': '25+'},
       
       # Quality metrics
       'missed_relevant_content': {'target': '< 5%'},
       'citation_accuracy': {'target': '> 95%'},
       'theme_coherence': {'measure': 'human validation score > 4.0/5'},
       
       # Usage metrics
       'daily_active_researchers': {'target': '> 60%'},
       'queries_per_session': {'healthy': '> 10'},
       'export_completion_rate': {'target': '> 80%'},
       
       # Research output metrics  
       'papers_published_using_tool': {'track_quarterly': True},
       'new_insights_discovered': {'track_via_survey': True},
       'policy_recommendations_generated': {'track': True}
   }
   ```

4. **Open Source Strategy**:
   Yes, selectively open-source:
   
   **Open Source**:
   - Citation extraction algorithms
   - Uruguay cultural context dictionaries
   - Evaluation datasets (anonymized)
   - Query interface specification
   
   **Keep Proprietary**:
   - Trained models on interview data
   - Actual interview content
   - Performance optimizations
   
   Benefits: Academic credibility, community contributions, standardization

5. **Sustainability Model**:
   ```python
   SUSTAINABILITY_PLAN = {
       'technical': {
           'infrastructure_cost': '$200-500/month for 37K interviews',
           'maintenance_hours': '10 hours/month',
           'update_cycle': 'Quarterly annotation model updates'
       },
       
       'financial': {
           'model_1': 'Grant funding for 3 years',
           'model_2': 'Institutional subscription ($500/month/institution)',
           'model_3': 'Freemium (basic search free, advanced features paid)',
           'model_4': 'Research partnership with Uruguay government'
       },
       
       'governance': {
           'data_steward': 'Original research institution',
           'technical_lead': 'Rotating between partner universities',
           'community_board': 'Researchers, participants, policymakers',
           'ethics_review': 'Annual review of use and impact'
       },
       
       'growth': {
           'year_1': 'Uruguay interviews only',
           'year_2': 'Add other Latin American countries',
           'year_3': 'Multi-language, multi-country platform',
           'long_term': 'Standard for qualitative policy research'
       }
   }
   ```
   
   Key: Design for low maintenance from day 1, automate everything possible
-->

## Conclusion

This enhanced embedding and query system, incorporating Gemini's expert analysis, will transform the Uruguay Interview corpus from a static dataset into a sophisticated, culturally-aware research platform. 

### Key Improvements from Gemini's Analysis:

1. **Balanced Analysis**: The system now combines top-down holistic understanding with bottom-up emergent theme validation, addressing the risk of confirmation bias.

2. **Explainable AI**: Relevance scores are now transparent and decomposed into understandable components (semantic similarity, keyword match, intensity scores).

3. **Dialogue Awareness**: Inter-turn dynamics tracking captures the interview as a conversation, not isolated statements.

4. **Quality Assurance**: Human-in-the-loop validation and contradiction detection ensure reliability at scale.

5. **Cultural Sensitivity**: Uruguay-specific enhancements ensure the system understands local context, from "pasta base" to the Montevideo-Interior divide.

6. **Analytical Flexibility**: Open-ended observation fields preserve the interpretive richness that structured categories might miss, addressing Gemini's concern about the "rigidity of pre-defined criteria."

As Gemini noted, this pipeline "operationalizes and scales the process of deductive thematic analysis" while maintaining the traceability that makes qualitative research trustworthy. The system excels at answering "what" and "how often" questions, while the enhanced contextual features help preserve the nuance needed for understanding "why."

Researchers will be able to ask complex questions in natural language and receive culturally-aware, citation-backed answers in seconds, dramatically accelerating the research process while maintaining both rigor and cultural authenticity.

## Phase 8: AI Research Assistant Tool Interface

### Overview

This phase transforms the enriched citation system into an intelligent research partner that AI assistants (like Claude) can use as a tool. Based on extensive analysis with Gemini, this interface is designed to scale from our 37-interview proof of concept to thousands of interviews while providing immediate value.

### 8.1 Architectural Foundation for Scale

#### Dual-Engine Database Design
The system uses two complementary data stores to enable both semantic understanding and precise filtering at scale:

```python
class ResearchToolArchitecture:
    """Core architecture enabling scale from 37 to 37,000+ interviews."""
    
    def __init__(self):
        # Vector Database (Pinecone/Weaviate/Milvus)
        self.vector_store = VectorStore(
            purpose="Semantic search and similarity matching",
            scales_to="Millions of embeddings",
            query_time="<100ms for 1M vectors"
        )
        
        # Document/Relational Database (PostgreSQL with JSONB)
        self.structured_store = StructuredStore(
            purpose="Metadata filtering and structured queries",
            enables="Fast demographic/temporal/geographic filtering",
            stores="Full text, annotations, hierarchical codes"
        )
        
        # Query Orchestrator (The Brain)
        self.orchestrator = QueryOrchestrator(
            strategy="Filter first, then semantic search",
            caching="Redis for common queries",
            scaling="Horizontal scaling of each component"
        )
```

#### Two-Step Retrieval Process
```python
async def smart_retrieval(query: str, filters: Dict) -> List[Citation]:
    """Efficient retrieval that scales to massive corpora."""
    
    <!-- GEMINI: Two-Step Retrieval Architecture Questions
    1. What happens if Step 1 returns too many candidates (e.g., 10K+)? Should we sample?
    2. How do we optimize PostgreSQL queries for complex filter combinations?
    3. Should we maintain materialized views for common filter patterns?
    4. What's the optimal candidate pool size before vector search becomes slow?
    5. How do we handle queries with no filters (searching entire corpus)?
    6. Should we implement query routing to bypass Step 1 for certain query types?
    -->
    
    <!-- GEMINI ANSWERS: Two-Step Retrieval Architecture
    
    1. **Handling Large Candidate Pools (10K+)**:
       ```python
       async def smart_candidate_selection(candidates, max_pool=5000):
           if len(candidates) <= max_pool:
               return candidates
           
           # Strategy 1: Stratified sampling by key attributes
           if len(candidates) < 20000:
               return stratified_sample(
                   candidates,
                   strata=['department', 'age_range', 'topic'],
                   n=max_pool
               )
           
           # Strategy 2: Pre-filtering by relevance signals
           else:
               # Use lightweight scoring (no embeddings)
               scored = []
               for c in candidates:
                   score = (
                       c.emotional_intensity * 0.3 +
                       c.citation_count * 0.2 +
                       c.recency_score * 0.1 +
                       c.has_key_terms * 0.4
                   )
                   scored.append((score, c))
               
               # Take top 5000 by pre-score
               return [c for score, c in sorted(scored, reverse=True)[:max_pool]]
       ```
    
    2. **PostgreSQL Query Optimization**:
       ```sql
       -- Create composite indexes for common filter combinations
       CREATE INDEX idx_demo_topic ON turns(department, age_range, topic);
       CREATE INDEX idx_topic_emotion ON turns USING gin(topics) WHERE emotional_intensity > 0.5;
       
       -- Use CTEs for complex queries
       WITH filtered_interviews AS (
           SELECT id FROM interviews 
           WHERE department = ANY($1) 
           AND age_range && $2  -- Array overlap
       ),
       relevant_turns AS (
           SELECT t.* FROM turns t
           JOIN filtered_interviews i ON t.interview_id = i.id
           WHERE t.topics @> $3  -- Contains all topics
           AND t.emotional_intensity >= $4
       )
       SELECT * FROM relevant_turns;
       ```
       
       Use EXPLAIN ANALYZE to verify index usage
    
    3. **Materialized Views**: Yes, for common patterns:
       ```sql
       -- High-emotion security discussions
       CREATE MATERIALIZED VIEW mv_security_high_emotion AS
       SELECT t.*, i.department, i.age_range
       FROM turns t
       JOIN interviews i ON t.interview_id = i.id
       WHERE 'security' = ANY(t.topics)
       AND t.emotional_intensity > 0.7
       WITH DATA;
       
       -- Refresh strategy
       CREATE INDEX ON mv_security_high_emotion(department, age_range);
       
       -- Refresh after batch updates
       REFRESH MATERIALIZED VIEW CONCURRENTLY mv_security_high_emotion;
       ```
       
       Monitor usage, create views for filters used >100 times/day
    
    4. **Optimal Candidate Pool Size**: 
       - Sweet spot: **2,000-5,000 candidates**
       - Why: Pinecone can filter this many IDs efficiently
       - Performance curve:
         - <1K: Minimal overhead (use always)
         - 1K-5K: Linear slowdown (~2ms per 1K)
         - 5K-10K: Noticeable lag (>10ms overhead)
         - >10K: Use sampling strategies
       
       Adaptive approach: Start with 2K, increase if <20 results
    
    5. **No-Filter Queries (Full Corpus)**:
       ```python
       async def handle_unfiltered_query(query):
           # Don't search everything - use smart defaults
           
           # Option 1: Topic extraction
           extracted_topics = extract_topics(query)
           if extracted_topics:
               return search_with_topic_filter(query, extracted_topics)
           
           # Option 2: Search high-significance content only
           return await vector_store.search(
               query_embedding=embed(query),
               filter={
                   "significance_score": {">=": 0.6},
                   "standalone_clarity": {">=": 0.7}
               },
               top_k=50
           )
       ```
       
       Never search all 37K interviews without filters
    
    6. **Query Routing**: Yes, implement smart routing:
       ```python
       class QueryRouter:
           def should_skip_filtering(self, query, filters):
               # Skip PostgreSQL if we have a turn ID
               if filters.get('turn_id'):
                   return True
               
               # Skip if only vector-compatible filters
               vector_only_filters = {'emotional_intensity', 'significance_score'}
               if all(f in vector_only_filters for f in filters.keys()):
                   return True
               
               # Skip for known-item searches
               if self.is_exact_quote_search(query):
                   return True
               
               return False
           
           async def route_query(self, query, filters):
               if self.should_skip_filtering(query, filters):
                   # Direct to vector search
                   return await self.vector_store.search(query, filters)
               else:
                   # Two-step retrieval
                   candidates = await self.get_candidates(filters)
                   return await self.vector_store.search(query, candidates)
       ```
    -->
    
    # Step 1: Structured filtering (fast)
    candidate_ids = await structured_store.filter(
        age_range=filters.get("age"),
        department=filters.get("location"),
        topics=filters.get("topics")
    )  # Returns e.g., 500 relevant turns from 50,000 total
    
    <!-- GEMINI: Filter Implementation Questions
    1. How do we handle OR conditions across different filter types?
    2. Should we use PostgreSQL GIN indexes for JSONB fields?
    3. What's the query plan for filtering 1M+ turns?
    4. How do we handle range queries (e.g., age 25-35)?
    5. Should filters be cached at the SQL level?
    -->
    
    <!-- GEMINI ANSWERS: Filter Implementation
    
    1. **OR Conditions Across Filter Types**:
       ```python
       def build_or_filter(filters):
           # Convert to SQL
           or_conditions = []
           
           # Example: {"or": [{"department": "Montevideo"}, {"age_range": "18-29"}]}
           for condition in filters['or']:
               sql_parts = []
               for field, value in condition.items():
                   if field == 'department':
                       sql_parts.append(f"department = '{value}'")
                   elif field == 'age_range':
                       sql_parts.append(f"age_range && ARRAY['{value}']")
               
               or_conditions.append(f"({' AND '.join(sql_parts)})")
           
           return f"({' OR '.join(or_conditions)})"
       
       # Better: Use SQLAlchemy
       from sqlalchemy import or_, and_
       
       conditions = []
       for cond in filters['or']:
           subconditions = []
           for field, value in cond.items():
               subconditions.append(getattr(Turn, field) == value)
           conditions.append(and_(*subconditions))
       
       query = session.query(Turn).filter(or_(*conditions))
       ```
    
    2. **GIN Indexes for JSONB**: Yes, absolutely:
       ```sql
       -- For semantic_tags array in JSONB
       CREATE INDEX idx_turn_tags ON turns USING gin((citation_metadata->'semantic_tags'));
       
       -- For full JSONB search
       CREATE INDEX idx_turn_metadata ON turns USING gin(citation_metadata);
       
       -- Query using index
       SELECT * FROM turns 
       WHERE citation_metadata->'semantic_tags' @> '["security_concern"]';
       
       -- Even better: Use jsonb_path_ops for smaller index
       CREATE INDEX idx_turn_tags_path ON turns 
       USING gin((citation_metadata->'semantic_tags') jsonb_path_ops);
       ```
       
       GIN indexes are 3-5x larger but queries are 10-100x faster
    
    3. **Query Plan for 1M+ Turns**:
       ```sql
       -- Partition by date for time-based queries
       CREATE TABLE turns_2025_05 PARTITION OF turns
       FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');
       
       -- Query plan optimization
       EXPLAIN (ANALYZE, BUFFERS) 
       SELECT * FROM turns
       WHERE department = 'Montevideo'
       AND topics @> ARRAY['security']
       AND created_at >= '2025-05-01'
       LIMIT 1000;
       
       -- Expected plan:
       -- Bitmap Heap Scan (using multiple indexes)
       --   -> BitmapAnd
       --       -> Bitmap Index Scan on idx_department
       --       -> Bitmap Index Scan on idx_topics
       ```
       
       Key: Ensure LIMIT is pushed down, use covering indexes
    
    4. **Range Query Handling**:
       ```python
       # Age range queries
       age_range_map = {
           '18-24': ['18-24', '18-29'],  # Overlapping ranges
           '25-34': ['25-34', '25-29', '30-34', '18-29'],
           '35-44': ['35-44', '35-49'],
       }
       
       def handle_age_range_query(requested_range):
           # Find all stored ranges that overlap
           overlapping = age_range_map.get(requested_range, [requested_range])
           
           return Turn.age_range.in_(overlapping)
       
       # For numeric ranges
       def handle_intensity_range(min_val, max_val):
           return and_(
               Turn.emotional_intensity >= min_val,
               Turn.emotional_intensity <= max_val
           )
       ```
    
    5. **SQL-Level Filter Caching**:
       ```python
       # Yes, implement filter result caching
       class FilterCache:
           def __init__(self, redis):
               self.redis = redis
               self.ttl = 300  # 5 minutes
           
           def get_cache_key(self, filters):
               # Deterministic key from filters
               return f"filter:{hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()}"
           
           async def get_filtered_ids(self, filters):
               cache_key = self.get_cache_key(filters)
               
               # Check cache
               cached = await self.redis.get(cache_key)
               if cached:
                   return json.loads(cached)
               
               # Execute query
               result_ids = await execute_filter_query(filters)
               
               # Cache if result set is reasonable size
               if len(result_ids) < 10000:
                   await self.redis.setex(
                       cache_key, 
                       self.ttl, 
                       json.dumps(result_ids)
                   )
               
               return result_ids
       ```
       
       Cache hit rate should be >40% for common demographic filters
    -->
    
    # Step 2: Semantic search within filtered set (precise)
    relevant_citations = await vector_store.semantic_search(
        query_embedding=embed(query),
        candidate_ids=candidate_ids,
        top_k=20
    )
    
    <!-- GEMINI: Vector Search Optimization Questions
    1. Can Pinecone handle dynamic ID filters efficiently?
    2. Should we pre-cluster vectors by common attributes?
    3. What's the performance impact of filtering 10K IDs in Pinecone?
    4. Should we implement our own FAISS index for more control?
    5. How do we handle embedding updates without full reindexing?
    -->
    
    <!-- GEMINI ANSWERS: Vector Search Optimization
    
    1. **Pinecone Dynamic ID Filtering**:
       - Yes, but with limits. Pinecone handles ID filters well up to ~5K IDs
       - Implementation:
       ```python
       # Efficient ID filtering
       results = index.query(
           vector=query_embedding,
           filter={
               "turn_id": {"$in": candidate_ids[:5000]}  # Cap at 5K
           },
           top_k=50
       )
       ```
       - For >5K IDs, use metadata filters instead of ID lists
       - Alternative: Create composite metadata field for filtering
    
    2. **Pre-clustering Vectors**: Yes, for common access patterns:
       ```python
       # Create separate namespaces or indexes
       namespaces = {
           "security_urban": "Security topics in Montevideo/Canelones",
           "employment_youth": "Employment for ages 18-29",
           "health_elderly": "Healthcare for 60+",
           "general": "Everything else"
       }
       
       # Route queries to appropriate namespace
       def select_namespace(query, filters):
           if 'security' in query and filters.get('urban'):
               return 'security_urban'
           # ... other routing logic
           return 'general'
       ```
       
       Benefits: 3-5x faster queries for common patterns
    
    3. **Performance Impact of 10K ID Filtering**:
       - Latency increase: ~50-100ms for 10K IDs
       - Memory spike: ~40MB temporary memory usage
       - CPU impact: Minimal if using ID list
       
       Mitigation strategies:
       ```python
       # Break into smaller queries
       async def search_large_candidate_set(candidates, batch_size=2000):
           all_results = []
           
           for batch in chunks(candidates, batch_size):
               results = await index.query(
                   vector=query_embedding,
                   filter={"turn_id": {"$in": batch}},
                   top_k=20
               )
               all_results.extend(results)
           
           # Re-rank combined results
           return sorted(all_results, key=lambda x: x.score)[:50]
       ```
    
    4. **FAISS vs Pinecone**:
       - Stick with Pinecone for MVP and near-term scale
       - Consider FAISS only if:
         - Need custom distance metrics
         - Want to run on-premise
         - Exceed 10M vectors
         - Need sub-10ms latency
       
       If using FAISS:
       ```python
       import faiss
       
       # Build index with metadata filtering
       index = faiss.IndexIDMap(faiss.IndexFlatIP(1536))
       
       # Add ID mapping for filtering
       id_to_metadata = {}  # Maintain separately
       
       # Custom filtering
       def search_with_filter(query_vec, metadata_filter):
           # Get all results
           scores, ids = index.search(query_vec, k=1000)
           
           # Filter by metadata
           filtered = [
               (score, id) for score, id in zip(scores[0], ids[0])
               if matches_filter(id_to_metadata[id], metadata_filter)
           ]
           
           return filtered[:50]
       ```
    
    5. **Embedding Updates Without Full Reindex**:
       ```python
       class IncrementalIndexUpdater:
           def __init__(self, index_name):
               self.index = pinecone.Index(index_name)
               self.update_queue = []
           
           async def update_embedding(self, turn_id, new_embedding, new_metadata):
               # Pinecone supports in-place updates
               await self.index.upsert(
                   vectors=[(
                       f"turn_{turn_id}",
                       new_embedding,
                       new_metadata
                   )],
                   namespace="default"
               )
           
           async def batch_update(self, updates):
               # Batch updates for efficiency
               vectors = [
                   (f"turn_{u['turn_id']}", u['embedding'], u['metadata'])
                   for u in updates
               ]
               
               await self.index.upsert(vectors=vectors)
           
           def schedule_reindex(self):
               # Full reindex only when:
               # 1. Embedding model changes
               # 2. >20% of vectors updated
               # 3. Monthly maintenance window
               pass
       ```
       
       Key: Pinecone's upsert is idempotent and handles updates efficiently
    -->
    
    return relevant_citations
```

### 8.2 Research Thread Management

Instead of simple sessions, the tool maintains parallel research threads:

```python
class ResearchThread:
    """A coherent line of inquiry with its own context and citation set."""
    
    <!-- GEMINI: Thread State Management Questions
    1. How do we persist thread state? Redis with TTL? PostgreSQL?
    2. What's the maximum thread lifetime? When do we garbage collect?
    3. How much context history should we maintain (token limits)?
    4. Should threads be shareable between researchers?
    5. How do we handle thread forking/branching?
    6. What's the memory footprint of 100 active threads?
    -->
    
    <!-- GEMINI ANSWERS: Thread State Management
    
    1. **Thread State Persistence**: Hybrid approach
       ```python
       class ThreadPersistence:
           def __init__(self):
               self.redis = Redis()  # Hot storage
               self.postgres = PostgreSQL()  # Cold storage
           
           async def save_thread(self, thread: ResearchThread):
               # Hot storage for active threads
               await self.redis.setex(
                   f"thread:{thread.id}",
                   ttl=3600,  # 1 hour sliding window
                   value=thread.to_json()
               )
               
               # Async write to PostgreSQL for persistence
               await self.postgres.upsert(
                   'research_threads',
                   id=thread.id,
                   state=thread.to_json(),
                   last_active=datetime.now(),
                   user_id=thread.user_id
               )
           
           async def load_thread(self, thread_id):
               # Try hot storage first
               cached = await self.redis.get(f"thread:{thread_id}")
               if cached:
                   return ResearchThread.from_json(cached)
               
               # Fall back to cold storage
               stored = await self.postgres.get('research_threads', thread_id)
               if stored:
                   # Warm the cache
                   await self.redis.setex(f"thread:{thread_id}", 3600, stored.state)
                   return ResearchThread.from_json(stored.state)
       ```
    
    2. **Thread Lifecycle Management**:
       ```python
       THREAD_LIFECYCLE = {
           'active_ttl': 3600,        # 1 hour of inactivity
           'archive_after': 86400 * 7, # 7 days
           'delete_after': 86400 * 30, # 30 days
           'max_threads_per_user': 20
       }
       
       async def garbage_collect_threads():
           # Run every hour
           now = datetime.now()
           
           # Archive inactive threads
           inactive = await postgres.query(
               """UPDATE research_threads 
                  SET status = 'archived' 
                  WHERE last_active < %s 
                  AND status = 'active'""",
               now - timedelta(days=7)
           )
           
           # Delete old threads
           await postgres.execute(
               "DELETE FROM research_threads WHERE last_active < %s",
               now - timedelta(days=30)
           )
       ```
    
    3. **Context History Limits**:
       ```python
       class ThreadContext:
           def __init__(self):
               self.max_tokens = 8000  # Reserve 8K for context
               self.max_queries = 20   # Last 20 queries
               self.max_citations = 100 # Top 100 most relevant
           
           def add_query(self, query, results):
               # Sliding window of queries
               self.queries.append({
                   'query': query,
                   'timestamp': datetime.now(),
                   'result_summary': self._summarize(results)
               })
               
               # Trim to token limit
               while self._count_tokens() > self.max_tokens:
                   self.queries.pop(0)  # Remove oldest
           
           def get_context_for_llm(self):
               return {
                   'recent_queries': self.queries[-5:],  # Last 5 for detail
                   'query_themes': self._extract_themes(self.queries),
                   'key_citations': self._top_citations(20),
                   'working_hypothesis': self.hypothesis
               }
       ```
    
    4. **Thread Sharing**: Yes, with permissions:
       ```python
       class ThreadSharing:
           SHARE_MODES = {
               'private': 'Only owner can access',
               'read_only': 'Others can view but not modify',
               'collaborative': 'Shared users can add queries',
               'public': 'Anyone in organization can access'
           }
           
           async def share_thread(self, thread_id, user_emails, mode='read_only'):
               thread = await self.load_thread(thread_id)
               
               for email in user_emails:
                   await self.postgres.insert('thread_shares', {
                       'thread_id': thread_id,
                       'shared_with': email,
                       'permission': mode,
                       'shared_by': thread.owner,
                       'shared_at': datetime.now()
                   })
               
               # Notify users
               await self.send_share_notifications(user_emails, thread)
       ```
    
    5. **Thread Forking/Branching**:
       ```python
       async def fork_thread(self, original_thread_id, fork_point_query_id=None):
           original = await self.load_thread(original_thread_id)
           
           # Create new thread with shared history up to fork point
           forked = ResearchThread(
               id=str(uuid4()),
               parent_thread_id=original_thread_id,
               topic=f"{original.topic} (Fork)",
               user_id=current_user_id
           )
           
           # Copy history up to fork point
           if fork_point_query_id:
               fork_index = next(
                   i for i, q in enumerate(original.queries)
                   if q.id == fork_point_query_id
               )
               forked.queries = original.queries[:fork_index + 1].copy()
               forked.citation_set = original.citation_set.copy()
           
           # Track relationship
           await self.postgres.insert('thread_relationships', {
               'parent_id': original_thread_id,
               'child_id': forked.id,
               'relationship_type': 'fork',
               'fork_point': fork_point_query_id
           })
           
           return forked
       ```
    
    6. **Memory Footprint for 100 Threads**:
       ```python
       # Memory calculation per thread:
       # - Query history (20 queries × 500 chars): ~10KB
       # - Citations (100 IDs + metadata): ~50KB  
       # - Patterns/hypotheses: ~10KB
       # - Metadata: ~5KB
       # Total per thread: ~75KB
       
       # For 100 active threads:
       # - Redis memory: 100 × 75KB = 7.5MB (negligible)
       # - Application memory: ~10MB with object overhead
       # - PostgreSQL storage: ~20MB including indexes
       
       # Optimization for scale:
       class ThreadMemoryOptimizer:
           def compress_inactive_threads(self):
               # Use msgpack for 30% compression
               compressed = msgpack.packb(thread.to_dict())
               
           def lazy_load_citations(self):
               # Don't load all citations into memory
               # Use generator pattern for iteration
               pass
       ```
       
       Memory is not a concern until ~10K active threads
    -->
    
    def __init__(self, thread_id: str, topic: str):
        self.thread_id = thread_id
        self.topic = topic
        self.query_history: List[Query] = []
        self.citation_set: Set[Citation] = set()
        self.discovered_patterns: List[Pattern] = []
        self.working_hypotheses: List[Hypothesis] = []
    
    async def refine_query(self, refinement: str) -> QueryResult:
        """Build on previous queries with maintained context."""
        
        # Understand refinement in context of thread history
        refined_intent = await parse_with_context(
            refinement, 
            self.query_history,
            self.citation_set
        )
        
        # Execute refined query
        result = await execute_query(refined_intent)
        
        # Update thread state
        self.query_history.append(refined_intent)
        self.citation_set.update(result.citations)
        
        return result

class ResearchSession:
    """Manages multiple parallel research threads."""
    
    def __init__(self):
        self.threads: Dict[str, ResearchThread] = {}
        self.cross_thread_insights: List[Insight] = []
    
    def create_thread(self, topic: str) -> ResearchThread:
        """Start a new line of inquiry."""
        thread = ResearchThread(str(uuid4()), topic)
        self.threads[thread.thread_id] = thread
        return thread
    
    def find_cross_thread_patterns(self) -> List[Pattern]:
        """Identify insights that span multiple research threads."""
        # e.g., "Employment concerns" and "Youth migration" threads
        # both surface quotes about "falta de oportunidades"
```

    <!-- GEMINI: Contradiction Detection Questions
    1. How do we define "contradiction" in qualitative interviews?
    2. What's the threshold for semantic similarity to flag potential contradictions?
    3. Should we look for contradictions across time (changing views)?
    4. How do we use NLI models for nuanced contradiction detection?
    5. What's the computational cost of checking all turn pairs?
    -->
    
    <!-- GEMINI ANSWERS: Contradiction Detection
    
    1. **Defining Contradiction in Qualitative Context**:
       ```python
       CONTRADICTION_TYPES = {
           'direct': 'Explicitly opposite claims (A vs not-A)',
           'implicit': 'Incompatible implications',
           'temporal': 'Changed stance over time',
           'contextual': 'Different views in different contexts',
           'ambivalence': 'Simultaneous conflicting feelings (not true contradiction)'
       }
       
       def classify_contradiction(turn1, turn2):
           # Direct: "Government helps" vs "Government never helps"
           if is_negation(turn1.claim, turn2.claim):
               return 'direct'
           
           # Implicit: "Need more police" vs "Police make things worse"
           if implies_opposite(turn1.implications, turn2.implications):
               return 'implicit'
           
           # Temporal: Check turn timestamps
           if turn2.timestamp - turn1.timestamp > timedelta(minutes=10):
               return 'temporal'  # Views can evolve
           
           # Ambivalence: Both positive and negative about same topic
           if mixed_sentiment(turn1, turn2):
               return 'ambivalence'  # Normal in interviews
       ```
    
    2. **Similarity Thresholds for Contradiction Flagging**:
       ```python
       CONTRADICTION_THRESHOLDS = {
           'topic_similarity': 0.7,    # Must discuss same topic
           'semantic_opposition': 0.8,  # High similarity but opposite sentiment
           'confidence_required': 0.6   # Don't flag low-confidence annotations
       }
       
       async def find_contradictions(interview_turns):
           contradictions = []
           
           for i, turn1 in enumerate(interview_turns):
               for turn2 in interview_turns[i+1:]:
                   # Skip if different topics
                   topic_sim = cosine_similarity(
                       embed(turn1.topics), 
                       embed(turn2.topics)
                   )
                   if topic_sim < 0.7:
                       continue
                   
                   # Check for opposition
                   text_sim = cosine_similarity(
                       turn1.embedding,
                       turn2.embedding
                   )
                   
                   sentiment_diff = abs(
                       turn1.sentiment_score - turn2.sentiment_score
                   )
                   
                   if text_sim > 0.6 and sentiment_diff > 0.7:
                       contradictions.append({
                           'turn1': turn1,
                           'turn2': turn2,
                           'confidence': text_sim * sentiment_diff
                       })
       ```
    
    3. **Temporal Contradiction Handling**:
       ```python
       class TemporalContradictionAnalyzer:
           def analyze_stance_evolution(self, turns_by_topic):
               evolution_patterns = []
               
               for topic, turns in turns_by_topic.items():
                   # Sort by timestamp
                   turns_sorted = sorted(turns, key=lambda t: t.timestamp)
                   
                   # Track sentiment/stance over time
                   stances = [self.extract_stance(t) for t in turns_sorted]
                   
                   # Identify shifts
                   for i in range(1, len(stances)):
                       if self.is_stance_shift(stances[i-1], stances[i]):
                           evolution_patterns.append({
                               'topic': topic,
                               'shift_type': self.classify_shift(stances[i-1], stances[i]),
                               'turns': (turns_sorted[i-1], turns_sorted[i]),
                               'interpretation': self.interpret_shift(context)
                           })
               
               return evolution_patterns
           
           def interpret_shift(self, context):
               # Common patterns in interviews
               if context.involves_interviewer_challenge:
                   return "Stance softened after interviewer probe"
               elif context.time_gap > 20:
                   return "Possible reflection/reconsideration"
               else:
                   return "Genuine ambivalence or complexity"
       ```
    
    4. **NLI Models for Nuanced Detection**:
       ```python
       from transformers import pipeline
       
       class NLIContradictionDetector:
           def __init__(self):
               # Use multilingual model for Spanish/English
               self.nli = pipeline(
                   "text-classification",
                   model="MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
               )
           
           async def check_entailment(self, premise, hypothesis):
               result = self.nli(f"{premise} [SEP] {hypothesis}")
               
               # Returns: entailment, neutral, contradiction
               scores = {r['label']: r['score'] for r in result}
               
               if scores.get('contradiction', 0) > 0.8:
                   return 'strong_contradiction'
               elif scores.get('contradiction', 0) > 0.6:
                   return 'potential_contradiction'
               elif scores.get('entailment', 0) < 0.3:
                   return 'tension'  # Not quite contradiction
               else:
                   return 'consistent'
           
           async def analyze_turn_pair(self, turn1, turn2):
               # Check both directions
               forward = await self.check_entailment(turn1.text, turn2.text)
               backward = await self.check_entailment(turn2.text, turn1.text)
               
               # Nuanced interpretation
               if forward == 'contradiction' or backward == 'contradiction':
                   return {
                       'type': 'logical_contradiction',
                       'strength': 'high',
                       'requires_human_review': True
                   }
       ```
    
    5. **Computational Optimization for All Pairs**:
       ```python
       async def efficient_contradiction_check(interview_turns):
           # For N turns, N*(N-1)/2 comparisons
           # For 50 turns = 1,225 comparisons
           
           # Optimization strategies:
           
           # 1. Topic clustering first
           topic_clusters = cluster_by_topic(interview_turns)
           
           # 2. Only compare within clusters
           comparisons_needed = sum(
               len(cluster) * (len(cluster) - 1) / 2
               for cluster in topic_clusters
           )  # Reduces by ~80%
           
           # 3. Use cheap filters first
           for cluster in topic_clusters:
               for i, turn1 in enumerate(cluster):
                   for turn2 in cluster[i+1:]:
                       # Quick sentiment check (cheap)
                       if abs(turn1.sentiment - turn2.sentiment) < 0.5:
                           continue
                       
                       # Expensive NLI check only for candidates  
                       if await quick_contradiction_check(turn1, turn2):
                           result = await deep_nli_check(turn1, turn2)
           
           # 4. Batch NLI processing
           nli_batch = []
           for pair in candidate_pairs:
               nli_batch.append((pair.turn1.text, pair.turn2.text))
           
           # Process batch of 32 pairs at once (GPU optimization)
           results = await nli_model.batch_process(nli_batch)
       ```
       
       Total time: ~2 seconds per interview for full contradiction analysis
    -->

### 8.3 MVP Implementation Plan (3-6 months)

#### Core Features for Immediate Value

**1. Grounded Semantic Search**
```python
@tool_endpoint
async def search_interviews(
    query: str,
    filters: Optional[Dict] = None,
    return_citations: bool = True,
    max_results: int = 20
) -> SearchResult:
    """
    The foundation: Every result is grounded in actual citations.
    
    Example:
        query: "What do young people say about finding work?"
        filters: {"age_range": "18-29", "topics": ["employment"]}
        
    Returns:
        Natural language summary WITH every claim footnoted
        to specific interview turns.
    """
```

**2. Smart Summarization with Voice Preservation**
```python
@tool_endpoint
async def summarize_theme(
    topic: str,
    level: Literal["executive", "detailed", "academic", "policy_brief"],
    preserve_voice: bool = True,
    highlight_outliers: bool = True,
    max_length: int = 500
) -> Summary:
    """
    Summarize a theme across all interviews, preserving participant voice.
    
    The 'preserve_voice' parameter ensures the summary uses actual
    phrases and metaphors from participants, not sanitized language.
    
    Example output for level="policy_brief":
        "Youth unemployment is perceived as a driving force behind emigration.
         As one participant from Artigas stated, 'O estudiás o te vas a la 
         zafra, no hay más nada' (Either you study or you go to the harvest, 
         there's nothing else).¹"
         
         ¹ INT_015_artigas, Turn 23
    """
```

**3. Contradiction & Nuance Detection (The Killer App)**
```python
<!-- GEMINI: Contradiction Detection Algorithm Questions
1. How do we define "contradiction"? Semantic opposition? Sentiment reversal?
2. What's the cosine similarity threshold for "same topic"?
3. How do we handle temporal contradictions (views changing over time)?
4. Should we use textual entailment models for better accuracy?
5. How do we detect subtle contradictions vs explicit ones?
6. What's the computational complexity for all-pairs comparison?
-->

@tool_endpoint
async def analyze_contradictions(
    topic: str,
    scope: Literal["within_interview", "across_interviews", "systemic"],
    include_ambivalence: bool = True
) -> ContradictionAnalysis:
    """
    Surface contradictions and nuanced positions on any topic.
    
    This is what makes qualitative analysis rich - finding where
    participants hold complex, contradictory views.
    
    Example output:
        {
            "systemic_tensions": [{
                "pattern": "Desire for more police vs. deep distrust",
                "examples": [
                    {
                        "turn_id": "INT_003_T15",
                        "text": "Necesitamos más policías en el barrio",
                        "emotion": "fear"
                    },
                    {
                        "turn_id": "INT_003_T22", 
                        "text": "La policía está corrupta, son peor que los chorros",
                        "emotion": "anger"
                    }
                ],
                "interpretation": "Participants want security but don't trust
                                 the institutions meant to provide it"
            }]
        }
    """
```

**4. Interactive Citation Network Visualization**
```python
@tool_endpoint
async def explore_citation_network(
    seed_quote: str,
    network_depth: int = 2,
    relationship_types: List[str] = ["similar", "opposing", "elaborates"],
    include_metadata: bool = True
) -> CitationNetwork:
    """
    Start with one quote and explore its connections across the corpus.
    
    Returns both data and visualization-ready format.
    
    Example:
        seed: "No hay futuro para los jóvenes acá"
        
    Returns network showing:
        - 5 similar sentiments from other interviews
        - 2 opposing views ("Hay oportunidades, pero hay que buscarlas")
        - 3 elaborations adding detail
        - Metadata: speaker demographics, locations, emotional valence
    """
```

**5. Full Provenance Export**
```python
@tool_endpoint
async def export_research_session(
    session_id: str,
    include_all_queries: bool = True,
    include_full_citations: bool = True,
    include_confidence_scores: bool = True,
    format: Literal["json", "markdown", "latex", "docx"] = "json"
) -> ResearchArchive:
    """
    Export a complete, reproducible record of the research session.
    
    The archive includes:
        - manifest.json: Complete session metadata
        - queries.json: Every query and its results
        - citations.json: All referenced turns with full text
        - analysis_path.md: Narrative of the research journey
        - confidence_scores.json: Transparency about AI certainty
    
    This enables computational reproducibility - a gold standard.
    """
```

#### The 30-Minute Challenge Demo

To demonstrate value with just 37 interviews:

```python
# Traditional Approach (30+ minutes):
# 1. Read through relevant interviews
# 2. Code and categorize manually  
# 3. Compare across demographics
# 4. Write synthesis

# With AI Tool (2 minutes):
result = await corpus_tool.comparative_analysis(
    question="How do urban vs rural youth discuss employment prospects?",
    groups=["urban_under_30", "rural_under_30"],
    include_emotional_analysis=True,
    return_format="academic_synthesis"
)

# Instant output with full citations, emotional analysis, and nuanced patterns
```

### 8.4 Methodological Features

#### Balance of Evidence (Not P-Values)
```python
class BalanceOfEvidence:
    """Qualitative research doesn't use p-values. We use evidence balance."""
    
    def analyze_hypothesis(self, hypothesis: str) -> EvidenceReport:
        return {
            "hypothesis": hypothesis,
            "supporting_evidence": [
                {"citation": "INT_001_T5", "strength": "strong", "quote": "..."},
                {"citation": "INT_008_T12", "strength": "moderate", "quote": "..."}
            ],
            "contradicting_evidence": [
                {"citation": "INT_015_T8", "strength": "strong", "quote": "..."}
            ],
            "nuanced_positions": [
                {"citation": "INT_022_T18", "interpretation": "Ambivalent..."}
            ],
            "evidence_balance": "Moderate support with important exceptions",
            "confidence": 0.75,
            "coverage": "Found relevant discussions in 23 of 37 interviews"
        }
```

#### Theory Building Support (Grounded Theory)
```python
class TheoryBuildingAssistant:
    """Support inductive theory development, not just deductive testing."""
    
    async def open_coding_assistant(self) -> List[EmergentCode]:
        """Help identify emergent themes without preconceptions."""
        
    async def axial_coding_assistant(self, core_category: str) -> AxialModel:
        """Explore relationships around a core category."""
        return {
            "core_category": core_category,
            "causal_conditions": [...],  # What leads to this?
            "context": [...],            # When/where does this occur?
            "intervening_conditions": [...],  # What affects its intensity?
            "strategies": [...],         # How do people respond?
            "consequences": [...]        # What results from this?
        }
    
    async def selective_coding_assistant(self) -> TheoryNarrative:
        """Help integrate categories into a coherent theoretical story."""
```

#### Methodological Mirror
```python
class MethodologicalReflexivity:
    """The AI analyzes the researcher's patterns to promote reflexivity."""
    
    async def analyze_research_pattern(self, session: ResearchSession) -> Reflection:
        """
        Example output:
        'I notice 80% of your queries focus on problems and deficits.
         You might want to explore strength-based perspectives:
         - What community resources do participants mention?
         - When do they express pride or accomplishment?
         - What solutions do they propose?'
        """
```

### 8.5 Safeguards and Ethics

#### Aggressive Citation Grounding
```python
class CitationRequirement:
    """Every single claim must be grounded in actual interview text."""
    
    def validate_response(self, response: str, citations: List[Citation]) -> bool:
        # Parse response for claims
        claims = extract_claims(response)
        
        # Verify each claim has a citation
        for claim in claims:
            if not has_supporting_citation(claim, citations):
                raise UngroundedClaimError(f"Claim lacks citation: {claim}")
        
        return True
```

#### Transparent Confidence Scoring
```python
class ConfidenceTransparency:
    """Make AI uncertainty visible and actionable."""
    
    def explain_confidence(self, score: float, factors: Dict) -> str:
        return f"""
        Overall confidence: {score:.2f}
        
        This is based on:
        - Data coverage: {factors['coverage']} 
          (Found relevant content in {factors['n_interviews']} of 37 interviews)
        - Evidence consistency: {factors['consistency']}
          ({factors['supporting']} supporting, {factors['contradicting']} contradicting)
        - Semantic coherence: {factors['coherence']}
          (How well the themes cluster together)
        
        ⚠️ Lower confidence suggests you should review source citations carefully.
        """
```

#### Bias Auditing
```python
class BiasAuditor:
    """Regular audits to identify potential biases in AI analysis."""
    
    async def audit_demographic_bias(self) -> BiasReport:
        """Check if certain voices are systematically privileged."""
        
    async def audit_thematic_bias(self) -> BiasReport:
        """Check if AI consistently surfaces certain themes over others."""
        
    async def generate_counter_narrative(self, dominant_narrative: str) -> str:
        """Actively seek voices that challenge the dominant pattern."""
```

### 8.6 User Experience Principles

#### From Synthesis Back to Source
```python
class SourceLinking:
    """Every piece of generated text links back to its evidence."""
    
    def format_response(self, text: str, citations: List[Citation]) -> HTML:
        # Every sentence becomes a hyperlink to its supporting quote
        # Clicking reveals the full turn context
        # User can always verify the AI's interpretation
```

#### Suggestive, Not Declarative Language
```python
class HumbleLanguage:
    """The AI suggests and explores, never declares truth."""
    
    good_phrases = [
        "One pattern that emerges is...",
        "Several participants express...", 
        "You might want to explore...",
        "The evidence suggests...",
        "A possible interpretation is..."
    ]
    
    bad_phrases = [
        "The data proves...",
        "All participants believe...",
        "The truth is...",
        "This clearly shows..."
    ]
```

### 8.7 Future Scaling Considerations

#### Phase 2 Enhancements (6-18 months)
- **Conversational Interface**: Multi-turn refinement with context
- **Pattern Discovery Engine**: Unsupervised discovery of emergent themes  
- **Cross-Corpus Analysis**: Compare Uruguay data with other countries
- **Multimodal Integration**: Include prosody, pauses, interviewer notes
- **Real-time Collaboration**: Multiple researchers on same corpus

#### Performance Targets at Scale
```python
performance_requirements = {
    "37_interviews": {
        "query_response_time": "<2 seconds",
        "full_corpus_summary": "<5 seconds",
        "network_visualization": "<3 seconds"
    },
    "37000_interviews": {
        "query_response_time": "<5 seconds",
        "filtered_summary": "<10 seconds",
        "network_visualization": "<15 seconds with sampling"
    }
}
```

### 8.8 Integration with AI Assistants

This tool is designed to be used by AI assistants like Claude through a clean API:

```python
# How an AI assistant would use this tool
research_tool = UruguayInterviewTool()

# Natural language query from user
user_question = "What are the main concerns about education in rural areas?"

# AI assistant translates to tool call
result = await research_tool.search_interviews(
    query=user_question,
    filters={"geographic": "rural", "topics": ["education"]},
    return_citations=True
)

# AI assistant synthesizes response with citations
response = f"""
Based on my analysis of the interviews, rural participants express three main 
education concerns:

1. **Distance to schools**: Many mention long commutes. As one parent from 
   Tacuarembó explained, "Mi hijo tiene que viajar dos horas cada día para 
   llegar al liceo"¹.

2. **Teacher shortage**: Several participants note that rural schools struggle 
   to retain qualified teachers².

3. **Limited resources**: Technology access is a particular concern, with one 
   participant noting "los gurises de la ciudad tienen computadoras, los 
   nuestros no"³.

Citations:
¹ INT_023_tacuarembo, Turn 15
² INT_016_rivera, Turn 8; INT_029_cerro_largo, Turn 12  
³ INT_031_rocha, Turn 22
"""
```

### 8.9 Conclusion

This AI Research Assistant Tool Interface transforms the Uruguay Interview corpus from a static dataset into a dynamic research partner. By combining:

- **Scalable architecture** (dual-engine design)
- **Methodological rigor** (grounded citations, balance of evidence)
- **Ethical safeguards** (transparency, reflexivity, bias auditing)
- **User-centered design** (synthesis-to-source, humble language)

We create a tool that enhances rather than replaces human interpretation, scales from 37 to 37,000+ interviews, and maintains the nuance and cultural sensitivity essential to qualitative research.

The MVP demonstrates immediate value through time savings (30 minutes → 2 minutes) while the architecture ensures we can scale to serve thousands of researchers analyzing millions of citizen voices.

<!-- GEMINI: Final Architecture Questions
1. What's the disaster recovery plan for the vector indices?
2. How do we handle GDPR/privacy requirements for embeddings?
3. Should we implement a feedback loop to improve embeddings based on query success?
4. What's the blue-green deployment strategy for embedding model updates?
5. How do we measure and optimize the total cost of ownership at scale?
6. Should we implement embedding compression for archival storage?
7. What's the monitoring strategy for embedding drift over time?
-->