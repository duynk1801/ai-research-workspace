# AI Research Workspace - Technical Documentation

## Tổng quan

AI Research Workspace là công cụ CLI giúp người dùng research một chủ đề bất kỳ, từ ý tưởng mơ hồ đến tri thức có thể hành động (actionable knowledge). Hệ thống tự động search, phân tích, trích xuất insights và lưu vào Knowledge Base cá nhân.

## Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI (Typer)                              │
│                   src/cli.py                                    │
│                                                                │
│  research <topic>                                              │
│  kb search | list | show | stats                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    7-Stage Pipeline                              │
│                                                                │
│  Stage 0: Quick Search + Problem Definition (0.4s)             │
│  Stage 1: Query Knowledge Base                                  │
│  Stage 2: External Search (GitHub/Arxiv)                        │
│  Stage 3: Extract Insights (parallel)                           │
│  Stage 4: Generate Ideas                                        │
│  Stage 5: Review (maturity scoring)                             │
│  Stage 6: Save to Knowledge Base                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
┌──────────────────┐ ┌──────────┐ ┌──────────────────┐
│ LLM (MiMo API)  │ │ Search   │ │ SQLite + FTS5    │
│ OpenAI-compat   │ │ GitHub   │ │ Evidence Layer   │
│                 │ │ Arxiv    │ │ Analysis Layer   │
│                 │ │          │ │ Ideas Layer      │
└──────────────────┘ └──────────┘ └──────────────────┘
```

---

## Flow chi tiết từng Stage

### Stage 0: Quick Search + Problem Definition

**Mục đích:** Hiểu bài toán người dùng trước khi research sâu.

**Thuật toán:**
```
1. quick_search(topic)        → HTTP call GitHub + Arxiv API (~1.5s)
2. analyze_results(topic)     → Pattern matching (không LLM, ~0.1s)
   - Đếm code_indicators vs paper_indicators
   - Trích xuất languages, topics từ kết quả
   - Liệt kê existing tools có >100 stars
3. get_problem_definition_questions()  → Tạo 5 câu hỏi động
   - WHAT:  Bài toán là gì?
   - WHY:   Tại sao cần?
   - WHO:   Cho ai?
   - SCOPE: Giới hạn?
   - DEPTH: Cần sâu đến đâu?
4. Thu thập answers từ user
5. is_problem_defined()       → Kiểm tra đủ 4/5 yếu tố
```

**Tại sao không dùng LLM ở bước này:**
- Tốc độ: HTTP search 1.5s vs LLM call 10-15s
- Pattern matching đủ để gợi ý câu hỏi
- User tự quyết định scope, không AI tự đoán

**Output:** Problem Definition JSON
```json
{
  "what": "tool để scrape web",
  "why": "tự động hóa thu thập dữ liệu",
  "who": "self-use",
  "scope": "Python only",
  "depth": "overview"
}
```

---

### Stage 1: Query Knowledge Base

**Mục đích:** Tìm insights đã tích lũy từ các session trước.

**Thuật toán:**
```
1. kb.get_all_insights()        → SELECT FROM SQLite
2. Nếu KB trống → skip
3. query_kb(topic, requirements, existing_insights)  → LLM call
   - So sánh topic mới vs insights cũ
   - Tìm connections, gaps
   - Gợi ý research cần thêm
```

**Tại sao query KB trước external search:**
- Tránh research lại những gì đã biết
- Tận dụng knowledge đã tích lũy (flywheel effect)
- Gợi ý gaps → search chính xác hơn

---

### Stage 2: External Search

**Mục đích:** Tìm sources bên ngoài (GitHub repos, Arxiv papers).

**Thuật toán:**
```
1. detect_topic_type(topic)    → Keyword matching
   - code_indicators: tool, framework, library, build...
   - paper_indicators: research, study, survey, algorithm...
   - Quyết định nguồn: github, arxiv, hay cả hai

2. multi_search(keyword, sources, limit=3)
   - search_github(): GET /search/repositories
   - search_arxiv():  GET export.arxiv.org/api/query
   - Mỗi source trả list items

3. Deduplicate results theo URL
```

**Topic-aware routing:**
```
Input: "Python web scraping tool"
  → code_indicators: 8 hits (tool, python, code, github...)
  → paper_indicators: 2 hits (research, analysis)
  → Result: sources = ["github"] (chỉ search code)

Input: "transformer attention mechanism paper"
  → code_indicators: 1 hit
  → paper_indicators: 5 hits (paper, research, algorithm, model)
  → Result: sources = ["arxiv"] (chỉ search papers)
```

---

### Stage 3: Extract Insights

**Mục đích:** Đọc nội dung sources và trích xuất structured insights.

**Thuật toán:**
```
1. Với mỗi source (github/arxiv):
   a. fetch_github_readme(url)  → GET /repos/{owner}/{repo}/readme
      hoặc paper abstract từ Arxiv

   b. extract_insights(content, title, type, url)  → LLM call
      - Gửi content + extraction prompt
      - LLM trả structured JSON

   c. Parse kết quả:
      - type: IDEA|CODE|PATTERN|RISK|INTEGRATION|GAP
      - main_idea, core_approach
      - strengths[], limitations[], gaps[]
      - relevance, maturity (S1/S2/S3)
      - tags[]

