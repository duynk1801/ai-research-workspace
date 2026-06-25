# AI Research Workspace - Improvement Plan

## Current State
- CLI tool with: clarify → search → extract → save
- SQLite + FTS5 for KB
- MiMo LLM for all tasks
- GitHub + Arxiv as sources

## What's Missing (from research)

### 1. 3-Layer Knowledge Architecture
**Source:** BITE (53 stars)
**Problem:** KB is flat - no distinction between evidence, analysis, ideas
**Solution:**
```
data/
├── evidence/          # Sources gốc (PDF, markdown, README)
├── analysis/          # Insights đã extract (structured)
├── index/             # JSONL index cho fast search
└── ideas/             # Ý tưởng tổng hợp, reports
```

### 2. Structured Extraction Schema
**Source:** BITE
**Problem:** Extracting too generic - just "insight" without structure
**Solution:** Extract with schema:
```python
{
    "main_idea": "Ý tưởng chính",
    "core_approach": "Cách tiếp cận",
    "strengths": ["điểm mạnh"],
    "limitations": ["hạn chế"],
    "gaps": ["khoảng trống"],
    "relevance": "Liên quan thế nào"
}
```

### 3. Research Pipeline Stages
**Source:** BITE
**Problem:** Flow stops at save - no query/ideate/review
**Solution:**
```
clarify → search → extract → query → ideate → review → save
```
- **query:** Find relevant insights in existing KB
- **ideate:** Generate new ideas from KB + search results
- **review:** Quality check on extracted insights

### 4. Idea Maturity Scoring
**Source:** BITE
**Problem:** No way to prioritize insights
**Solution:**
```
S1: Raw insight (just extracted)
S2: Validated (cross-referenced with other sources)
S3: Actionable (has clear next steps)
```

### 5. Agent System
**Source:** Khoj
**Problem:** Single LLM for everything
**Solution:** Research Agent with:
- Persona: "Senior research engineer"
- Tools: search, extract, save
- Knowledge: User's accumulated KB

### 6. Semantic Search
**Source:** Khoj
**Problem:** FTS5 is keyword-only, misses synonyms
**Solution:** Add embeddings + cosine similarity search

---

## Implementation Priority

### Phase 1: Core Improvements (This Week)
1. [ ] Restructure KB to 3-layer (evidence/analysis/ideas)
2. [ ] Update extraction schema
3. [ ] Add query stage (search KB before external search)
4. [ ] Add idea maturity scoring

### Phase 2: Pipeline Enhancement (Next Week)
5. [ ] Add ideate stage (generate ideas from KB)
6. [ ] Add review stage (quality check)
7. [ ] Create Research Agent class

### Phase 3: Advanced Features (Month 2)
8. [ ] Add embeddings + semantic search
9. [ ] Add web search source
10. [ ] Add multi-model routing

### Phase 4: Integration (Month 3)
11. [ ] Telegram Bot integration
12. [ ] OpenClaw module
13. [ ] Browser extension

---

## Technology Stack Updated

### Current
- Python, MiMo LLM, SQLite, FTS5, GitHub/Arxiv APIs

### Adding
- ChromaDB (vector search)
- Neo4j (knowledge graph)
- Telegram Bot API
- OpenClaw (agent platform)
- FastAPI (backend)
- React/Flutter (mobile)

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Sources | 2 (GitHub, Arxiv) | 5+ (add web, SO, PapersWithCode) |
| KB Search | FTS5 keyword | Semantic + keyword |
| Pipeline Stages | 4 | 7 |
| Insight Quality | Generic | Structured with maturity |
| Output | CLI only | CLI + Telegram + Web |
