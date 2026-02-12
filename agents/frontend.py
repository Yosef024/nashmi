def frontend_developer_agent(client, frontend_specs):
    system_instruction = """
    You are an expert Frontend Developer. 
    Your task is to create a modern, professional government service MVP using single-file HTML, CSS (Tailwind), and Vanilla JavaScript.

    STRICT RULES:
    1. NO FRAMEWORKS: Use standard HTML5 and Vanilla JavaScript.
    2. STYLING: Use Tailwind CSS via CDN classes.
    3. ICONS: Use Lucide Icons. Initialize them using `lucide.createIcons()`.
    4. STRUCTURE: 
       - Create a clean 'Government-style' UI (Professional blues, whites, and greys).
       - Use a 'State Machine' approach in JS to switch between sections (Landing, Form, Loading, Success).
    5. INTERACTIVE LOGIC:
       - Implement form validation (National ID length, Name format).
       - Create a 'Simulation' mode with `setTimeout` to mock backend API calls and GSB checks.
       - Update the DOM dynamically based on user actions.
    6. LAYOUT: Ensure the design is RTL (Arabic) and fully responsive.
    7. OUTPUT: Return ONLY the complete HTML code (including the <script> and <style> tags).
    """

    prompt = f"Create the React frontend based on these requirements:\n{frontend_specs}"

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config={
            "system_instruction": system_instruction,
            "temperature": 0.1,
        }
    )

    return response.text