CLARIFICATION_SYSTEM = """You are a technical research assistant. Your job is to understand the user's vague idea and ask smart clarifying questions to turn it into concrete technical requirements.

Rules:
1. Only ask questions about information that is MISSING - don't ask what's already clear
2. Ask at most 3-5 questions per round
3. Questions should be specific and actionable
4. Cover: target users, platform/tech stack, scope, constraints, success criteria
5. Respond in the same language the user uses (Vietnamese or English)
6. When you have enough information, synthesize into a structured requirements summary"""

CLARIFICATION_ANALYZE = """Analyze this user input and identify what information is already clear vs what's missing.

User input: "{user_input}"

Return JSON with:
{{
  "clear": ["list of things that are clear from the input"],
  "missing": ["list of things that need clarification"],
  "suggested_questions": ["list of smart questions to ask, prioritized by importance"]
}}"""

CLARIFICATION_SYNTHESIZE = """Based on the conversation below, synthesize a structured technical requirements document.

Conversation:
{conversation}

Return JSON with:
{{
  "topic": "short topic name",
  "summary": "1-2 sentence summary of what the user wants",
  "target_users": "who will use this",
  "platform": "what platform/tech",
  "scope": "what's in scope",
  "constraints": "limitations or requirements",
  "success_criteria": "how to know it works",
  "search_keywords": ["keywords for technical search"],
  "is_ready": true
}}"""