2. Parallel execution: ThreadPoolExecutor(max_workers=3)
   - Đọc 2-3 sources cùng lúc
   - Tiết kiệm 50-60% thời gian
```

**Structured Extraction Schema:**
```json
{
  "type": "IDEA",
  "title": "Web Mining Toolkit Pattern",
  "main_idea": "Comprehensive Python toolkit combining web mining, NLP, ML",
  "core_approach": "Integrates web services, crawling, HTML parsing, NLP, ML algorithms",
  "strengths": ["All-in-one solution", "Well-documented"],
  "limitations": ["Limited customization", "Bundle approach adds dependencies"],
  "gaps": ["No modular architecture", "Modern web scraping challenges unclear"],
  "relevance": "Useful for rapid prototyping",
  "maturity": "S2",
  "tags": ["web-mining", "nlp", "python"]
}
```

**Idea Maturity Scoring:**
```
S1: Raw insight - vừa extract, chưa validate
S2: Validated - cross-referenced với sources khác
S3: Actionable - có clear next steps, có thể dùng ngay
```

---

### Stage 4: Generate Ideas

**Mục đích:** Từ insights + gaps, tạo ý tưởng research mới.

**Thuật toán:**
```
generate_ideas(topic, insights, gaps)  → LLM call

Input:
  - topic: "Python web scraping tool"
  - insights: [list extracted insights]
  - gaps: [gaps identified from KB query]

LLM prompt:
  - Gửi tất cả insights + gaps
  - Yêu cầu 3-5 research ideas
  - Mỗi idea: title, hypothesis, approach, resources, success_criteria
```

---

### Stage 5: Review

**Mục đích:** Tổng hợp và đánh giá chất lượng insights.

**Thuật toán:**
```
Local computation (không LLM):
1. Đếm insights theo type (IDEA, CODE, PATTERN...)
2. Đếm insights theo maturity (S1, S2, S3)
3. Hiển thị tổng quan cho user
```

---

### Stage 6: Save

**Mục đích:** Lưu insights vào Knowledge Base.

**Thuật toán:**
```
1. Hiển thị danh sách insights cho user review
2. User confirm save
3. kb.save_insights(insights)  → INSERT INTO SQLite
   - Mỗi insight lưu đầy đủ structured fields
   - FTS5 auto-index cho full-text search
4. kb.finish_session()  → UPDATE session status
```

---

## Knowledge Base Architecture (3 Layers)

```
data/
├── evidence/          # Sources gốc (PDF, markdown, README)
├── analysis/          # Insights đã extract (structured JSON)
├── index/             # JSONL index cho fast search (planned)
├── ideas/             # Ý tưởng tổng hợp, reports (planned)
└── knowledge.db       # SQLite database
```

### Database Schema

**Table: sessions**
```sql
id              INTEGER PRIMARY KEY
topic           TEXT NOT NULL
requirements    TEXT (JSON)
status          TEXT (active/completed)
created_at      TIMESTAMP
```

**Table: insights**
```sql
id              INTEGER PRIMARY KEY
session_id      INTEGER (FK → sessions)
topic           TEXT
insight_type    TEXT (IDEA|CODE|PATTERN|RISK|INTEGRATION|GAP)
title           TEXT
main_idea       TEXT
core_approach   TEXT
strengths       TEXT (JSON array)
limitations     TEXT (JSON array)
gaps            TEXT (JSON array)
relevance       TEXT
maturity        TEXT (S1|S2|S3)
source_url      TEXT
source_type     TEXT (github|arxiv)
tags            TEXT (JSON array)
created_at      TIMESTAMP
```

**FTS5 Index:** title, content, main_idea, tags

---

## LLM Integration

**Model:** MiMo v2.5 Pro (OpenAI-compatible API)

**Các LLM calls trong pipeline:**

| Stage | LLM Call | Purpose | Temperature |
|-------|----------|---------|-------------|
| 1 | query_kb() | Tìm connections trong KB | 0.3 |
| 3 | extract_insights() | Trích xuất structured insights | 0.3 |
| 4 | generate_ideas() | Tạo research ideas mới | 0.7 |

**Robustness:**
- `chat_json()` retry 1 lần nếu JSON parse fail
- Extract fallback: trả empty list thay vì crash
- Mỗi extraction được wrap trong try/except

---

## Cài đặt & Sử dụng

```bash
# Clone
git clone git@github.com:duynk1801/ai-research-workspace.git
cd ai-research-workspace

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Cấu hình
cp .env.example .env
# Thêm MIMO_API_KEY vào .env

# Sử dụng
python -m src.cli research "chủ đề research"
python -m src.cli kb list
python -m src.cli kb search "query"
python -m src.cli kb show 1
python -m src.cli kb stats
```

---

## Nguồn tham khảo (Pattern đã áp dụng)

| Pattern | Nguồn | Áp dụng |
|---------|-------|---------|
| 3-Layer KB | BITE (53★) | evidence/analysis/ideas directories |
| Structured Extraction | BITE | main_idea, strengths, limitations, gaps |
| Pipeline Stages | BITE | 7-stage research pipeline |
| Idea Maturity | BITE | S1/S2/S3 scoring |
| Parallel Extraction | Mới | ThreadPoolExecutor for concurrent LLM calls |
| Topic-aware Routing | Mới | Keyword matching → source selection |
| Problem Definition | Design Thinking + CPS Framework | 5-factor problem scoping |
