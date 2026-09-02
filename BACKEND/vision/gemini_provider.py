import os
import json
from openai import OpenAI

from vision.prompts import SYSTEM_PROMPT

client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()


def analyze_image(base64_image: str) -> dict:
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Проанализируй газон"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    )

    content = response.choices[0].message.content.strip()

    # --- FIX JSON ---
    if "```" in content:
        content = content.replace("```json", "").replace("```", "").strip()

    start = content.find("{")
    end = content.rfind("}")

    if start != -1 and end != -1:
        content = content[start:end+1]

    try:
        parsed = json.loads(content)
        return parsed
    except Exception as e:
        print("❌ JSON ошибка (gemini):", e)
        print("RAW:", content)
        return None
