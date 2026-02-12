# orchestrator.py
from  google import genai

def service_orchestrator(client, service_description):
    system_instruction = """
    You are a Lead Software Architect. Your job is to take a Government Service Description (JSON)
    and split it into two highly detailed technical requirement documents for an MVP.

    1. BACKEND BRIEF: Focus on Python/FastAPI logic, data models, and eligibility rules. 
       Ignore external APIs; use mock functions for GSB and e-Fawateercom.
    2. FRONTEND BRIEF: Focus on React/Tailwind components, form validation, and user experience.

    Output format: 
    ---BACKEND_START---
    [Detailed backend specs]
    ---BACKEND_END---
    ---FRONTEND_START---
    [Detailed frontend specs]
    ---FRONTEND_END---
    """
    prompt = f"Here is the service description to process:\n{service_description}"

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config={"system_instruction": system_instruction, "temperature": 0.2}
    )

    full_text = response.text
    try:
        backend_specs = full_text.split("---BACKEND_START---")[1].split("---BACKEND_END---")[0].strip()
        frontend_specs = full_text.split("---FRONTEND_START---")[1].split("---FRONTEND_END---")[0].strip()
    except IndexError:
        backend_specs = "Error: Backend specs could not be parsed."
        frontend_specs = "Error: Frontend specs could not be parsed."

    return backend_specs, frontend_specs