import json
from src.llm import chat, chat_json
from src.prompts.clarification import (
    CLARIFICATION_SYSTEM, CLARIFICATION_ANALYZE, CLARIFICATION_SYNTHESIZE
)


def analyze_input(user_input: str) -> dict:
    messages = [
        {"role": "system", "content": CLARIFICATION_SYSTEM},
        {"role": "user", "content": CLARIFICATION_ANALYZE.format(user_input=user_input)}
    ]
    return chat_json(messages)


def generate_questions(conversation: list[dict]) -> str:
    messages = [{"role": "system", "content": CLARIFICATION_SYSTEM}]
    messages.extend(conversation)
    return chat(messages, temperature=0.7)


def synthesize_requirements(conversation: list[dict]) -> dict:
    full_conversation = "\n".join(
        f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in conversation
    )
    messages = [
        {"role": "system", "content": CLARIFICATION_SYSTEM},
        {"role": "user", "content": CLARIFICATION_SYNTHESIZE.format(conversation=full_conversation)}
    ]
    return chat_json(messages)
