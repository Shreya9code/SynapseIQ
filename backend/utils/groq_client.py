from groq import Groq
from backend.config import settings

# Initialize the client
client = Groq(api_key=settings.GROQ_API_KEY)

def generate_response(prompt: str, system_prompt: str = "") -> str:
    """Direct Groq call for non-Agent tasks."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1024
    )
    return response.choices[0].message.content