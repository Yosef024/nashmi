# backend_agent.py
from google import genai
def backend_developer_agent(client, backend_specs):
    system_instruction = """
    You are an expert Python Developer specializing in FastAPI.
    Write a clean, production-ready (for MVP) backend code based on the requirements provided.
    Guidelines:
    1. Use FastAPI. 2. Use Pydantic. 3. Implement eligibility logic.
    4. Use in-memory storage. 5. Create /apply, /status, /pay endpoints.
    Return ONLY the Python code.
    """
    prompt = f"Develop the backend based on these specifications:\n{backend_specs}"
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config={"system_instruction": system_instruction, "temperature": 0.1}
    )
    return response.text