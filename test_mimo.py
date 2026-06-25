import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("MIMO_API_KEY"),
    base_url=os.getenv("MIMO_BASE_URL")
)

completion = client.chat.completions.create(
    model="mimo-v2.5-pro",
    messages=[
        {
            "role": "system",
            "content": "You are MiMo, an AI assistant developed by Xiaomi. Today is date: Thursday, June 25, 2026. Your knowledge cutoff date is December 2024."
        },
        {
            "role": "user",
            "content": "Xin chào, giới thiệu về bản thân bạn"
        }
    ],
    max_completion_tokens=1024,
    temperature=1.0,
    top_p=0.95,
    stream=False,
    frequency_penalty=0,
    presence_penalty=0
)

print("🤖 MiMo:", completion.choices[0].message.content)