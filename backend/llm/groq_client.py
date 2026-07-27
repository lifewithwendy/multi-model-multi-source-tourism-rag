import os
from groq import Groq

def generate_rag_response(context: str, question: str) -> str:
    """
    Calls the Groq API to generate an answer based on the retrieved context.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY not set in environment."
        
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        return f"Failed to initialize Groq client: {str(e)}"
    
    system_prompt = """
You are an expert Sri Lanka tourism assistant. 
Your goal is to answer the user's question based STRICTLY on the provided context.
The context contains structured data and descriptions about various tourist attractions (waterfalls, mountains, beaches).

CRITICAL RULES:
1. Answer ONLY using the information provided in the Context below. Do not use your pre-trained outside knowledge.
2. ALWAYS cite the specific attraction name(s) you are referencing in your answer.
3. If the context does not contain enough information to answer the question, you must explicitly say: "I do not have enough information to answer that based on the provided context."
4. Be concise, helpful, and format your response clearly.
"""
    
    user_prompt = f"Context:\n{context}\n\nQuestion:\n{question}"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=1024
        )
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        return "Error: Received an empty response from the LLM."
    except Exception as e:
        # Handle rate limits, API downtime, etc gracefully
        return f"LLM Generation Error: {str(e)}"
