import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Securely initialize the Gemini client.
# Requires GEMINI_API_KEY in environment (Render env vars or .env locally).
# IMPORTANT: Must pass api_key explicitly — env-level discovery fails on Render.
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None
    print("Warning: GEMINI_API_KEY not found in environment. Answers will fail.")

SYSTEM_PROMPT = """
Role: You are an objective Mutual Fund FAQ Assistant.
Task: Answer the user's question using ONLY the provided context.

Constraints:
1. Max 3 sentences.
2. If the answer is not in the context, strictly say "I cannot find official info for this."
3. NO investment advice, opinions, or comparisons like "which is better".
4. Focus only on factual output.

Context:
{context}
"""

REFUSAL_PROMPT = """
I am a facts-only assistant and cannot provide investment advice, opinions, or performance comparisons. 
To make a personalized investment decision, please consult a SEBI-registered financial advisor. 
You can learn more about how mutual funds work at https://investor.sebi.gov.in.
"""

def is_advisory_query(query: str) -> bool:
    advisory_keywords = ["should i", "which is better", "top pick", "recommend", "invest in", "good investment", "better than", "best", "long term"]
    qs = query.lower()
    for kw in advisory_keywords:
        if kw in qs:
            return True
    return False

def generate_answer(query: str, context: str) -> str:
    """
    Calls Google Gemini (2.0 Flash) to synthesize the final answer strictly bound by context.
    """
    if not context:
        return "I cannot find official info for this."

    if not client:
        return "Sorry, I encountered an internal error while connecting to the answer generator (Missing API Key)."

    try:
        # Format the system prompt into the interaction
        full_query = f"{SYSTEM_PROMPT.format(context=context)}\n\nQuery: {query}"
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=full_query,
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=150,
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini LLM Error: {e}")
        return "Sorry, I encountered an internal error while connecting to the answer generator."
