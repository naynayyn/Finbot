import os
import json
import groq
from dotenv import load_dotenv

load_dotenv()
client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are FinBot, a friendly AI financial advisor.
When the user speaks to you, extract their intent and any data.
Always respond in the SAME language the user spoke in.

Respond in JSON format:
{
  "intent": "log_expense" | "check_budget" | "get_advice" | "set_budget" | "view_summary" | "chat",
  "data": { "amount": number, "category": string, "description": string },
  "response": "your friendly reply to the user"
}"""

def classify_and_respond(user_text: str, financial_context: str = "") -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    if financial_context:
        messages.append({"role": "user", "content": f"My financial context: {financial_context}"})
    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)
