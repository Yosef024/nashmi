# backend_agent.py
from google import genai
def backend_developer_agent(client, backend_specs):
    system_instruction = """
    You are an expert Python Developer specializing in FastAPI and Modular Architecture.
    Your task is to create a Backend Plugin (Module) for a central government platform.

    STRICT GUIDELINES:
    1. NO APP INSTANCE: Do NOT create 'app = FastAPI()'. Do NOT use 'uvicorn.run()'.
    2. USE APIROUTER: Use 'from fastapi import APIRouter' to define all endpoints.
    3. REGISTRATION FUNCTION: You MUST implement a function named 'register_endpoints(app: FastAPI)'.
       Inside this function, use 'app.include_router(router, prefix="/api/SERVICE_NAME")'.
    4. LOGIC: 
       - Use Pydantic models for request/response validation.
       - Implement business logic for eligibility, application submission, and status tracking.
       - Use a dictionary (in-memory) to store records specific to this service.
    5. ENDPOINTS: Create endpoints like /apply, /status, and /verify as part of the router.
    6. STANDARDS: Write clean, production-ready code with proper error handling (HTTPException).

    Return ONLY the Python code.
    """
    prompt = f"Develop the backend based on these specifications:\n{backend_specs}"
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config={"system_instruction": system_instruction, "temperature": 0.1}
    )
    return response.text