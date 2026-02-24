from flask import Flask, render_template, request, jsonify
import json
import os
from chat_agent import ChatAgent
from service_builder import ServiceBuildingAgent
from prompts import service_intake_form, system_prompt
from agents.main import run_pipeline

app = Flask(__name__)

# Global state to keep track of the session (In a real app, use a DB or Session)
api_key = 'YOUR_API_KEY_HERE'
agent_instance = None
current_missing_fields = []


@app.route('/')
def index():
    global agent_instance, current_missing_fields
    # Initialize the agent when the page loads
    agent_instance = ChatAgent(service_form=service_intake_form.copy(), api_key=api_key)
    current_missing_fields = agent_instance.get_missing_fields()
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    global agent_instance, current_missing_fields

    user_input = request.json.get('message')

    if not agent_instance or not current_missing_fields:
        return jsonify({"response": "جلسة العمل انتهت أو لم تبدأ بشكل صحيح.", "finished": True})

    section, field, path = current_missing_fields[0]

    # 1. Validate and Process Input
    if agent_instance.validator.validate(field, "", user_input):
        processed = agent_instance.process_response(path, user_input)
        agent_instance.update_form(path, processed)

        # 2. Check for next missing fields
        current_missing_fields = agent_instance.get_missing_fields()

        if not current_missing_fields:
            # Finalize the process
            service_builder = ServiceBuildingAgent(agent_instance.service_form, api_key)
            document = service_builder.build_service_document()
            service_builder.save_to_file()

            # Optional: Run pipeline
            # run_pipeline(service_builder.service_data)

            return jsonify({
                "response": "🎉 تم جمع جميع البيانات! جاري حفظ الوثيقة...",
                "finished": True
            })

        # 3. Ask the next question
        next_section, next_field, next_path = current_missing_fields[0]
        question = agent_instance.ask_question(next_section, next_field)
        return jsonify({"response": question, "finished": False})

    else:
        # If validation fails, ask again
        question = agent_instance.ask_question(section, field)
        return jsonify({
            "response": f"⚠️ عذراً، الإجابة غير واضحة. {question}",
            "finished": False
        })


if __name__ == '__main__':
    # Ensure templates folder exists
    if not os.path.exists('templates'):
        os.makedirs('templates')

    # Run the Flask app
    print("Starting server at http://127.0.0.1:5000")
    app.run(debug=True)