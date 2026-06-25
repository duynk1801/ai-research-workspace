REPORT_SYSTEM = """You are a technical research report writer. Summarize research findings into clear, actionable reports."""

REPORT_PROMPT = """Write a research summary report for this session.

Topic: {topic}
Requirements: {requirements}
Sources analyzed: {source_count}
Insights extracted: {insight_count}

Insights:
{insights_text}

Write a concise report with:
1. Executive summary (2-3 sentences)
2. Key findings (bullet points)
3. Recommended next steps
4. Potential risks to watch"""
