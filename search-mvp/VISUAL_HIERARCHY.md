# Visual Hierarchy for Research Agent Output

## Line Patterns and Their Meanings

### 1. Iteration Boundaries (Double Line)
```
════════════════════════════════════════════════════════════════════════════════
🔄 ITERATION 1/5
════════════════════════════════════════════════════════════════════════════════
```
- **Purpose**: Clearly separates each iteration
- **When used**: At the start of each research iteration
- **Visual weight**: Heaviest - makes iterations easy to scan

### 2. Major Phase Transitions (Single Line)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 RESEARCH STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
- **Purpose**: Marks major sections like statistics, report generation phase
- **When used**: Between research and report phases, for statistics section
- **Visual weight**: Medium - important but not as prominent as iterations

### 3. Content Subsections (Light Dashes)
```
💭 AGENT THINKING:
────────────────────────────────────────────────────────────────────────────────
  Now let me examine the economic-related meta-themes...
────────────────────────────────────────────────────────────────────────────────

📝 ADDING TO SCRATCHPAD:
────────────────────────────────────────────────────────────────────────────────
  RESEARCH PLAN for economy...
────────────────────────────────────────────────────────────────────────────────
```
- **Purpose**: Separates content within iterations (thinking, scratchpad notes)
- **When used**: For agent thinking, scratchpad additions, interview content
- **Visual weight**: Light - provides structure without overwhelming

### 4. No Lines (Clean Content)
```
🔧 Searching for "economía"
✅ 11.0K chars | Found: 17 text matches across 7 interviews

📊 CORPUS STATISTICS
📚 Total interviews: 35
💬 Total conversation turns: 5,510
```
- **Purpose**: Keeps output clean and scannable
- **When used**: For tool calls, results, and most content
- **Visual weight**: None - content speaks for itself

## Recent Improvements

### Simplified Meta-Theme Output
The `explore_meta_theme` tool now provides cleaner output:

**Before** (verbose):
```
• technical_assistance_vacuum
  📊 7 turns across 1 interview(s)
  📍 067:
     [[067:13]] [[067:17]] [[067:15]] [[067:18]] [[067:22]] [[067:27]]
     [[067:55]]
```

**After** (concise):
```
• technical_assistance_vacuum
  📊 7 turns across 1 interview(s)
  📍 Found in: [[067:summary]]
```

This reduces visual noise while maintaining essential information. The agent can drill down into specific interviews when needed.

## Benefits of This Hierarchy

1. **Clear Iteration Tracking**: Double lines make it immediately obvious where each iteration starts/ends
2. **Phase Separation**: Easy to see when research ends and report generation begins
3. **Content Organization**: Light dashes group related content without visual clutter
4. **Reduced Noise**: Minimal use of lines keeps focus on the content
5. **Scannable Output**: Visual hierarchy helps quickly find specific sections
6. **Progressive Disclosure**: High-level summaries with ability to drill down for details

## Example Flow

```
════════════════════════════════════════════════════════════════════════════════
🔄 ITERATION 1/5
════════════════════════════════════════════════════════════════════════════════

🔧 get_corpus_stats()
✅ 2.5K chars

📊 CORPUS STATISTICS
📚 Total interviews: 35
...

════════════════════════════════════════════════════════════════════════════════
🔄 ITERATION 2/5
════════════════════════════════════════════════════════════════════════════════

💭 AGENT THINKING:
────────────────────────────────────────────────────────────────────────────────
  Now let me examine the economic-related meta-themes...
────────────────────────────────────────────────────────────────────────────────

🔧 explore_meta_theme({"meta_theme": "economic_sector_collapse"})
✅ 1.8K chars
...

════════════════════════════════════════════════════════════════════════════════
✅ RESEARCH PHASE COMPLETE
📊 5 iterations, 10 tool calls
════════════════════════════════════════════════════════════════════════════════

📝 REPORT GENERATION PHASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Synthesizing findings from 10 research actions...

📝 RESEARCH REPORT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Report content here...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 RESEARCH STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️  Duration: 15s
🔄 Iterations completed: 5
🔧 Tool calls made: 10
...
```