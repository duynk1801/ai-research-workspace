# Conversation Model: AI Research Workspace

## Pattern

User asks a question → I research existing repos → extract applicable knowledge/code patterns → apply to our project.

## Session 1: Research Existing Solutions

### Question
"Tôi muốn biết những repo nào đã研究 về AI Research Workspace, knowledge management, và research automation"

### Sources Analyzed

#### Khoj (35,288 stars)
- **What it is:** AI second brain - chat with docs, web, multiple LLMs
- **Key pattern:** Multi-model routing (GPT, Claude, Gemini, Llama)
- **Key pattern:** Agent system with custom knowledge + persona + tools
- **Key pattern:** Semantic search with embeddings (not just keyword)
- **What we can take:** Agent architecture, semantic search approach

#### BITE (53 stars)
- **What it is:** Semi-automated research assistant for academic papers
- **Key pattern:** 3-Layer Knowledge Architecture (Evidence → Index → Ideas)
- **Key pattern:** Research Pipeline with 10 stages (collect → download → analyze → build → query → ideate → focus → review → audit → export)
- **Key pattern:** Structured Paper Analysis (main_idea → core_design → experiments → limitations → gaps)
- **Key pattern:** Idea Maturity Ladder (S1 rough → S2 validated → S3 ready to test)
- **Key pattern:** Each stage has clear input/output contract
- **What we can take:** 3-Layer KB, structured extraction schema, pipeline stages, maturity scoring

#### SurfSense (15,103 stars)
- **What it is:** Open source NotebookLM alternative for teams
- **Key pattern:** Team collaboration on shared knowledge
- **What we can take:** (Less relevant for our solo-use MVP)

#### DocsGPT (17,950 stars)
- **What it is:** Enterprise AI platform with agent builder
- **Key pattern:** Deep research mode (multi-source)
- **What we can take:** Deep research concept

### Key Findings

1. **No one has Clarification Loop** - We're unique here
2. **No one has Topic-Aware Search Routing** - We're unique here
3. **BITE's 3-Layer KB** is the best pattern for knowledge storage
4. **BITE's Pipeline Stages** show how to structure research workflow
5. **Khoj's Agent System** is good for multi-model routing

### Applied to Our Project

| Pattern | Source | Applied As |
|---------|--------|-----------|
| 3-Layer KB | BITE | evidence/analysis/ideas directories |
| Structured Extraction | BITE | Extract main_idea, strengths, limitations, gaps |
| Pipeline Stages | BITE | clarify → search → extract → query → ideate → review → save |
| Idea Maturity | BITE | Score insights S1/S2/S3 |
| Agent System | Khoj | Research Agent with persona + tools |
| Semantic Search | Khoj | Embeddings-based KB search (planned) |

---

## Template for Future Sessions

### How to Use This Pattern

1. **User asks:** "Tìm hiểu về [field/technology]"
2. **I search:** GitHub repos, Arxiv papers
3. **I analyze:** Architecture, key patterns, code structure
4. **I extract:** Patterns we can apply
5. **I apply:** To our codebase
6. **I document:** In this note file

### Fields to Research Next

- [ ] Vector DB integration (ChromaDB vs pgvector)
- [ ] Knowledge Graph patterns (Neo4j)
- [ ] Telegram Bot integration
- [ ] OpenClaw module architecture
- [ ] Browser extension patterns
- [ ] Mobile app architecture (React Native/Flutter)
