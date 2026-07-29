import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def generate_rag_response(context: str, question: str) -> str:
    """
    Calls the Groq API using LangChain ChatGroq to generate an answer based on the retrieved context.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY not set in environment."
        
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    try:
        llm = ChatGroq(api_key=api_key, model=model_name, temperature=0.0)
    except Exception as e:
        return f"Failed to initialize ChatGroq model: {str(e)}"
    
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

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Context:\n{context}\n\nQuestion:\n{question}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        return chain.invoke({"context": context, "question": question})
    except Exception as e:
        return f"LLM Generation Error: {str(e)}"
