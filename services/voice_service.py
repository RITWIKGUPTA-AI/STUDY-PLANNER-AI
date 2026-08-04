import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY") or "missing-api-key"
)

def speech_to_text():
    """
    Browser-based speech recognition will be implemented later.
    """
    return ""


def ask_voice_ai(question):

    prompt = f"""
You are an expert AI tutor.

Student asked:

{question}

Explain in a simple,
easy,
step-by-step manner.

If it is numerical,
solve it.

If it is theory,
explain with examples.
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert AI tutor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"AI Error: {e}"